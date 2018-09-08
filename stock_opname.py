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
		'expiration_time_length': fields.float('Expiration Time(Hours)', required=True,
			help='Validity length in hours before a stock opname expires'),
		'max_item_count': fields.integer('Maximum Item Count', required=True,
			help='Maximum item type taken per stock opname'),
		'max_total_qty': fields.integer('Maximum Total Quantity', required=True,
			help='Maximum total quantity per stock opname'),
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
		'location_id': fields.many2one('stock.location', 'Location', required=True, select=True),
		'product_id': fields.many2one('product.product', 'Product', required=True),
		'priority': fields.selection([(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6')], 'Priority',
			required=True),
		'active': fields.boolean('Active'),
	}
	
	# DEFAULTS --------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'priority': 1,
		'active': True,
	}

# ---------------------------------------------------------------------------------------------------------------------------

class stock_opname_memory(osv.osv_memory):
	_name = "stock.opname.memory"
	_description = "Stock opname memory"
	
	_columns = {
		'date': fields.datetime('Date', required=True),
		#TEGUH @20180331 : Add field name
		'name': fields.char('Inventory Reference', help="Inventory Name.",required = True),
		'location_id': fields.many2one('stock.location', 'Inventoried Location', required=True),
		'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
		'rule_id': fields.many2one('stock.opname.rule', 'Rule'),
		'line_ids': fields.one2many('stock.opname.memory.line', 'stock_opname_memory_id', 'Inventories', help="Inventory Lines."),	
	}
	
	# DEFAULTS --------------------------------------------------------------------------------------------------------------
	
	def _default_rule_id(self, cr, uid, context=None):
		return self._get_rule_id(cr, uid, context)
	
	_defaults = {
		'rule_id': _default_rule_id,
		'date': lambda self, cr, uid, context: datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
		'create_uid': lambda self, cr, uid, ctx: self.pool.get('res.users').browse(cr, uid, [uid]).id,
		'name' : 'SO',
		'branch_id': lambda self, cr, uid, ctx: self.pool.get('res.users').browse(cr, uid, uid, ctx).branch_id.id,
	}
	
	# ONCHANGES -------------------------------------------------------------------------------------------------------------
	
	def onchange_location_and_employee(self, cr, uid, ids, location_id, rule_id, employee_id, context={}):
		if not context.get('is_override', False) and not rule_id:
			raise osv.except_orm(_('Generating Stock Opname Error'),
				_('There is no Stock Opname Rule marked as being used. Please select a rule to be used first.'))
		line_ids = []
		stock_location_obj = self.pool.get('stock.location')
		if location_id and employee_id:
			location = stock_location_obj.browse(cr, uid, location_id)
			line_ids = self._get_line_ids(cr, uid, location, context)
		return {'value': {'line_ids': line_ids}}
	
	# METHODS ---------------------------------------------------------------------------------------------------------------
	
	def _get_theoretical_qty(self, cr, uid, location, product, product_uom, context=None):
		uom_obj = self.pool.get("product.uom")
		quant_obj = self.pool.get("stock.quant")
	# Pool quants
		args = [
			# ('company_id', '=', line.company_id.id),
			('location_id', '=', location.id),
			# ('lot_id', '=', line.prod_lot_id.id),
			('product_id','=', product.id),
			# ('owner_id', '=', line.partner_id.id),
			# ('package_id', '=', line.package_id.id)
		]
		quant_ids = quant_obj.search(cr, uid, args, context=context)
		quants = quant_obj.browse(cr, uid, quant_ids, context=context)
	# Calculate theoretical qty
		total_qty = sum([quant.qty for quant in quants])
		if product_uom and product.uom_id.id != product_uom.id:
			total_qty = uom_obj._compute_qty_obj(cr, uid, product.uom_id, total_qty, product_uom, context=context)
		return total_qty
	
	def _get_product_ids_excluded(self, cr, uid, location_id, context=None):
		"""
		Get product ids of stock inventories in draft or confirm (in progress) state.
		This exluded product ids should not be generated in stock opname.
		"""
		cr.execute("""
			SELECT DISTINCT stock_inventory_line.product_id
			FROM
				stock_inventory_line JOIN stock_inventory
				ON stock_inventory_line.inventory_id = stock_inventory.id
			WHERE
				stock_inventory.location_id = {} AND
				(stock_inventory.state = 'draft' OR stock_inventory.state = 'confirm')
		""".format(location_id))
		excluded_products = cr.dictfetchall()
		excluded_product_ids = []
		for excluded_product in excluded_products:
			excluded_product_ids.append(excluded_product['product_id'])
		return excluded_product_ids

	def _generate_stock_opname_products(self, cr, uid, location,context={}):
	# to be overridden by inheriting models
		return []
	
	def _get_line_ids(self, cr, uid, location, context=None):
		if context is None or (context is not None and not context.get('is_override', False)):
		# Getting the rule first
			active_rule_id = self._get_rule_id(cr, uid, context)
			rule_obj = self.pool.get('stock.opname.rule')
			active_rule = rule_obj.browse(cr, uid, active_rule_id)
		
		# Process the rule with product_ids in inject if any
			line_ids = []
			product_ids_taken = self._get_product_ids_excluded(cr, uid, location.id, context=context)
			maximum_item_count = active_rule.max_item_count
			total_qty = 0
			maximum_qty = active_rule.max_total_qty
		
		# Handle SO inject
			stock_opname_inject_obj = self.pool.get('stock.opname.inject')
			inject_ids = stock_opname_inject_obj.search(cr, uid, [('active', '=', True), ('location_id', '=', location.id)], order='priority ASC, id ASC')
			first = True
			for inject in stock_opname_inject_obj.browse(cr, uid, inject_ids):
				inject_product = inject.product_id
				product_uom = inject_product.uom_id
				theoretical_qty = self._get_theoretical_qty(cr, uid, location, inject_product, product_uom, context)
			# untuk inject tidak usah cek maximum_qty, karena sifatnya wajib
			# maximum_item_count tetap diperiksa, though...
				if first:
					if maximum_item_count != 0:
						total_qty += theoretical_qty if theoretical_qty > 0 else 0
						product_ids_taken.append(inject_product.id)
						line_ids.append({
							'location_id': location.id,
							'product_id': inject_product,
							'inject_id': inject.id,
						})
						first = False
				else:
					if (maximum_qty == 0 or total_qty + theoretical_qty <= maximum_qty) and \
							inject_product.id not in product_ids_taken and len(line_ids) + 1 <= maximum_item_count:
						total_qty += theoretical_qty if theoretical_qty > 0 else 0
						product_ids_taken.append(inject_product.id)
						line_ids.append({
							'location_id': location.id,
							'product_id': inject_product,
							'inject_id': inject.id,
						})
					elif total_qty == maximum_qty or len(line_ids) == maximum_item_count:
						break
			
		# Process the rule with the algorithm
		# if there are possibilities to add more item
			if (maximum_qty == 0 or total_qty < maximum_qty) and len(line_ids) < maximum_item_count:
				try:
					#exec active_rule.algorithm
					# noinspection PyUnresolvedReferences
					#rule_products = generate_stock_opname_products(self, cr, uid)
					rule_products = self._generate_stock_opname_products(cr, uid, location.id,context)
				except Exception as ex:
					raise osv.except_orm(_('Stock Opname Generate Error'),
						_('Syntax or other error(s) in the code of selected Stock Opname Rule.'))
				product_obj = self.pool.get('product.product')
				for rule_product in rule_products:
					product = product_obj.browse(cr, uid, [rule_product['product_id']])
					product_uom = product.uom_id
					theoretical_qty = self._get_theoretical_qty(cr, uid, location, product, product_uom, context)
					if (maximum_qty == 0 or total_qty + theoretical_qty <= maximum_qty) and \
							product.id not in product_ids_taken and len(line_ids)+1 <= maximum_item_count:
						total_qty += theoretical_qty if theoretical_qty > 0 else 0
						product_ids_taken.append(product.id)
						line_ids.append({
							'location_id': location.id,
							'product_id': product,
						})
					elif (maximum_qty != 0 and total_qty == maximum_qty) or len(line_ids) == maximum_item_count:
						break
			return line_ids
	
	def _get_rule_id(self, cr, uid, context={}):
		context = context and context or {}
		if not context.get('is_override', False):
			rule_obj = self.pool.get('stock.opname.rule')
			active_rule_ids = rule_obj.search(cr, uid, [('is_used', '=', True)])
			if len(active_rule_ids) == 0:
				return None
			return active_rule_ids[0]
		else:
			return None
	
	# ACTIONS ---------------------------------------------------------------------------------------------------------------
	
	def action_generate_stock_opname(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		is_override =context.get('is_override', False)
		so_name = ''
		stock_opname_obj = self.pool.get('stock.inventory')
		stock_opname_inject_obj = self.pool.get('stock.opname.inject')
		stock_opname_memory_line_obj = self.pool.get('stock.opname.memory.line')
		today = datetime.now()
		stock_inventory_ids = []
		for memory in self.browse(cr, uid, ids):
			so_name = memory.name
			if not is_override and not memory.rule_id:
				raise osv.except_osv(_('Stock Opname Error'),
					_('There is no Stock Opname Rule marked as being used. Please select a rule to be used first.'))
			memory_line = stock_opname_memory_line_obj.browse(cr, uid, memory.line_ids.ids)
			line_ids = []
			for line in memory_line:
				if line.product_id.type != 'product':
					raise osv.except_osv(_('Invalid Product Type'), _('One or more products is not a stockable product.'))
				vals = {
					# 'location_id': line.location_id.id,
					'location_id': memory.location_id.id,
					'product_id': line.product_id.id,
					'inject_id': line.inject_id and line.inject_id.id or None,
				}
				if is_override:
					so_name = 'OVR.'+memory.name
					vals.update({
						'product_uom_id': line.product_uom_id.id,
						'product_qty': line.product_qty,
					})
				line_ids.append((0, False, vals))
				if line.inject_id:
					stock_opname_inject_obj.write(cr, uid, [line.inject_id.id], {"active": False}, context)
			
			memory_hour = int(memory.rule_id.expiration_time_length)
			memory_minute = (memory.rule_id.expiration_time_length - memory_hour) * 60
			stock_opname = {
				#TEGUH@20180331 : ubah reference SO + custom name
				'name': '%s - %s %s' % (so_name,memory.employee_id.name, (today + timedelta(hours=7)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
				#'name': '%s - %s %s' % (memory.name,memory.employee_id.name, (today + timedelta(hours=7)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
				#'name': 'SO @%s - %s (%s) - %s Row(s)' % (memory.location_id.name,memory.employee_id.name, (today + timedelta(hours=7)).strftime(DEFAULT_SERVER_DATETIME_FORMAT),len(memory.line_ids)),
				'state': 'confirm', # if memory.rule_id.id else 'done',
				'date': memory.date,
				'expiration_date': (
					datetime.strptime(memory.date, DEFAULT_SERVER_DATETIME_FORMAT) +
					timedelta(hours=memory_hour) +
					timedelta(minutes=memory_minute)).strftime(DEFAULT_SERVER_DATETIME_FORMAT),
				'employee_id': memory.employee_id.id if memory.employee_id else None,
				'location_id': memory.location_id.id,
				'is_override': is_override,
				'line_ids': line_ids,
				'branch_id': memory.branch_id.id,
			}
			stock_inventory_ids.append(stock_opname_obj.create(cr, uid, stock_opname, context))
	# kalau begitu di-create state langsung dijadikan confirm, maka stock movenya tidak dicatat alias
	# stock opnamenya tidak ngefek ke stock product ybs. Maka dari itu di titik ini dipanggillah action yang buat
	# men-done kan stock opname yang baru saja di-create di atas, khusus untuk override
		if is_override:
			stock_opname_obj.action_done(cr, uid, stock_inventory_ids, context=context)
		action = {"type": "ir.actions.act_window", "res_model": "stock.inventory"}
		if len(stock_inventory_ids) == 1:
			action.update({"views": [[False, "form"]], "res_id": stock_inventory_ids[0]})
		else:
			action.update({"views": [[False, "tree"], [False, "form"]], "domain": [("id", "in", stock_inventory_ids)]})
		return action

# ---------------------------------------------------------------------------------------------------------------------------

class stock_opname_memory_line(osv.osv_memory):
	_name = "stock.opname.memory.line"
	_description = "Stock opname memory line"
	
	_columns = {
		'stock_opname_memory_id': fields.many2one('stock.opname.memory', 'Stock Opname Memory'),
		'product_id': fields.many2one('product.product', 'Product', required=True),
		'location_id': fields.many2one('stock.location', 'Location', required=True),
		'product_uom_id': fields.many2one('product.uom', 'Product Unit of Measure', required=True),
		'product_qty': fields.float('Checked Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
		'inject_id': fields.many2one('stock.opname.inject', 'Inject'),
	}
	
	_defaults = {
		'product_qty': 0,
		'product_uom_id': lambda self, cr, uid, ctx=None: self.pool['ir.model.data'].get_object_reference(cr, uid,
			'product', 'product_uom_unit')[1],
		'inject_id': False,
	}
	
# ---------------------------------------------------------------------------------------------------------------------------
