from odoo import fields, models, tools


class GoodsReceiptsReport(models.Model):
    _name = 'goods.receipts.report'
    _description = 'Goods Receipts Report'
    _auto = False
    _order = 'receive_date desc'

    receive_date = fields.Datetime('Receipt Date', readonly=True)
    location_id = fields.Many2one('stock.location', string='From Location', readonly=True)
    location_dest_id = fields.Many2one('stock.location', string='To Location', readonly=True)
    reference = fields.Many2one('stock.picking', string='Reference', readonly=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', readonly=True)
    supplier_id = fields.Many2one('res.partner', 'Supplier', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    product_uom = fields.Many2one('uom.uom', 'Unit', readonly=True)
    product_uom_qty = fields.Float('Quantity Received', readonly=True)
    price_unit = fields.Float('Unit Price', readonly=True)
    total_price = fields.Float('Total Price', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)

    def init(self):
        """All validated receipts (incoming operation type).

        Receipts created from a purchase order take the supplier and unit
        price from the PO; receipts created by hand fall back to the
        receipt's contact and the stock move's own unit price.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s AS (
                SELECT
                    sm.id AS id,
                    sm.location_id AS location_id,
                    sm.location_dest_id AS location_dest_id,
                    sm.picking_id AS reference,
                    po.id AS purchase_order_id,
                    sm.date AS receive_date,
                    COALESCE(po.partner_id, sp.partner_id) AS supplier_id,
                    sm.product_id AS product_id,
                    sm.uom_id AS product_uom,
                    sm.quantity AS product_uom_qty,
                    COALESCE(pol.price_unit, sm.price_unit, 0.0) AS price_unit,
                    sm.quantity * COALESCE(pol.price_unit, sm.price_unit, 0.0) AS total_price,
                    sm.company_id AS company_id
                FROM stock_move sm
                JOIN stock_picking_type spt
                    ON spt.id = sm.picking_type_id AND spt.code = 'incoming'
                LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
                LEFT JOIN purchase_order_line pol ON pol.id = sm.purchase_line_id
                LEFT JOIN purchase_order po ON po.id = pol.order_id
                WHERE sm.state = 'done'
            )
        """ % self._table)
