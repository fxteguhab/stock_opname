from openerp.osv import osv, fields
from datetime import datetime, timedelta

# ==========================================================================================================================

class product_template(osv.osv):
	
	_inherit = 'product.template'
	
	# METHODS ---------------------------------------------------------------------------------------------------------------
	
	def _get_last_sale(self, cr, uid, ids, name, args, context=None):
		return None
	
	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'latest_inventory_adjustment_date': fields.datetime('Latest Inventory Adjustment Date'),
		'latest_inventory_adjustment_employee_id': fields.many2one('hr.employee', 'Latest Inventory Adjustment Employee'),
		'last_sale': fields.function(_get_last_sale, string="Last Sale", type='datetime', readonly=True, store={}),
	}
	
	
# ==========================================================================================================================
