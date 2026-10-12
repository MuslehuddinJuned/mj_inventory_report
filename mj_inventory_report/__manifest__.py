{
    "name": "Inventory Report",
    "version": "19.0.1.1.0",
    "summary": "Comprehensive inventory reporting with product-wise stock movements and material receipt details.",
    "description":  """  
                    1. Product-wise inventory In/Out Summary with opening, inward, outward, closing stock and value for a given
                       period (preset or custom), location, products and categories. Exportable, filterable, groupable and printable (PDF).
                    2. Material Receive Report (purchase) with date, supplier name, quantity, unit, unit cost, total cost.
                       Only validated (Done) receipts created from a Purchase Order are included.
                """,
    'author': 'Musleh Uddin Juned',
    'website': 'http://www.zachai-bachhai.com',
    "category": "Inventory",
    "depends": ["stock", 'purchase', 'purchase_stock'],
    "data": [
        "security/ir.model.access.csv",
        'views/goods_receipts_report_view.xml',
        'views/imex_inventory_views.xml',
        'report/imex_inventory_report.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}