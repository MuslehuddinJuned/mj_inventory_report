from odoo import models, fields, tools, api
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class ImexInventoryReport(models.Model):
    _name = "imex.inventory.report"
    _description = "Inventory Summary Report"
    _auto = False
    _order = "product_id"

    product_id = fields.Many2one("product.product", readonly=True)
    product_uom = fields.Many2one("uom.uom", readonly=True)
    product_category = fields.Many2one("product.category", readonly=True)
    location = fields.Many2one("stock.location", readonly=True)
    standard_price = fields.Float("Unit Cost", related="product_id.standard_price", readonly=True)
    total_value = fields.Float("Total Value", readonly=True)

    initial = fields.Float(readonly=True)
    product_in = fields.Float(readonly=True)
    product_out = fields.Float(readonly=True)
    balance = fields.Float(readonly=True)


    def action_open_product(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Product',
            'res_model': 'product.product',
            'view_mode': 'form',
            'res_id': self.product_id.id,
            'target': 'current',
        }

    def action_view_move_history(self):
        self.ensure_one()

        ctx = self.env.context
        date_from = ctx.get('date_from')
        date_to = ctx.get('date_to')

        if not date_from or not date_to:
            raise UserError("Date range is missing. Please open the report from the wizard.")

        domain = [
            ('state', '=', 'done'),
            ('product_id', '=', self.product_id.id),
            '|',
            ('location_id', '=', self.location.id),
            ('location_dest_id', '=', self.location.id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Move History',
            'res_model': 'stock.move.line',
            'view_mode': 'list,form',
            'domain': domain,
            'target': 'current',
        }
        
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute("""
            CREATE VIEW imex_inventory_report AS (
                SELECT
                    ROW_NUMBER() OVER () AS id,

                    pp.id AS product_id,
                    pt.uom_id AS product_uom,
                    pt.categ_id AS product_category,
                    sl.id AS location,

                    0.0 AS initial,
                    0.0 AS product_in,
                    0.0 AS product_out,
                    0.0 AS balance,
                    0.0 AS total_value

                FROM product_product pp
                JOIN product_template pt
                    ON pt.id = pp.product_tmpl_id

                CROSS JOIN stock_location sl
                WHERE sl.usage = 'internal'
            )
        """)


    def read(self, fields=None, load='_classic_read'):
        records = super().read(fields, load)

        ctx = self.env.context
        date_from = ctx.get('date_from')
        date_to = ctx.get('date_to')
        location_id = ctx.get('location_id')

        if not date_from or not date_to or not location_id:
            return records

        date_from_dt = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT)
        date_to_dt = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT) + timedelta(days=1)

        cr = self.env.cr

        cr.execute("""
            SELECT
                pp.id AS product_id,

                COALESCE(SUM(
                    CASE
                        WHEN sm.date < %(date_from)s
                        AND sml.location_dest_id = %(location_id)s
                            THEN sml.quantity
                        WHEN sm.date < %(date_from)s
                        AND sml.location_id = %(location_id)s
                            THEN -sml.quantity
                        ELSE 0
                    END
                ), 0) AS initial,

                COALESCE(SUM(
                    CASE
                        WHEN sm.date >= %(date_from)s
                        AND sm.date < %(date_to)s
                        AND sml.location_dest_id = %(location_id)s
                            THEN sml.quantity
                        ELSE 0
                    END
                ), 0) AS product_in,

                COALESCE(SUM(
                    CASE
                        WHEN sm.date >= %(date_from)s
                        AND sm.date < %(date_to)s
                        AND sml.location_id = %(location_id)s
                            THEN sml.quantity
                        ELSE 0
                    END
                ), 0) AS product_out

            FROM product_product pp
            LEFT JOIN stock_move_line sml ON sml.product_id = pp.id
            LEFT JOIN stock_move sm ON sm.id = sml.move_id AND sm.state = 'done'
            GROUP BY pp.id
        """, {
            'date_from': date_from_dt,
            'date_to': date_to_dt,
            'location_id': location_id,
        })

        result = {
            product_id: (initial, product_in, product_out)
            for product_id, initial, product_in, product_out in cr.fetchall()
        }

        for rec in records:
            product = rec.get('product_id')
            if not product:
                continue

            product_id = product[0] if isinstance(product, (list, tuple)) else product

            initial, product_in, product_out = result.get(product_id, (0, 0, 0))

            balance = initial + product_in - product_out

            rec['initial'] = initial
            rec['product_in'] = product_in
            rec['product_out'] = product_out
            rec['balance'] = balance
            rec['total_value'] = balance * rec.get('standard_price', 0.0)

        return records
