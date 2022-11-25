# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.notifications import clear_notifications
from frappe.model.document import Document
from frappe.utils import cint

IGNORED_DOCTYPES = {
	"Account",
	"Cost Center",
	"Warehouse",
	"Budget",
	"Party Account",
	"Employee",
	"Sales Taxes and Charges Template",
	"Purchase Taxes and Charges Template",
	"POS Profile",
	"BOM",
	"Company",
	"Bank Account",
	"Item Tax Template",
	"Mode of Payment",
	"Item Default",
	"Customer",
	"Supplier",
}


class TransactionDeletionRecord(Document):
	def validate(self):
		frappe.only_for("System Manager")

		if {row.doctype_name for row in self.doctypes_to_be_ignored}.difference(IGNORED_DOCTYPES):
			frappe.throw(
				_(
					"DocTypes should not be added manually to the 'Excluded DocTypes' table. You are only allowed to remove entries from it."
				),
				title=_("Not Allowed"),
			)

	def before_submit(self):
		self.populate_doctypes_to_be_ignored_table()
		delete_bins(self.company)
		delete_lead_addresses(self.company)
		reset_company_values(self.company)
		clear_notifications()
		self.delete_company_transactions()

	def populate_doctypes_to_be_ignored_table(self):
		if self.doctypes_to_be_ignored:
			return

		self.extend(
			"doctypes_to_be_ignored", [{"doctype_name": doctype} for doctype in IGNORED_DOCTYPES]
		)

	def delete_company_transactions(self):
		table_doctypes = frappe.get_all("DocType", filters={"istable": 1}, pluck="name")

		for doctype, fieldname in get_doctypes_with_company_field(
			exclude_doctypes=self.get_ignored_doctypes_and_singles()
		):
			if doctype == self.doctype:
				continue

			no_of_docs = frappe.db.count(doctype, {fieldname: self.company})
			if no_of_docs <= 0:
				continue

			if doctype not in table_doctypes:
				self.append("doctypes", {"doctype_name": doctype, "no_of_docs": no_of_docs})

			delete_version_log(doctype, fieldname, self.company)
			delete_communications(doctype, fieldname, self.company)
			delete_child_table_rows(doctype, fieldname, self.company)
			frappe.db.delete(doctype, {fieldname: self.company})

			if naming_series := frappe.db.get_value("DocType", doctype, "autoname"):
				if "#" in naming_series:
					update_naming_series(naming_series, doctype)

	def get_ignored_doctypes_and_singles(self) -> list:
		singles = set(frappe.get_all("DocType", filters={"issingle": 1}, pluck="name"))
		ignored = {row.doctype_name for row in self.doctypes_to_be_ignored}
		return list(singles + ignored)


def update_naming_series(naming_series, doctype_name):
	from pypika.functions import Max

	if "." in naming_series:
		prefix = naming_series.rsplit(".", 1)[0]
	elif "{" in naming_series:
		prefix = naming_series.rsplit("{", 1)[0]
	else:
		prefix = naming_series

	table = frappe.qb.DocType(doctype_name)
	last = frappe.qb.from_(table).select(Max(table.name)).where(table.name.like(f"{prefix}%"))

	last = cint(last[0][0].replace(prefix, "")) if last and last[0][0] else 0
	series = frappe.qb.DocType("Series")
	frappe.qb.update(series).set(series.current, last).where(series.name == prefix).run()


def delete_version_log(doctype, company_fieldname, company_name):
	frappe.db.sql(
		"""delete from `tabVersion` where ref_doctype=%s and docname in
		(select name from `tab{0}` where `{1}`=%s)""".format(
			doctype, company_fieldname
		),
		(doctype, company_name),
	)


def delete_communications(doctype, company_fieldname, company_name):
	reference_docs = frappe.get_all(doctype, filters={company_fieldname: company_name}, pluck="name")
	communications = frappe.get_all(
		"Communication",
		filters={"reference_doctype": doctype, "reference_name": ["in", reference_docs]},
		pluck="name",
	)

	frappe.delete_doc("Communication", communications, ignore_permissions=True)


@frappe.whitelist()
def get_doctypes_to_be_ignored():
	return list(IGNORED_DOCTYPES)


def get_doctypes_with_company_field(exclude_doctypes) -> tuple[tuple[str, str]]:
	return frappe.get_all(
		"DocField",
		filters={
			"fieldtype": "Link",
			"options": "Company",
			"parent": ["not in", exclude_doctypes],
		},
		fields=["parent", "fieldname"],
		as_list=True,
	)


def reset_company_values(compay_name: str) -> None:
	company_obj = frappe.get_doc("Company", compay_name)
	company_obj.total_monthly_sales = 0
	company_obj.sales_monthly_history = None
	company_obj.save()


def delete_bins(compay_name: str) -> None:
	company_warehouses = frappe.get_all("Warehouse", filters={"company": compay_name}, pluck="name")
	bins = frappe.get_all("Bin", filters={"warehouse": ["in", company_warehouses]}, pluck="name")
	frappe.db.delete("Bin", {"name": ("in", bins)})


def delete_child_table_rows(doctype, company_fieldname, company_name):
	parent_docs_to_be_deleted = frappe.get_all(
		doctype, {company_fieldname: company_name}, pluck="name"
	)

	child_tables = frappe.get_all(
		"DocField", filters={"fieldtype": "Table", "parent": doctype}, pluck="options"
	)

	for table in child_tables:
		frappe.db.delete(table, {"parent": ["in", parent_docs_to_be_deleted]})


def delete_lead_addresses(company_name: str) -> None:
	"""Delete addresses to which leads are linked"""
	leads = frappe.get_all("Lead", filters={"company": company_name}, pluck="name")
	if not leads:
		return

	if addresses := frappe.get_all(
		"Dynamic Link",
		filters={"link_name": ("in", leads), "link_doctype": "Lead", "parenttype": "Address"},
		pluck="parent",
	):
		frappe.db.sql(
			"""DELETE FROM `tabAddress`
			WHERE name IN %(addresses)s AND
			name NOT IN (
				SELECT DISTINCT dl1.parent FROM `tabDynamic Link` dl1
				INNER JOIN `tabDynamic Link` dl2 ON dl1.parent = dl2.parent
				AND dl1.link_doctype <> dl2.link_doctype
			)
			""",
			{"addresses": addresses},
		)

		dl = frappe.db.get_table("Dynamic Link")
		frappe.qb.delete(dl).where(dl.link_doctype == "Lead").where(dl.parenttype == "Address").where(
			dl.link_name.isin(leads)
		).run()

	customer = frappe.qb.DocType("Customer")
	frappe.qb.update(customer).set(customer.lead_name, None).where(
		customer.lead_name.isin(leads)
	).run()
