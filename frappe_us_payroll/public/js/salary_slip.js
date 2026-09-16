function schedule_us_payroll_recalculation(frm) {
	if (!frm.doc.employee || frm.__us_payroll_syncing) {
		return;
	}

	clearTimeout(frm.__us_payroll_recalc_timer);
	frm.__us_payroll_recalc_timer = setTimeout(() => {
		frappe.call({
			method: "frappe_us_payroll.payroll.salary_slip.recalculate",
			args: { salary_slip: frm.doc },
			freeze: false,
			callback: async (response) => {
				if (!response.message) {
					return;
				}

				frm.__us_payroll_syncing = true;
				try {
					await frm.set_value(response.message);
					frm.refresh_fields([
						"deductions",
						"employer_contributions",
						"us_social_security_taxable_wages",
						"us_medicare_taxable_wages",
						"us_futa_taxable_wages",
						"wa_paid_leave_taxable_wages",
						"wa_unemployment_taxable_wages",
						"total_deduction",
						"net_pay",
					]);
				} finally {
					frm.__us_payroll_syncing = false;
				}
			},
		});
	}, 250);
}

frappe.ui.form.on("Salary Detail", {
	amount(frm, cdt, cdn) {
		if (locals[cdt][cdn].parentfield === "earnings") {
			schedule_us_payroll_recalculation(frm);
		}
	},
	earnings_remove(frm) {
		schedule_us_payroll_recalculation(frm);
	},
});
