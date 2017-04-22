from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from datetime import datetime, timedelta


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
		'algorithm': "def generate_stock_opname_products():\n	return [{'product_id':1, 'product_qty':10}]",
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
		new_rule = super(stock_opname_rule, self).create(cr, uid, data, context)
		rule_ids = self.search(cr, uid, [('id', '!=', new_rule)])
		if len(rule_ids) == 0:
			if data['is_used'] == False:
				self.write(cr, uid, [new_rule], {'is_used': True}, context)
		else:
			if data['is_used'] == True:
				for rule in self.browse(cr, uid, rule_ids):
					if rule.is_used == True:
						self.write(cr, uid, [rule.id], {'is_used': False}, context)
						break
		return new_rule
	
	def write(self, cr, uid, ids, data, context=None):
		result = super(stock_opname_rule, self).write(cr, uid, ids, data, context)
		if 'is_used' in data and data['is_used'] == True:
			rule_ids = self.search(cr, uid, [('id', '!=', ids)])
			for rule_id in rule_ids:
				rule = self.browse(cr, uid, [rule_id])
				if rule.is_used == True:
					self.write(cr, uid, [rule_id], {'is_used': False}, context)
		return result
	
	def unlink(self, cr, uid, ids, context=None):
		result = super(stock_opname_rule, self).unlink(cr, uid, ids, context)
		rule_ids = self.search(cr, uid, [])
		if len(rule_ids) == 1:
			for rule in self.browse(cr, uid, rule_ids):
				if rule.is_used == False:
					self.write(cr, uid, [rule.id], {'is_used': True}, context)
		return result


# ---------------------------------------------------------------------------------------------------------------------------


