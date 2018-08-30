from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

# ==========================================================================================================================

class product_template(osv.osv):
	
	_inherit = 'product.template'
	
	# METHODS ---------------------------------------------------------------------------------------------------------------
	def _get_last_sale(self, cr, uid, ids, name, args, context=None):
		result = {}
		last_sale = ''
		for id in ids:
			cr.execute("""
			SELECT DISTINCT ON (sl.name)
			sl.name, so_line.write_date, hr.name_related
			FROM sale_order_line so_line
			LEFT JOIN hr_employee hr ON hr.id = so_line.salesman_id
			LEFT JOIN stock_location sl ON sl.id = so_line.stock_location_id
			LEFT JOIN product_product pp ON pp.product_tmpl_id = %d
			WHERE so_line.product_id = pp.id
			ORDER BY sl.name,so_line.write_date DESC
			""" % id)
			for row in cr.dictfetchall():
				last_sale = last_sale +'\n' +str(row['name'])+' || '+str(row['write_date'])+' || '+str(row['name_related']) 
			result[id] =last_sale
			return result

	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'latest_inventory_adjustment_date': fields.datetime('Latest Inventory Adjustment Date', readonly=True),
		'latest_inventory_adjustment_employee_id': fields.many2one('hr.employee', 'Latest Inventory Adjustment Employee', readonly=True),
		#'last_sale': fields.function(_get_last_sale, string="Last Sale", type='datetime', readonly=True, store=False),
		'last_sale': fields.function(_get_last_sale, string="Last Sale", type='text', readonly=True, store=False),
	}
	
	
# ==========================================================================================================================
