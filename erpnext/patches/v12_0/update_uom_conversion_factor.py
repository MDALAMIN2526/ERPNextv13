import frappe


def execute():
	from cpmerp.setup.setup_wizard.operations.install_fixtures import add_uom_data

	frappe.reload_doc("setup", "doctype", "UOM Conversion Factor")
	frappe.reload_doc("setup", "doctype", "UOM")
	frappe.reload_doc("stock", "doctype", "UOM Category")

	add_uom_data()