class stock_opname_inject(osv.osv):
	_name = "stock.opname.inject"
	_description = "Stock opname inject"
	
	_columns = {
		'product_id': fields.many2one('product.product', 'Product', required=True),
		'product_qty': fields.float('Product Quantity', required=True,
			digits_compute=dp.get_precision('Product Unit of Measure')),
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
		'location_id': fields.many2one('stock.location', 'Inventoried Location', required=True),
		'employee_id': fields.many2one('hr.employee', 'Employee'),
		'rule_id': fields.many2one('stock.opname.rule', 'Rule'),
		'line_ids': fields.one2many('stock.opname.memory.line', 'stock_opname_memory_id', 'Inventories', help="Inventory Lines."),
	}
	
	# DEFAULTS --------------------------------------------------------------------------------------------------------------
	
	def _get_line_ids(self, cr, uid, context=None):
		if context is None or (context is not None and not context.get('is_override', False)):
		# Getting the rule first
			active_rule_id = self._get_rule_id(cr, uid, context)
			rule_obj = self.pool.get('stock.opname.rule')
			active_rule = rule_obj.browse(cr, uid, active_rule_id)
			try:
				exec active_rule.algorithm
				# noinspection PyUnresolvedReferences
				products_from_rule = generate_stock_opname_products()
			except:
				raise osv.except_orm(_('Generating Stock Opname Error'),
					_('Syntax or other error(s) in the code of selected Stock Opname Rule.'))
			
		# Process the rule with product_ids in inject if any
			line_ids = []
			product_ids_taken = []
			maximum_item_count = active_rule.max_item_count
			total_qty = 0
			maximum_qty = active_rule.max_total_qty
			
			line_ids_from_inject = []
			stock_opname_inject_obj = self.pool.get('stock.opname.inject')
			product_ids_from_inject = stock_opname_inject_obj.search(cr, uid, [], order='priority ASC')
			for product_id in product_ids_from_inject:
				product_inject = stock_opname_inject_obj.browse(cr, uid, product_id)
				if (maximum_qty == 0 or total_qty+product_inject.product_qty <= maximum_qty) and \
				product_inject.product_id not in product_ids_taken and len(product_ids_taken)+1 <= maximum_item_count:
					total_qty += product_inject.product_qty
					product_ids_taken.append(product_inject.product_id)
					line_ids_from_inject.append({'product_id': product_inject.product_id,
												'product_qty': product_inject.product_qty,
												'is_inject': True, })
				elif total_qty == maximum_qty or len(product_ids_taken) == maximum_item_count:
					break
			line_ids.extend(line_ids_from_inject)
			
		# Process the rule with the algorithm
			line_ids_from_rule = []
			for product in products_from_rule:
				if (maximum_qty == 0 or total_qty+product['product_qty'] <= maximum_qty) and \
				product['product_id'] not in product_ids_taken and len(product_ids_taken)+1 <= maximum_item_count:
					total_qty += product['product_qty']
					product_ids_taken.append(product['product_id'])
					line_ids_from_rule.append({'product_id': product['product_id'],
												'product_qty': product['product_qty'],
												'is_inject': False, })
				elif total_qty == maximum_qty or len(product_ids_taken) == maximum_item_count:
					break
			line_ids.extend(line_ids_from_rule)
			return line_ids
	
	def _get_rule_id(self, cr, uid, context=None):
		if context is None or (context is not None and not context.get('is_override', False)):
			rule_obj = self.pool.get('stock.opname.rule')
			active_rule_ids = rule_obj.search(cr, uid, [('is_used', '=', True)])
			if len(active_rule_ids) == 0:
				raise osv.except_orm(_('Generating Stock Opname Error'),
					_('There is no Stock Opname Rule marked as being used.'))
			return active_rule_ids[0]
		else:
			return 0
	
	_defaults = {
		'rule_id': _get_rule_id,
		'line_ids': _get_line_ids,
	}
	
	# ONCHANGE --------------------------------------------------------------------------------------------------------------
	
	def onchange_location_id(self, cr, uid, ids):
		return {'value': {'line_ids': []}}
	
	# METHOD ----------------------------------------------------------------------------------------------------------------
	
	def action_generate_stock_opname(self, cr, uid, ids, context=None):
		stock_opname_obj = self.pool.get('stock.inventory')
		stock_opname_memory_line_obj = self.pool.get('stock.opname.memory.line')
		today = datetime.now()
		for memory in self.browse(cr, uid, ids):
			memory_line_id = stock_opname_memory_line_obj.browse(cr, uid, memory.line_ids.ids)
			line_ids = []
			for line in memory_line_id:
				line_ids.append((0, False, {
					'location_id': line.location_id.id,
					'product_id': line.product_id.id,
					'product_uom_id': line.product_uom_id.id,
					'product_qty': line.product_qty,
					'is_inject': line.is_inject,
				}))
			
			memory_hour = int(memory.rule_id.expiration_time_length)
			memory_minute = (memory.rule_id.expiration_time_length - memory_hour) * 60
			stock_opname = {
				'name': 'SO ' + today.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
				'state': 'confirm' if memory.rule_id.id else 'done',
				'date': memory.date,
				'expiration_date': (datetime.strptime(memory.date, DEFAULT_SERVER_DATETIME_FORMAT)
									+ timedelta(hours=memory_hour) + timedelta(minutes=memory_minute))
					.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
				'employee_id': memory.employee_id.id,
				'location_id': memory.location_id.id,
				'line_ids': line_ids,
			}
			stock_opname_obj.create(cr, uid, stock_opname, context)

# ---------------------------------------------------------------------------------------------------------------------------


class stock_opname_memory_line(osv.osv_memory):
	_name = "stock.opname.memory.line"
	_description = "Stock opname memory line"
	
	_columns = {
		'stock_opname_memory_id': fields.many2one('stock.opname.memory', 'Stock Opname Memory'),
		'product_id': fields.many2one('product.product', 'Product', required=True),
		'location_id': fields.many2one('stock.location', 'Location', required=True),
		'product_uom_id': fields.many2one('product.uom', 'Product Unit of Measure', required=True),
		'product_qty': fields.float('Real Quantity', required=True,
			digits_compute=dp.get_precision('Product Unit of Measure')),
		'is_inject': fields.boolean('Is Inject?'),
	}
	
	_defaults = {
		'product_qty': 0,
		'product_uom_id': lambda self, cr, uid, ctx=None: self.pool['ir.model.data'].get_object_reference(cr, uid,
			'product', 'product_uom_unit')[1]
	}
	
	# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	
	
# ---------------------------------------------------------------------------------------------------------------------------