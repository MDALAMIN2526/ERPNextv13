# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import today, now_datetime
from frappe.model.document import Document

class InpatientRecord(Document):
	def after_insert(self):
		frappe.db.set_value("Patient", self.patient, "inpatient_status", "Admission Scheduled")
		frappe.db.set_value("Patient", self.patient, "inpatient_record", self.name)

	def validate(self):
		self.validate_already_scheduled_or_admitted()
		if self.status == "Discharged":
			frappe.db.set_value("Patient", self.patient, "inpatient_status", None)
			frappe.db.set_value("Patient", self.patient, "inpatient_record", None)

	def validate_already_scheduled_or_admitted(self):
		query = """
			select name, status
			from `tabInpatient Record`
			where (status = 'Admitted' or status = 'Admission Scheduled')
			and name != %(name)s and patient = %(patient)s
			"""

		ip_record = frappe.db.sql(query,{
				"name": self.name,
				"patient": self.patient
			}, as_dict = 1)

		if ip_record:
			msg = _(("Already {0} Patient {1} with Inpatient Record ").format(ip_record[0].status, self.patient) \
				+ """ <b><a href="#Form/Inpatient Record/{0}">{0}</a></b>""".format(ip_record[0].name))
			frappe.throw(msg)

	def admit(self, bed_location, datetime_in, expected_discharge=None):
		admit_patient(self, bed_location, datetime_in, expected_discharge)

	def discharge(self):
		discharge_patient(self)

	def transfer(self, bed_location, datetime_in, leave_from):
		if leave_from:
			patient_leave_bed_location(self, datetime_in, leave_from)
		if bed_location:
			transfer_patient(self, bed_location, datetime_in)

@frappe.whitelist()
def schedule_inpatient(patient, scheduled_to=None):
	patient_obj = frappe.get_doc('Patient', patient)
	inpatient_record = frappe.new_doc('Inpatient Record')
	inpatient_record.patient = patient
	inpatient_record.patient_name = patient_obj.patient_name
	inpatient_record.gender = patient_obj.sex
	inpatient_record.blood_group = patient_obj.blood_group
	inpatient_record.dob = patient_obj.dob
	inpatient_record.mobile = patient_obj.mobile
	inpatient_record.email = patient_obj.email
	inpatient_record.phone = patient_obj.phone
	inpatient_record.status = "Admission Scheduled"
	inpatient_record.scheduled_date = today()
	inpatient_record.save(ignore_permissions = True)

@frappe.whitelist()
def schedule_discharge(patient):
	inpatient_record_id = frappe.db.get_value('Patient', patient, 'inpatient_record')
	if inpatient_record_id:
		frappe.db.set_value("Inpatient Record", inpatient_record_id, "status", "Discharge Scheduled")

def discharge_patient(inpatient_record):
	if inpatient_record.bed_locations:
		for bed_location in inpatient_record.bed_locations:
			if bed_location.left != 1:
				bed_location.left = True
				bed_location.left_datetime = now_datetime()
				frappe.db.set_value("Healthcare Service Unit", bed_location.bed_location, "occupied", False)

	inpatient_record.discharge_date = today()
	inpatient_record.status = "Discharged"

	inpatient_record.save(ignore_permissions = True)

def admit_patient(inpatient_record, bed_location, datetime_in, expected_discharge=None):
	inpatient_record.admitted_datetime = datetime_in
	inpatient_record.status = "Admitted"
	inpatient_record.expected_discharge = expected_discharge

	inpatient_record.set('bed_locations', [])
	transfer_patient(inpatient_record, bed_location, datetime_in)

	frappe.db.set_value("Patient", inpatient_record.patient, "inpatient_status", "Admitted")
	frappe.db.set_value("Patient", inpatient_record.patient, "inpatient_record", inpatient_record.name)

def transfer_patient(inpatient_record, bed_location, datetime_in):
	item_line = inpatient_record.append('bed_locations', {})
	item_line.bed_location = bed_location
	item_line.datetime_in = datetime_in

	inpatient_record.save(ignore_permissions = True)

	frappe.db.set_value("Healthcare Service Unit", bed_location, "occupied", True)

def patient_leave_bed_location(inpatient_record, leave_datetime, leave_from):
	if inpatient_record.bed_locations:
		for bed_location in inpatient_record.bed_locations:
			if bed_location.left != 1 and bed_location.bed_location == leave_from:
				bed_location.left = True
				bed_location.left_datetime = leave_datetime
				frappe.db.set_value("Healthcare Service Unit", bed_location.bed_location, "occupied", False)
	inpatient_record.save(ignore_permissions = True)
