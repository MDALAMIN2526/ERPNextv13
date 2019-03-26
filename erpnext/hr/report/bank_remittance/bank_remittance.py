# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{
			"label": _("Payroll Number"),
			"fieldtype": "Link",
			"fieldname": "payroll_no",
			"options": "Payroll Entry",
			"width": 150
		},
		{
			"label": _("Debit A/C Number"),
			"fieldtype": "Int",
			"fieldname": "debit_account",
			"hidden": 1,
			"width": 200
		},
		{
			"label": _("Payment Date"),
			"fieldtype": "data",
			"fieldname": "payment_date",
			"width": 100
		},
		{
			"label": _("Employee Name"),
			"fieldtype": "Link",
			"fieldname": "employee_name",
			"options": "Employee",
			"width": 200
		},
		{
			"label": _("Bank Name"),
			"fieldtype": "Data",
			"fieldname": "bank_name",
			"width": 50
		},
		{
			"label": _("Employee A/C Number"),
			"fieldtype": "Int",
			"fieldname": "employee_account_no",
			"width": 50
		},
		{
			"label": _("IFSC Code"),
			"fieldtype": "data",
			"fieldname": "bank_code",
			"width": 100
		},
		{
			"label": _("Currency"),
			"fieldtype": "data",
			"fieldname": "currency",
			"width": 50
		},
		{
			"label": _("Net Salary Amount"),
			"fieldtype": "Currency",
			"options": "currency",
			"fieldname": "amount",
			"width": 100
		}
	]
	data = get_report_data(filters)

	return columns, data


def get_report_data(filters):
	data = []
	entries = frappe.get_all("Payroll Entry", fields=[" * "] )
	for entry in entries:
		employee_details = frappe.get_list(
		"Payroll Employee Detail",
		filters = {"parent": entry.name},
		fields=["*"]
		)
		if frappe.db.get_value("Account", entry.payment_account, "account_type") == "Bank" :
			for details in employee_details:
				payment_date = frappe.db.get_value("Salary Slip", {
					"payroll_entry": entry.name,
					"Employee": details.employee
				}, "modified")
				amount_to_pay = frappe.db.get_value("Salary Slip", {
					"payroll_entry": entry.name,
					"Employee": details.employee
				}, "net_pay")
				row = {
					"payroll_no": entry.name,
					"debit_account": frappe.db.get_value("Bank Account", {"account": entry.payment_account}, "bank_account_no", debug = 1),
					"payment_date": frappe.utils.formatdate(payment_date.strftime('%Y-%m-%d')),
					"bank_name": frappe.db.get_value("Employee", details.employee, "bank_name"),
					"employee_account_no": frappe.db.get_value("Employee", details.employee, "bank_ac_no"),
					"bank_code": frappe.db.get_value("Employee", details.employee, "ifsc_code"),
					"employee_name": details.employee+": " + details.employee_name,
					"currency": frappe.get_cached_value('Company', filters.company,  'default_currency'),
					"amount": amount_to_pay,
				}

				data.append(row)

	return data
