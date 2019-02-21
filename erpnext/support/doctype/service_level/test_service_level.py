# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals
from erpnext.hr.doctype.employee_group.test_employee_group import make_employee_group
from frappe.utils import now_datetime
import datetime
from datetime import timedelta

import frappe
import unittest

class TestServiceLevel(unittest.TestCase):

	def test_service_level(self):
		test_make_service_level = make_service_level()
		test_get_service_level = get_service_level()
		self.assertEquals(test_make_service_level, test_get_service_level)

def make_service_level():
	employee_group = make_employee_group()
	make_holiday_list()
	service_level = frappe.get_doc({
		"doctype": "Service Level",
		"service_level": "_Test Service Level",
		"holiday_list": "__Test Holiday List",
		"priority": "Medium",
		"employee_group": employee_group,
		"response_time": 2,
		"response_time_period": "Day",
		"resolution_time": 3,
		"resolution_time_period": "Day",
		"support_and_resolution": [
			{
				"workday": "Monday",
				"start_time": "10:00:00",
				"end_time": "18:00:00",
			},
			{
				"workday": "Tuesday",
				"start_time": "10:00:00",
				"end_time": "18:00:00",
			},
			{
				"workday": "Wednesday",
				"start_time": "10:00:00",
				"end_time": "18:00:00",
			},
			{
				"workday": "Thursday",
				"start_time": "10:00:00",
				"end_time": "18:00:00",
			},
			{
				"workday": "Friday",
				"start_time": "10:00:00",
				"end_time": "18:00:00",
			},
			{
				"workday": "Saturday",
				"start_time": "10:00:00",
				"end_time": "18:00:00",
			},
			{
				"workday": "Sunday",
				"start_time": "10:00:00",
				"end_time": "18:00:00",
			}
		]
	})
	service_level_exist = frappe.db.exists("Service Level", "_Test Service Level")
	if not service_level_exist:
		service_level.insert()
		return service_level.service_level
	else:
		return service_level_exist

def get_service_level():
	service_level = frappe.db.exists("Service Level", "_Test Service Level")
	return service_level

def make_holiday_list():
	holiday_list_exist = frappe.db.exists("Holiday List", "__Test Holiday List")
	if not holiday_list_exist:
		now = datetime.datetime.now()
		holiday_list = frappe.get_doc({
			"doctype": "Holiday List",
			"holiday_list_name": "__Test Holiday List",
			"from_date": str(now.year) + "-01-01",
			"to_date": str(now.year) + "-12-31",
			"holidays": [
				{
					"description": "Test Holiday 1",
					"holiday_date": now_datetime().date()+timedelta(days=1)
				},
				{
					"description": "Test Holiday 2",
					"holiday_date": now_datetime().date()+timedelta(days=3)
				},
				{
					"description": "Test Holiday 3",
					"holiday_date": now_datetime().date()+timedelta(days=7)
				},
			]
		}).insert()