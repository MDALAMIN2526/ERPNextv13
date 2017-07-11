// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

/* global frappe, refresh_field */

frappe.ui.form.on("Supplier Scorecard", {

	onload: function(frm) {
		if (frm.doc.indicator_color !== "")
		{
			frm.set_indicator_formatter("status", function(doc) {
				return doc.indicator_color.toLowerCase();
			});
		}
		if (frm.doc.__unsaved == 1)
		{
			//Add the criteria
			frappe.call({
				method: "erpnext.buying.doctype.supplier_scorecard_criteria.supplier_scorecard_criteria.get_criteria_list",
				callback: function(r) {
					for (var j = 0; j < frm.doc.criteria.length; j++)
					{
						if(!frm.doc.criteria[j].hasOwnProperty("criteria_name"))
						{
							frm.get_field("criteria").grid.grid_rows[j].remove();
						}
					}
					for (var i = 0; i < r.message.length; i++)
					{
						var new_row = frm.add_child("criteria");
						new_row.criteria_name = r.message[i].name;
						frm.script_manager.trigger("criteria_name", new_row.doctype, new_row.name);
					}
					refresh_field("criteria");
				}
			});
			//Add the criteria
			frappe.call({
				method: "erpnext.buying.doctype.supplier_scorecard_standing.supplier_scorecard_standing.get_standings_list",
				callback: function(r) {
					for (var j = 0; j < frm.doc.standings.length; j++)
					{
						if(!frm.doc.standings[j].hasOwnProperty("standing_name"))
						{
							frm.get_field("standings").grid.grid_rows[j].remove();
						}
					}
					for (var i = 0; i < r.message.length; i++)
					{
						var new_row = frm.add_child("standings");
						new_row.standing_name = r.message[i].name;
						frm.script_manager.trigger("standing_name", new_row.doctype, new_row.name);
					}
					refresh_field("standings");
				}
			});
		}

	},
	refresh: function(frm) {
		if (frm.dashboard.hasOwnProperty('heatmap')){
			frm.dashboard.heatmap.setLegend([0,20,40,60,80,101],["#991600","#169900"]);
		}
	},
	generate_scorecards:function(frm) {
		frappe.call({
			method: "erpnext.buying.doctype.supplier_scorecard.supplier_scorecard.make_all_scorecards",
			args: {
				"docname": frm.doc.name
			},
			frm: frm
		});
	},
	start_date: function(frm)
	{
		var sd = new Date(frm.doc.start_date);
		if (frm.doc.period === "Per Week"){
			frm.doc.end_date = new Date(sd.getFullYear(),sd.getMonth(),sd.getDate()+7).toISOString();
		} else if (frm.doc.period === "Per Month"){
			frm.doc.end_date = new Date(sd.getFullYear(),sd.getMonth()+1,sd.getDate()).toISOString();
		}else {
			frm.doc.end_date = new Date(sd.getFullYear()+1,sd.getMonth(),sd.getDate()).toISOString();
		}
		frm.refresh_field("end_date");
	}

});

frappe.ui.form.on("Supplier Scorecard Scoring Standing", {

	standing_name: function(frm, cdt, cdn) {
		var d = frappe.get_doc(cdt, cdn);
		return frm.call({
			method: "erpnext.buying.doctype.supplier_scorecard_standing.supplier_scorecard_standing.get_scoring_standing",
			child: d,
			args: {
				standing_name: d.standing_name
			}
		});
	}
});

frappe.ui.form.on("Supplier Scorecard Scoring Variable", {

	variable_label: function(frm, cdt, cdn) {
		var d = frappe.get_doc(cdt, cdn);
		return frm.call({
			method: "erpnext.buying.doctype.supplier_scorecard_variable.supplier_scorecard_variable.get_scoring_variable",
			child: d,
			args: {
				variable_label: d.variable_label
			}
		});
	}
});

frappe.ui.form.on("Supplier Scorecard Scoring Criteria", {

	criteria_name: function(frm, cdt, cdn) {
		var d = frappe.get_doc(cdt, cdn);
		frm.call({
			method: "erpnext.buying.doctype.supplier_scorecard_criteria.supplier_scorecard_criteria.get_variables",
			args: {
				criteria_name: d.criteria_name
			},
			callback: function(r) {
				for (var i = 0; i < r.message.length; i++)
				{
					var exists = false;
					for (var j = 0; j < frm.doc.variables.length; j++)
					{
						if(!frm.doc.variables[j].hasOwnProperty("variable_label"))
						{
							frm.get_field("variables").grid.grid_rows[j].remove();
						}
						else if(frm.doc.variables[j].variable_label === r.message[i])
						{
							exists = true;
						}
					}
					if (!exists){
						var new_row = frm.add_child("variables");
						new_row.variable_label = r.message[i];
						frm.script_manager.trigger("variable_label", new_row.doctype, new_row.name);
					}

				}
				refresh_field("variables");
			}
		});
		return frm.call({
			method: "erpnext.buying.doctype.supplier_scorecard_criteria.supplier_scorecard_criteria.get_scoring_criteria",
			child: d,
			args: {
				criteria_name: d.criteria_name
			}
		});

	}
});



