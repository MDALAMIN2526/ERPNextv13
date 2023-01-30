// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt


{% include 'erpnext/selling/sales_common.js' %}

frappe.ui.form.on('Quotation', {
	setup: function(frm) {
		frm.custom_make_buttons = {
			'Sales Order': 'Sales Order'
		},

		frm.set_query("quotation_to", function() {
			return{
				"filters": {
					"name": ["in", ["Customer", "Lead"]],
				}
			}
		});

		frm.set_df_property('packed_items', 'cannot_add_rows', true);
		frm.set_df_property('packed_items', 'cannot_delete_rows', true);

		frm.set_query('company_address', function(doc) {
			if(!doc.company) {
				frappe.throw(__('Please set Company'));
			}

			return {
				query: 'frappe.contacts.doctype.address.address.address_query',
				filters: {
					link_doctype: 'Company',
					link_name: doc.company
				}
			};
		});
	},

	refresh: function(frm) {
		frm.trigger("set_label");
		frm.trigger("set_dynamic_field_label");
	},

	quotation_to: function(frm) {
		frm.trigger("set_label");
		frm.trigger("toggle_reqd_lead_customer");
		frm.trigger("set_dynamic_field_label");
	},

	set_label: function(frm) {
		frm.fields_dict.customer_address.set_label(__(frm.doc.quotation_to + " Address"));
	}
});

