from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

# ==========================================================================================================================

class product_template(osv.osv):
	
	_inherit = 'product.template'
	
	# METHODS ---------------------------------------------------------------------------------------------------------------
	
	def _get_last_sale(self, cr, uid, ids, name, args, context=None):
		sale_order_obj = self.pool.get('sale.order')
		sale_order_line_obj = self.pool.get('sale.order.line')
		sale_order_line_ids = sale_order_line_obj.search(cr, uid, [('product_id', 'in', ids)])
		sale_order_ids = []
		for sale_order_line_id in sale_order_line_ids:
			sale_order_line = sale_order_obj.browse(cr, uid, sale_order_line_id)
			sale_order_ids.append(sale_order_line.order_id)
		ordered_sale_order_ids = sale_order_obj.search(cr, uid, sale_order_ids, order='date_order DESC')
		last_sale_order = sale_order_obj.browse(cr, uid, ordered_sale_order_ids[0])
		return datetime.strptime(last_sale_order.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
	
	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'latest_inventory_adjustment_date': fields.datetime('Latest Inventory Adjustment Date'),
		'latest_inventory_adjustment_employee_id': fields.many2one('hr.employee', 'Latest Inventory Adjustment Employee'),
		'last_sale': fields.function(_get_last_sale, string="Last Sale", type='datetime', readonly=True, store={}),
	}
	
	
# ==========================================================================================================================
