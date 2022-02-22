# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class SubcontractingOrder(Document):
	def validate(self):
		self.validate_purchase_order()

	def validate_purchase_order(self):
		if self.get("purchase_order"):
			po = frappe.get_doc("Purchase Order", self.get("purchase_order"))

			if po.docstatus != 1:
				frappe.throw(_(f"Please submit Purchase Order {po.name} before proceeding."))

			if po.is_subcontracted != "Yes":
				frappe.throw(_("Please select a valid Purchase Order that is configured for Subcontracting."))


@frappe.whitelist()
def make_subcontracting_receipt(source_name, target_doc=None):
	return get_mapped_subcontracting_receipt(source_name, target_doc)

def get_mapped_subcontracting_receipt(source_name, target_doc=None, ignore_permissions=False):
	fields = {
		"Subcontracting Order": {
			"doctype": "Subcontracting Receipt",
			"validation": {
				"docstatus": ["=", 1],
			}
		},
		"Subcontracting Order Item": {
			"doctype": "Subcontracting Receipt Item",
		},
	}

	doc = get_mapped_doc("Subcontracting Order", source_name, fields)
	return doc