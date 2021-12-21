# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import unittest
from datetime import date

import frappe

from erpnext.utilities.bulk_transaction import transaction_processing


class TestBulkTransactionLogger(unittest.TestCase):

	def test_for_single_record(self):
		create_company()
		create_customer()
		create_item()
		so_name = create_so()
		transaction_processing([{"name": so_name}], "Sales Order", "Sales Invoice")
		data = frappe.db.get_list("Sales Invoice", filters = {"posting_date": date.today(), "customer": "Bulk Customer"}, fields=["*"])
		if not data:
			self.fail("No Sales Invoice Created !")

	def test_entry_in_log(self):
		create_company()
		create_customer()
		create_item()
		so_name = create_so()
		transaction_processing([{"name": so_name}], "Sales Order", "Sales Invoice")
		doc = frappe.get_doc("Bulk Transaction Logger", str(date.today()))
		for d in doc.get("logger_data"):
			if d.name == so_name:
				self.assertEqual(d.name, so_name)
				self.assertEqual(d.transaction_status, "Success")
				self.assertEqual(d.from_doctype, "Sales Order")
				self.assertEqual(d.to_doctype, "Sales Invoice")
				self.assertEqual(d.retried, 0)


def create_company():
	if not frappe.db.exists('Company', 'Test Bulk'):
		frappe.get_doc({
			'doctype': 'Company',
			'company_name': 'Test Bulk',
			'country': 'India',
			'default_currency': 'INR'
		}).insert()

def create_customer():
	if not frappe.db.exists('Customer', 'Bulk Customer'):
		frappe.get_doc({
			'doctype': 'Customer',
			'customer_name': 'Bulk Customer'
		}).insert()

def create_item():
	if not frappe.db.exists("Item", "MK"):
		frappe.get_doc({
			"doctype": "Item",
			"item_code": "MK",
			"item_name": "Milk",
			"description": "Milk",
			"item_group": "Products"
		}).insert()

def create_so():
	so = frappe.new_doc("Sales Order")
	so.customer = "Bulk Customer"
	so.company = "Test Bulk"
	so.transaction_date = date.today()
	so.append("items", {
		"item_code": "MK",
		"delivery_date": date.today(),
		"qty": 10,
		"rate": 80,
	})

	so.flags.ignore_validate = True
	so.insert(ignore_mandatory=True)
	so.submit()

	return so.name