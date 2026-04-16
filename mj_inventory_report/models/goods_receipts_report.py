from odoo import fields, models, tools

class GoodsReceiptsReport(models.Model):
    _name = 'goods.receipts.report'
    _description = 'goods Receipts Report'
    _auto = False
    _order = 'receive_date desc'

    receive_date = fields.Datetime('Receipt Date', readonly=True)
    location_id = fields.Many2one('stock.location', string='From Location', readonly=True)
    location_dest_id = fields.Many2one('stock.location', string='To Location', readonly=True)
    reference = fields.Many2one('stock.picking', string='Reference', readonly=True)
    supplier_id = fields.Many2one('res.partner', 'Supplier', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    product_uom_qty = fields.Float('Quantity Received', readonly=True)
    price_unit = fields.Float('Unit Price', readonly=True)
    total_price = fields.Float('Total Price', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s AS (
                SELECT
                    sm.id AS id, location_id, location_dest_id, sm.picking_id AS reference,
                    sm.date AS receive_date,
                    po.partner_id AS supplier_id,
                    sm.product_id AS product_id,
                    sm.product_uom_qty AS product_uom_qty,
                    pol.price_unit AS price_unit,
                    (sm.product_uom_qty * pol.price_unit) AS total_price
                FROM stock_move sm
                JOIN purchase_order_line pol ON sm.purchase_line_id = pol.id
                JOIN purchase_order po ON pol.order_id = po.id
                WHERE sm.state = 'done'
                    AND sm.picking_type_id IN (
                        SELECT id FROM stock_picking_type WHERE code = 'incoming'
                    )
            )
        """ % self._table)
