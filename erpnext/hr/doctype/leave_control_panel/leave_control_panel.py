# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import webnotes
from webnotes.utils import cint, cstr, flt, nowdate
from webnotes.model.doc import Document
from webnotes.model.code import get_obj
from webnotes import msgprint, throw, _

class DocType:
	def __init__(self, doc, doclist):
		self.doc = doc
		self.doclist = doclist

	def get_employees(self):
		leave_emp_map = {self.doc.employment_type: "employment_type", self.doc.branch: "branch", 
			self.doc.designation: "designation", self.doc.department: "department", 
			self.doc.grade: "grade"}
		condition = ""

		for leave_field, emp_field in leave_emp_map.items():
			if leave_field:
				condition += " and " + emp_field + "='" + leave_field + "'"

		return frappe.conn.sql("""select name from `tabEmployee` where status='Active'%s""", condition)

	def validate_values(self):
		val_dict = {self.doc.period: "Period", self.doc.leave_type: "Leave Type", 
			self.doc.no_of_days: "New Leaves Allocated"}
		for d in val_dict:
			if not d:
				throw("{enter}: {field}".format(**{
					"enter": _("Please enter"),
					"field": val_dict[d]
				}))

	def allocate_leave(self):
		self.validate_values()
		for d in self.get_employees():
			la = Document('Leave Allocation')
			la.employee = cstr(d[0])
			la.employee_name = webnotes.conn.get_value("Employee", cstr(d[0]), "employee_name")
			la.leave_type = self.doc.leave_type
			la.period = self.doc.period
			la.posting_date = nowdate()
			la.carry_forward = cint(self.doc.carry_forward)
			la.new_leaves_allocated = flt(self.doc.no_of_days)
			la_obj = get_obj(doc=la)
			la_obj.doc.docstatus = 1
			la_obj.validate()
			la_obj.on_update()
			la_obj.doc.save(1)
		msgprint(_("Leaves Allocated Successfully"))