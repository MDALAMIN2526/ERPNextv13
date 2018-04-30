# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from frappe import _
from frappe.model.document import Document
from frappe.utils import today, flt

class LoyaltyProgram(Document):
	pass


def get_loyalty_details(customer, loyalty_program, expiry_date=None, company=None):
	if not expiry_date:
		expiry_date = today()
	args_list = [customer, loyalty_program, expiry_date]
	condition = ''
	if company:
		condition = " and company=%s "
		args_list.append(company)
	loyalty_point_details = frappe.db.sql('''select sum(loyalty_points) as loyalty_points,
		sum(purchase_amount) as total_spent from `tabLoyalty Point Entry`
		where customer=%s and loyalty_program=%s and (expiry_date>=%s) {condition}
		group by customer'''.format(condition=condition), tuple(args_list), as_dict=1)
	if loyalty_point_details:
		return loyalty_point_details[0]
	else:
		return {"loyalty_points": 0, "total_spent": 0}

@frappe.whitelist()
def get_loyalty_program_details(customer, loyalty_program=None, expiry_date=None, company=None):
	lp_details = frappe._dict()
	customer_loyalty_program = frappe.db.get_value("Customer", customer, "loyalty_program")

	if not customer_loyalty_program:
		frappe.throw(_("Customer isn't enrolled in any Loyalty Program"))
	if loyalty_program and loyalty_program != customer_loyalty_program:
		frappe.throw(_("Customer isn't enrolled in this Loyalty Program"))

	if not loyalty_program:
		loyalty_program = customer_loyalty_program
	if not company:
		company = frappe.db.get_default("company") or frappe.get_all("Company")[0].name

	lp_details.update(get_loyalty_details(customer, loyalty_program, expiry_date, company))

	lp_details.update({"loyalty_program": loyalty_program})
	loyalty_program = frappe.get_doc("Loyalty Program", lp_details.loyalty_program)

	lp_details.expiry_duration = loyalty_program.expiry_duration
	lp_details.conversion_factor = loyalty_program.conversion_factor
	lp_details.expense_account = loyalty_program.expense_account
	lp_details.cost_center = loyalty_program.cost_center
	lp_details.company = loyalty_program.company

	tier_spent_level = sorted([d.as_dict() for d in loyalty_program.collection_rules], key=lambda rule:rule.min_spent, reverse=True)
	for i, d in enumerate(tier_spent_level):
		if i==0 or lp_details.total_spent < d.min_spent:
			lp_details.tier_name = d.tier_name
			lp_details.collection_factor = d.collection_factor
		else:
			break
	return lp_details

@frappe.whitelist()
def get_redeemption_factor(loyalty_program=None, customer=None):
	customer_loyalty_program = None
	if not loyalty_program:
		customer_loyalty_program = frappe.db.get_value("Customer", customer, "loyalty_program")
		loyalty_program = customer_loyalty_program
	if loyalty_program:
		return frappe.db.get_value("Loyalty Program", loyalty_program, "conversion_factor")
	else:
		frappe.throw(_("Customer isn't enrolled in any Loyalty Program"))


def validate_loyalty_points(ref_doc, points_to_redeem):
	loyalty_program = None
	posting_date = None

	if ref_doc.doctype == "Sales Invoice":
		posting_date = ref_doc.posting_date
	else:
		posting_date = today()

	if hasattr(ref_doc, "loyalty_program") and ref_doc.loyalty_program:
		loyalty_program = ref_doc.loyalty_program
	else:
		loyalty_program = frappe.db.get_value("Customer", ref_doc.customer, ["loyalty_program"])

	if loyalty_program and frappe.db.get_value("Loyalty Program", loyalty_program, ["company"]) !=\
		ref_doc.company:
		frappe.throw(_("The Loyalty Program isn't valid for the selected company"))

	if loyalty_program and points_to_redeem:
		loyalty_program_details = get_loyalty_program_details(ref_doc.customer, loyalty_program,
			posting_date, ref_doc.company)

		if points_to_redeem > loyalty_program_details.loyalty_points:
			frappe.throw(_("You don't have enought Loyalty Points to redeem"))

		loyalty_amount = flt(points_to_redeem * loyalty_program_details.conversion_factor)

		if loyalty_amount > ref_doc.grand_total:
			frappe.throw(_("You can't redeem Loyalty Points having more value than the Grand Total."))

		if not ref_doc.loyalty_amount and ref_doc.loyalty_amount != loyalty_amount:
			ref_doc.loyalty_amount = loyalty_amount

		if ref_doc.doctype == "Sales Invoice":
			ref_doc.loyalty_program = loyalty_program
			if not ref_doc.loyalty_redemption_account:
				ref_doc.loyalty_redemption_account = loyalty_program_details.expense_account

			if not ref_doc.loyalty_redemption_cost_center:
				ref_doc.loyalty_redemption_cost_center = loyalty_program_details.cost_center

		elif ref_doc.doctype == "Sales Order":
			return loyalty_amount