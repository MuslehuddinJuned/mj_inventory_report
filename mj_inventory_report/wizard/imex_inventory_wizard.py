from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date, timedelta

class ImexInventoryWizard(models.TransientModel):
    _name = "imex.inventory.wizard"
    _description = "Inventory Report Wizard"

    date_from = fields.Date(required=True, default=lambda self: date.today() - timedelta(days=365))
    date_to = fields.Date(required=True, default=fields.Date.context_today)
    location_id = fields.Many2one(
        "stock.location",
        required=True,
        domain=[('usage', '=', 'internal')]
    )
    barcode = fields.Char(string="Scan Barcode")
    product_ids = fields.Many2many("product.product")
    product_category_ids = fields.Many2many("product.category")
    report_type = fields.Selection(
        [
            ('raw_materials', 'Raw Materials'),
            ('assets', 'Assets'),
        ],
        string="Report Type",
        default='raw_materials',
        required=True,
    )

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if not self.barcode:
            return

        if self.report_type != 'assets':
            product = self.env['product.product'].search(
                [('barcode', '=', self.barcode)],
                limit=1
            )

            if not product:
                raise UserError("No product found for this barcode.")

            self.product_ids = [(4, product.id)]
            self.barcode = False  # clear for next scan
        
    def action_view_report(self):
        self.ensure_one()

        if self.date_from > self.date_to:
            raise UserError("Date From cannot be after Date To.")

        domain = [
            ('location', '=', self.location_id.id)
        ]

        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))

        if self.product_category_ids:
            domain.append(('product_category', 'in', self.product_category_ids.ids))

        if self.product_ids:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Inventory Summary',
                'res_model': 'imex.inventory.report',
                'view_mode': 'kanban',
                'domain': domain,
                'context': {
                    'date_from': self.date_from,
                    'date_to': self.date_to,
                    'location_id': self.location_id.id,
                },
            }
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inventory Summary',
            'res_model': 'imex.inventory.report',
            'view_mode': 'list,kanban',
            'domain': domain,
            'context': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'location_id': self.location_id.id,
            },
        }

    def action_view_asset(self):
        self.ensure_one()

        asset = self.env['account.asset.assign'].search(
            [('barcode', '=', self.barcode)]
        )

        if not asset:
            raise UserError("No asset found for this barcode.")

        if len(asset) > 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Assets',
                'res_model': 'account.asset.assign',
                'view_mode': 'list,form',
                'domain': [('id', 'in', asset.ids)],
            }
            
        return {
            'type': 'ir.actions.act_window',
            'name': 'Asset',
            'res_model': 'account.asset.assign',
            'view_mode': 'form',
            'res_id': asset.id,
            'target': 'current',
        }


    