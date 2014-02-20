# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import add_days, add_years, cint, getdate
from frappe.model import db_exists
from frappe.model.doc import addchild, make_autoname
from frappe.model.bean import copy_doclist
from frappe import msgprint, throw, _
import datetime

class DocType:
	def __init__(self,doc,doclist=[]):
		self.doc = doc
		self.doclist = doclist

	def autoname(self):
		self.doc.name = make_autoname(self.doc.holiday_list_name + "/.###")

	def validate(self):
		self.update_default_holiday_list()

	def get_weekly_off_dates(self):
		self.validate_values()
		period_start_date, period_end_date = self.get_period_start_end_dates()
		date_list = self.get_weekly_off_date_list(period_start_date, period_end_date)
		last_idx = max([cint(d.idx) for d in self.doclist.get(
			{"parentfield": "holiday_list_details"})] or [0,])
		for i, d in enumerate(date_list):
			ch = addchild(self.doc, 'holiday_list_details', 'Holiday', self.doclist)
			ch.description = self.doc.weekly_off
			ch.holiday_date = d
			ch.idx = last_idx + i + 1

	def validate_values(self):
		if not self.doc.period:
			throw(_("Please select Period"))
		if not self.doc.weekly_off:
			throw(_("Please select weekly off day"))

	def get_period_start_end_dates(self):
		return frappe.conn.sql("""select from_date, to_date
			from `tabPeriod` where name=%s""", (self.doc.period,))[0]

	def get_weekly_off_date_list(self, year_start_date, year_end_date):
		from frappe.utils import getdate
		year_start_date, year_end_date = getdate(year_start_date), getdate(year_end_date)

		from dateutil import relativedelta
		from datetime import timedelta
		import calendar

		date_list = []
		weekday = getattr(calendar, (self.doc.weekly_off).upper())
		reference_date = year_start_date + relativedelta.relativedelta(weekday=weekday)

		while reference_date <= year_end_date:
			date_list.append(reference_date)
			reference_date += timedelta(days=7)

		return date_list

	def clear_table(self):
		self.doclist = self.doc.clear_table(self.doclist, 'holiday_list_details')

	def update_default_holiday_list(self):
		frappe.conn.sql("""update `tabHoliday List` set is_default=0 
			where ifnull(is_default, 0)=1 and period=%s""", (self.doc.period,))