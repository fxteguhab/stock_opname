from datetime import datetime
from openerp.osv import osv, fields
from openerp import api
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from openerp import tools


# ==========================================================================================================================
#TEGUH@20180413 : tambah inheritance dr class  stock change product qty, spy bisa nyambung Stock Opname dari form product
class stock_change_product_qty(osv.osv_memory):
	
	_inherit = 'stock.change.product.qty'
	
	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
		'location_id': fields.many2one('stock.location', 'Inventoried Location', required=True)
	}

	
	_defaults = {
		'employee_id': lambda self, cr, uid, ctx: self.pool.get('res.users').browse(cr, uid, [uid]).id,
		'location_id': lambda self, cr, uid, ctx: self.pool.get('res.users').browse(cr, uid, uid, ctx).branch_id.default_outgoing_location_id.id
	}

	# OVERRIDES====================================================================
	def change_product_qty(self, cr, uid, ids, context=None):
		""" Changes the Product Quantity by making a Physical Inventory.
		@param self: The object pointer.
		@param cr: A database cursor
		@param uid: ID of the user currently logged in
		@param ids: List of IDs selected
		@param context: A standard dictionary
		@return:
		"""
		if context is None:
			context = {}

		inventory_obj = self.pool.get('stock.inventory')
		inventory_line_obj = self.pool.get('stock.inventory.line')

		for data in self.browse(cr, uid, ids, context=context):
			if data.new_quantity < 0:
				raise osv.except_osv(_('Warning!'), _('Quantity cannot be negative.'))
			ctx = context.copy()
			ctx['location'] = data.location_id.id
			#ctx['lot_id'] = data.lot_id.id
			ctx['employee_id'] = data.employee_id.id

			if data.product_id.id and data.lot_id.id:
				filter = 'none'
			elif data.product_id.id:
				filter = 'product'
			else:
				filter = 'none'
			inventory_id = inventory_obj.create(cr, uid, {
				'name': _('PRODUCT.SO: %s') % tools.ustr(data.product_id.name),
				'filter': filter,
				'product_id': data.product_id.id,
				'location_id': data.location_id.id,
				#'lot_id': data.lot_id.id}, context=context)
				'employee_id': data.employee_id.id},context = context)

			line_data = self._prepare_inventory_line(cr, uid, inventory_id, data, context=context)

			inventory_line_obj.create(cr, uid, line_data, context=context)
			inventory_obj.action_done(cr, uid, [inventory_id], context=context)
		return {}

# ==========================================================================================================================

