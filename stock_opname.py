from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class stock_opname_rule(osv.osv):
	_name = "stock.opname.rule"
	_description = "Stock opname rule"
	
	_columns = {
		'name': fields.char('Rule Name', required=True, translate=True),
		'is_used': fields.boolean('Is Used'),
		'algorithm': fields.text('Algorithm', required=True),
		'expiration_time_length': fields.float('Expiration Time Length', required=True,
			help='Validity length in hours before a stock opname expires'),
		'max_item_count': fields.integer('Maximum Item Count', required=True,
			help='Maximum item type taken per stock opname'),
		'max_total_qty': fields.integer('Maximum Total Quantity', required=True,
			help='Maximum total quantity per stock opname'),
	}
	
	# DEFAULTS --------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'is_used': False,
		'algorithm': "def generate_stock_opname_products(supplier_id):\n	return []",
		'max_item_count': 1,
	}
	
	# CONSTRAINT ------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('const_expiration_time_length', 'CHECK(expiration_time_length >= 0)', _('Expiration time length cannot be less than zero.')),
		('const_max_item_count', 'CHECK(max_item_count >= 0)', _('Maximum item count cannot be less than zero.')),
		('const_max_total_qty', 'CHECK(max_total_qty >= 0)', _('Maximum total quantity cannot be less than zero.')),
	]

	# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, data, context=None):
		new_algorithm = super(stock_opname_rule, self).create(cr, uid, data, context)
		algorithm_ids = self.search(cr, uid, [('id', '!=', new_algorithm)])
		if len(algorithm_ids) == 0:
			if data['is_used'] == False:
				self.write(cr, uid, [new_algorithm], {'is_used': True}, context)
		else:
			if data['is_used'] == True:
				for algorithm in self.browse(cr, uid, algorithm_ids):
					if algorithm.is_used == True:
						self.write(cr, uid, [algorithm.id], {'is_used': False}, context)
						break
		return new_algorithm
	
	def write(self, cr, uid, ids, data, context=None):
		result = super(stock_opname_rule, self).write(cr, uid, ids, data, context)
		if 'is_used' in data and data['is_used'] == True:
			algorithm_ids = self.search(cr, uid, [('id', '!=', ids)])
			for algorithm_id in algorithm_ids:
				algorithm = self.browse(cr, uid, [algorithm_id])
				if algorithm.is_used == True:
					self.write(cr, uid, [algorithm_id], {'is_used': False}, context)
		return result
	
	def unlink(self, cr, uid, ids, context=None):
		result = super(stock_opname_rule, self).unlink(cr, uid, ids, context)
		algorithm_ids = self.search(cr, uid, [])
		if len(algorithm_ids) == 1:
			for algorithm in self.browse(cr, uid, algorithm_ids):
				if algorithm.is_used == False:
					self.write(cr, uid, [algorithm.id], {'is_used': True}, context)
		return result


# ---------------------------------------------------------------------------------------------------------------------------


class stock_opname_inject(osv.osv):
	_name = "stock.opname.inject"
	_description = "Stock opname inject"
	
	_columns = {
		'product_id': fields.many2one('product.product', 'Product', required=True),
		'priority': fields.selection([(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6')], 'Priority',
			required=True),
	}
	
	# DEFAULTS --------------------------------------------------------------------------------------------------------------
	_defaults = {
		'priority': 1,
	}
	
	# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	
# ---------------------------------------------------------------------------------------------------------------------------


class stock_opname_memory(osv.osv_memory):
	_name = "stock.opname.memory"
	_description = "Stock opname memory"
	
	_columns = {
		'date': fields.datetime('Date', required=True),
		'location_id': fields.many2one('stock.location', 'Inventoried Location'),
		# TODO Onchange: ubah location_id di line domainnya jadi yang parent_id nya location_id ini
		'employee_id': fields.many2one('hr.employee', 'Employee'),
		'line_ids': fields.one2many('stock.opname.memory.line', 'stock_opname_id', 'Inventories', help="Inventory Lines."),
	}
	
	# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	
	
# ---------------------------------------------------------------------------------------------------------------------------


class stock_opname_memory_line(osv.osv_memory):
	_name = "stock.opname.memory.line"
	_description = "Stock opname memory line"
	
	_columns = {
		'stock_opname_id': fields.many2one('stock.opname.memory.line', 'Stock Opname'),
		'product_id': fields.many2one('product.product', 'Product', required=True),
		'location_id': fields.many2one('stock.location', 'Location'),
		'product_uom_id': fields.many2one('product.uom', 'Product Unit of Measure', required=True),
		'product_qty': fields.float('Real Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
	}
	
	_defaults = {
		'product_qty': 0,
		'product_uom_id': lambda self, cr, uid, ctx=None: self.pool['ir.model.data'].get_object_reference(cr, uid,
			'product', 'product_uom_unit')[1]
	}
	
	# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	
	
# ---------------------------------------------------------------------------------------------------------------------------