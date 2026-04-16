{
    "name": "Inventory Report",
    "version": "19.0.1.0.0",
    "summary": "Comprehensive inventory reporting with product-wise stock movements and material receipt details.",
    "description":  """  
                    1. Product-wise inventory report with opening, inward, outward and closing stock for a given date range and location. 
                    2. Material Receive Report (purchase) with date, supplier name, quantity, unit cost, total cost.
                """,
    'author': 'Musleh Uddin Juned',
    'website': 'http://www.zachai-bachhai.com',
    "category": "Inventory",
    "depends": ["stock", 'purchase', 'purchase_stock'],
    "data": [
        "security/ir.model.access.csv",
        'views/goods_receipts_report_view.xml',
        'views/imex_inventory_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}