function schedule_us_payroll_recalculation(frm) {
    if (!frm.doc.employee) {
        return;
    }

    clearTimeout(frm.__us_payroll_recalc_timer);

    frm.__us_payroll_recalc_timer = setTimeout(() => {
        frappe.call({
            method: "frappe_us_payroll.payroll.salary_slip.recalculate",
            args: {
                salary_slip: frm.doc,
            },
            freeze: false,
            callback(r) {
                if (!r.message) {
                    return;
                }

                frm.set_value("deductions", r.message.deductions);
                frm.refresh_field("deductions");
            },
        });
    }, 250);
}

frappe.ui.form.on("Salary Detail", {
    amount(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        if (row.parentfield === "earnings") {
            schedule_us_payroll_recalculation(frm);
        }
    },
});