erpnext.selling.QuotationController = class QuotationController extends erpnext.selling.SellingController {
	onload(doc, dt, dn) {
		super.onload(doc, dt, dn);
	}
	party_name() {
		var me = this;
		erpnext.utils.get_party_details(this.frm, null, null, function() {
			me.apply_price_list();
		});

		if(me.frm.doc.quotation_to=="Lead" && me.frm.doc.party_name) {
			me.frm.trigger("get_lead_details");
		}
	}
	refresh(doc, dt, dn) {
		super.refresh(doc, dt, dn);
		frappe.dynamic_link = {
			doc: this.frm.doc,
			fieldname: 'party_name',
			doctype: doc.quotation_to == 'Customer' ? 'Customer' : 'Lead',
		};

		var me = this;

		if (doc.__islocal && !doc.valid_till) {
			if(frappe.boot.sysdefaults.quotation_valid_till){
				this.frm.set_value('valid_till', frappe.datetime.add_days(doc.transaction_date, frappe.boot.sysdefaults.quotation_valid_till));
			} else {
				this.frm.set_value('valid_till', frappe.datetime.add_months(doc.transaction_date, 1));
			}
		}

		if (doc.docstatus == 1 && !["Lost", "Ordered"].includes(doc.status)) {
<<<<<<< HEAD
			if (frappe.boot.sysdefaults.allow_sales_order_creation_for_expired_quotation
				|| (!doc.valid_till)
				|| frappe.datetime.get_diff(doc.valid_till, frappe.datetime.get_today()) >= 0) {
					this.frm.add_custom_button(
						__("Sales Order"),
						this.frm.cscript["Make Sales Order"],
						__("Create")
					);
				}
=======
			this.frm.add_custom_button(
				__("Sales Order"),
				() => this.make_sales_order(),
				__("Create")
			);
>>>>>>> cef7dfd0b4 (feat: Dialog to select alternative item before creating Sales order)

			if(doc.status!=="Ordered") {
				this.frm.add_custom_button(__('Set as Lost'), () => {
						this.frm.trigger('set_as_lost_dialog');
					});
				}

			if(!doc.auto_repeat) {
				cur_frm.add_custom_button(__('Subscription'), function() {
					erpnext.utils.make_subscription(doc.doctype, doc.name)
				}, __('Create'))
			}

			cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
		}

		if (this.frm.doc.docstatus===0) {
			this.frm.add_custom_button(__('Opportunity'),
				function() {
					erpnext.utils.map_current_doc({
						method: "erpnext.crm.doctype.opportunity.opportunity.make_quotation",
						source_doctype: "Opportunity",
						target: me.frm,
						setters: [
							{
								label: "Party",
								fieldname: "party_name",
								fieldtype: "Link",
								options: me.frm.doc.quotation_to,
								default: me.frm.doc.party_name || undefined
							},
							{
								label: "Opportunity Type",
								fieldname: "opportunity_type",
								fieldtype: "Link",
								options: "Opportunity Type",
								default: me.frm.doc.order_type || undefined
							}
						],
						get_query_filters: {
							status: ["not in", ["Lost", "Closed"]],
							company: me.frm.doc.company
						}
					})
				}, __("Get Items From"), "btn-default");
		}

		this.toggle_reqd_lead_customer();

	}

	make_sales_order() {
		var me = this;

		let has_alternative_item = this.frm.doc.items.some((item) => item.is_alternative);
		if (has_alternative_item) {
			this.show_alternative_item_dialog();
		} else {
			frappe.model.open_mapped_doc({
				method: "erpnext.selling.doctype.quotation.quotation.make_sales_order",
				frm: me.frm
			});
		}
	}

	set_dynamic_field_label(){
		if (this.frm.doc.quotation_to == "Customer")
		{
			this.frm.set_df_property("party_name", "label", "Customer");
			this.frm.fields_dict.party_name.get_query = null;
		}

		if (this.frm.doc.quotation_to == "Lead")
		{
			this.frm.set_df_property("party_name", "label", "Lead");

			this.frm.fields_dict.party_name.get_query = function() {
				return{	query: "erpnext.controllers.queries.lead_query" }
			}
		}
	}

	toggle_reqd_lead_customer() {
		var me = this;

		// to overwrite the customer_filter trigger from queries.js
		this.frm.toggle_reqd("party_name", this.frm.doc.quotation_to);
		this.frm.set_query('customer_address', this.address_query);
		this.frm.set_query('shipping_address_name', this.address_query);
	}

	tc_name() {
		this.get_terms();
	}

	address_query(doc) {
		return {
			query: 'frappe.contacts.doctype.address.address.address_query',
			filters: {
				link_doctype: frappe.dynamic_link.doctype,
				link_name: doc.party_name
			}
		};
	}

	validate_company_and_party(party_field) {
		if(!this.frm.doc.quotation_to) {
			frappe.msgprint(__("Please select a value for {0} quotation_to {1}", [this.frm.doc.doctype, this.frm.doc.name]));
			return false;
		} else if (this.frm.doc.quotation_to == "Lead") {
			return true;
		} else {
			return super.validate_company_and_party(party_field);
		}
	}

	get_lead_details() {
		var me = this;
		if(!this.frm.doc.quotation_to === "Lead") {
			return;
		}

		frappe.call({
			method: "erpnext.crm.doctype.lead.lead.get_lead_details",
			args: {
				'lead': this.frm.doc.party_name,
				'posting_date': this.frm.doc.transaction_date,
				'company': this.frm.doc.company,
			},
			callback: function(r) {
				if(r.message) {
					me.frm.updating_party_details = true;
					me.frm.set_value(r.message);
					me.frm.refresh();
					me.frm.updating_party_details = false;

				}
			}
		})
	}

	show_alternative_item_dialog() {
		// Create a `{original item: [alternate items]}` map
		var me = this;
		let item_alt_map = {};

		this.frm.doc.items.filter(
			(item) => item.is_alternative
		).forEach((item) =>
			(item_alt_map[item.alternative_to] ??= []).push(item.item_code)
		)

		const fields = [{
			fieldtype:"Link",
			fieldname:"original_item",
			options: "Item",
			label: __("Original Item"),
			read_only: 1,
			in_list_view: 1,
		},
		{
			fieldtype:"Link",
			fieldname:"alternative_item",
			options: "Item",
			label: __("Alternative Item"),
			in_list_view: 1,
			get_query: (row, cdt, cdn) => {
				return {
					filters: {
						"item_code": ["in", item_alt_map[row.original_item]]
					}
				}
			},
		}];

		this.data = Object.keys(item_alt_map).map((item) => {
			return {"original_item": item}
		});

		const dialog = new frappe.ui.Dialog({
			title: __("Select Alternatives for Sales Order"),
			fields: [
				{
					fieldname: "alternative_items",
					fieldtype: "Table",
					label: "Items with Alternatives",
					cannot_add_rows: true,
					in_place_edit: true,
					reqd: 1,
					data: this.data,
					description: __("Select an alternative to be used in the Sales Order or leave it blank to use the original item."),
					get_data: () => {
						return this.data;
					},
					fields: fields
				},
			],
			primary_action: function() {
				frappe.model.open_mapped_doc({
					method: "erpnext.selling.doctype.quotation.quotation.make_sales_order",
					frm: me.frm,
					args: {
						mapping: dialog.get_value("alternative_items")
					}
				});
				dialog.hide();
			},
			primary_action_label: __('Continue')
		});

		dialog.show();
	}
};

cur_frm.script_manager.make(erpnext.selling.QuotationController);

frappe.ui.form.on("Quotation Item", "items_on_form_rendered", "packed_items_on_form_rendered", function(frm, cdt, cdn) {
	// enable tax_amount field if Actual
})

frappe.ui.form.on("Quotation Item", "stock_balance", function(frm, cdt, cdn) {
	var d = frappe.model.get_doc(cdt, cdn);
	frappe.route_options = {"item_code": d.item_code};
	frappe.set_route("query-report", "Stock Balance");
})
