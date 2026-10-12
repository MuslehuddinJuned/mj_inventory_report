# -*- coding: utf-8 -*-
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

PERIODS = [
    ("this_month", "This Month"),
    ("last_month", "Last Month"),
    ("this_quarter", "This Quarter"),
    ("last_quarter", "Last Quarter"),
    ("this_year", "This Year"),
    ("last_year", "Last Year"),
    ("last_12_months", "Last 12 Months"),
    ("custom", "Custom"),
]


def _period_range(period, today):
    """Return the (date_from, date_to) pair for a named period."""
    quarter_start = date(today.year, 3 * ((today.month - 1) // 3) + 1, 1)

    if period == "this_month":
        return today.replace(day=1), today
    if period == "last_month":
        start = today.replace(day=1) - relativedelta(months=1)
        return start, start + relativedelta(months=1, days=-1)
    if period == "this_quarter":
        return quarter_start, today
    if period == "last_quarter":
        start = quarter_start - relativedelta(months=3)
        return start, start + relativedelta(months=3, days=-1)
    if period == "this_year":
        return date(today.year, 1, 1), today
    if period == "last_year":
        return date(today.year - 1, 1, 1), date(today.year - 1, 12, 31)
    if period == "last_12_months":
        return today - relativedelta(years=1) + timedelta(days=1), today
    return None, None  # custom


class ImexInventoryWizard(models.TransientModel):
    """Optional entry point for running the Inventory In/Out Summary on a
    custom period / scope.  The menu item goes straight to the report
    (last 365 days) and this wizard is reached via its "Change Period" button.
    """

    _name = "imex.inventory.wizard"
    _description = "Inventory Report Wizard"

    period = fields.Selection(
        PERIODS,
        string="Period",
        default="last_12_months",
        required=True,
        help="Pick a preset range, or choose Custom to type the dates yourself.",
    )
    date_from = fields.Date(required=True, default=lambda self: date.today() - timedelta(days=365))
    date_to = fields.Date(required=True, default=fields.Date.context_today)
    location_id = fields.Many2one(
        "stock.location",
        string="Location",
        domain=[("usage", "=", "internal")],
        help="Leave empty to include every internal location.",
    )
    barcode = fields.Char(string="Scan Barcode")
    product_ids = fields.Many2many("product.product", string="Products")
    product_category_ids = fields.Many2many("product.category", string="Product Categories")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ctx = self.env.context
        # opened from "Change Period" on the report -> keep the dates we were
        # handed instead of overwriting them with a preset
        if ctx.get("default_date_from") or ctx.get("default_date_to"):
            res["period"] = "custom"
        elif res.get("period") and res["period"] != "custom":
            d_from, d_to = _period_range(res["period"], fields.Date.context_today(self))
            if d_from:
                res["date_from"], res["date_to"] = d_from, d_to
        return res

    @api.onchange("period")
    def _onchange_period(self):
        if self.period and self.period != "custom":
            d_from, d_to = _period_range(self.period, fields.Date.context_today(self))
            if d_from:
                self.date_from = d_from
                self.date_to = d_to

    @api.onchange("date_from", "date_to")
    def _onchange_dates(self):
        """Typing a date by hand switches the preset to Custom."""
        if self.period and self.period != "custom":
            expected = _period_range(self.period, fields.Date.context_today(self))
            if (self.date_from, self.date_to) != expected:
                self.period = "custom"

    @api.onchange("barcode")
    def _onchange_barcode(self):
        if not self.barcode:
            return

        product = self.env["product.product"].search(
            [("barcode", "=", self.barcode)], limit=1
        )
        if not product:
            raise UserError(_("No product found for this barcode."))

        self.product_ids = [(4, product.id)]
        self.barcode = False  # clear for next scan

    def action_view_report(self):
        self.ensure_one()

        if self.date_from > self.date_to:
            raise UserError(_("Date From cannot be after Date To."))

        action = self.env["imex.inventory.report"].action_open_report(
            date_from=self.date_from,
            date_to=self.date_to,
            location_ids=self.location_id.ids,
            product_ids=self.product_ids.ids,
            category_ids=self.product_category_ids.ids,
        )

        if self.product_ids:
            # kanban first when looking at a handful of scanned products
            action["view_mode"] = "kanban,list"
            action["views"] = [v for v in action["views"] if v[1] == "kanban"] + \
                              [v for v in action["views"] if v[1] == "list"]

        return action
