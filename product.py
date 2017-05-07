from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

# ==========================================================================================================================

class product_template(osv.osv):
	
	_inherit = 'product.template'
	
	# METHODS ---------------------------------------------------------------------------------------------------------------
	
	def _get_last_sale(self, cr, uid, ids, name, args, context=None):
	# NIBBLE: DONE! Optimasi dengan cr.execute langsung
		result = {}
		for id in ids:
			cr.execute("""
			SELECT so.date_order, so.id
			FROM sale_order_line so_line
				LEFT JOIN sale_order so
					ON so.id = so_line.order_id
			WHERE so_line.product_id = %d
			ORDER BY date_order DESC
			LIMIT 1
			""" % id)
			for row in cr.dictfetchall():
				result[id] = row['date_order']
		return result
	
	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'latest_inventory_adjustment_date': fields.datetime('Latest Inventory Adjustment Date', readonly=True),
		'latest_inventory_adjustment_employee_id': fields.many2one('hr.employee', 'Latest Inventory Adjustment Employee', readonly=True),
		'last_sale': fields.function(_get_last_sale, string="Last Sale", type='datetime', readonly=True, store=False),
	}
	
	
# ==========================================================================================================================