class stock_inventory(osv.osv):
	
	_inherit = 'stock.inventory'
	
	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'expiration_date': fields.datetime('Expiration Date', readonly=True),
		'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
		'is_override': fields.boolean('Is Override'),
		'validity' : fields.float('Validity(%)', compute="_compute_validity", group_operator="avg",store="False"),
		'line_count':fields.float('Line(s)', compute="_compute_line", group_operator="sum",store="False"),
		'move_count':fields.float('Adjustment(s)', compute="_compute_move", group_operator="sum",store="False"),
	}
	
	_defaults = {
		'validity' : 100,
		'line_count' : 0,
		'move_count' : 0,
	}
	# COMPUTE -------------------------------------------------------------------------------------------------------------
	@api.one
	@api.depends('move_count','line_count')
	def _compute_validity(self):
		for record in self:
			if (record.line_count >0):
				record.validity = (record.line_count - record.move_count)/record.line_count * 100

	@api.one
	@api.depends('line_ids')
	def _compute_line(self):
		for record in self:
			if len(record.line_ids) > 0:
				record.line_count = len(record.line_ids)
				
	@api.one
	@api.depends('move_ids')
	def _compute_move(self):
		for record in self:
			if len(record.move_ids) > 0:
				record.move_count = len(record.move_ids)			

	# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, data, context=None):
		self._check_employee_doing_another_stock_inventory(cr, uid, data['employee_id'], 1, context=context)

		return super(stock_inventory, self).create(cr, uid, data, context)
	
	def write(self, cr, uid, ids, data, context=None):
		if data.get('employee_id', False):
			for si in self.browse(cr, uid, ids, context=context):
				if si.employee_id.id != data['employee_id']:
					self._check_employee_doing_another_stock_inventory(cr, uid, data['employee_id'], 1, context=context)
		return super(stock_inventory, self).write(cr, uid, ids, data, context)
	
	#def action_done(self, cr, uid, ids, context=None):
	#	result = super(stock_inventory, self).action_done(cr, uid, ids, context=context)
	#	product_obj = self.pool.get('product.product')
	#	inventory_line_obj = self.pool.get('stock.inventory.line')
	#	for inv in self.browse(cr, uid, ids, context=context):
	#		for line in inventory_line_obj.browse(cr, uid, inv.line_ids.ids, context=context):
	#			product_obj.write(cr, uid, line.product_id.id, {
	#				'latest_inventory_adjustment_date': datetime.now(),
	#				'latest_inventory_adjustment_employee_id': inv.employee_id and inv.employee_id.id or None,
	#			})
	#	return result
	
	def action_cancel_inventory(self, cr, uid, ids, context=None):
		""" Cancels the stock move and change inventory state to done.
		Also, make injected lines back to active.
        @return: True
        """
		stock_opname_inject_obj = self.pool.get('stock.opname.inject')
		for inv in self.browse(cr, uid, ids, context=context):
			for line in inv.line_ids:
				if line.inject_id:
					stock_opname_inject_obj.write(cr, uid, line.inject_id.id, {'active': True})
					break
			for line in inv.line_ids:
				self.write(cr, uid, [inv.id], {'line_ids': [(2,line.id)]}, context=context)
			self.pool.get('stock.move').action_cancel(cr, uid, [x.id for x in inv.move_ids], context=context)
			self.write(cr, uid, [inv.id], {'state': 'cancel'}, context=context)
		return True
	
	# METHODS ---------------------------------------------------------------------------------------------------------------
	
	def _check_employee_doing_another_stock_inventory(self, cr, uid, employee_id, limit, context=None):
		"""
		Method to check whether employee have another stock inventory in draft or in progress state or not.
		If the employee does, raise error.
		"""
		if self._is_employee_doing_another_stock_inventory(cr, uid, employee_id, limit, context=context):
			raise osv.except_osv(_('Stock Inventory Error'),
				_('Employee have another draft or in progress stock inventory.'))
	
	def _is_employee_doing_another_stock_inventory(self, cr, uid, employee_id, limit, context=None):
		cr.execute("""
			SELECT id, employee_id
			FROM stock_inventory
			WHERE (state = 'draft' OR state = 'confirm') AND employee_id = {}
		""".format(employee_id))
		other_stock_inventory_ids = cr.dictfetchall()
		if other_stock_inventory_ids and len(other_stock_inventory_ids) >= limit:
			return True
		else:
			return False
	
	# CRON ------------------------------------------------------------------------------------------------------------------
	
	def cron_autocancel_expired_stock_opname(self, cr, uid, context=None):
		"""
		Autocancel expired stock inventory based on expiration_date and today's time
		"""
		today = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
	# Pool every stock.inventory with draft or confirmed state
		stock_inventory_ids = self.search(cr, uid, [
			('state', 'in', ['draft', 'confirm']),  # draft or in progress
			('expiration_date', '<', today),
		])
		self.action_cancel_inventory(cr, uid, stock_inventory_ids, context)

# ==========================================================================================================================

class stock_inventory_line(osv.osv):
	
	_inherit = 'stock.inventory.line'
	
	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'inject_id': fields.many2one('stock.opname.inject', 'Inject'),
		'inject_by': fields.char('Request From', readonly=True),
	}

# ==========================================================================================================================

