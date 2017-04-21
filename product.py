from openerp.osv import osv, fields

# ==========================================================================================================================

class product_product(osv.osv):
	
	_inherit = 'product.product'
	
	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'latest_inventory_adjustment_date': fields.datetime('Latest Inventory Adjustment Date'),
		'latest_inventory_adjustment_employee': fields.many2one('hr.employee', 'Latest Inventory Adjustment Employee'),
	}

# ==========================================================================================================================
