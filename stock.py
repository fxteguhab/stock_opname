from datetime import datetime
from openerp.osv import osv, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _

# ==========================================================================================================================

class stock_inventory(osv.osv):
	
	_inherit = 'stock.inventory'
	
	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'expiration_date': fields.datetime('Expiration Date', readonly=True),
		'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
		'is_override': fields.boolean('Is Override'),
	}
	
	# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, data, context=None):
		self._check_employee_doing_another_stock_inventory(cr, uid, data['employee_id'], context=context)
		return super(stock_inventory, self).create(cr, uid, data, context)
	
	def write(self, cr, uid, ids, data, context=None):
		if data.get('employee_id', False):
			self._check_employee_doing_another_stock_inventory(cr, uid, data['employee_id'], context=context)
		else:
			for stock_inventory in self.browse(cr, uid, ids, context=context):
				self._check_employee_doing_another_stock_inventory(cr, uid, stock_inventory.employee_id.id, context=context)
		return super(stock_inventory, self).write(cr, uid, ids, data, context)
	
	def action_done(self, cr, uid, ids, context=None):
		result = super(stock_inventory, self).action_done(cr, uid, ids, context=context)
		product_obj = self.pool.get('product.product')
		inventory_line_obj = self.pool.get('stock.inventory.line')
		for inv in self.browse(cr, uid, ids, context=context):
			for line in inventory_line_obj.browse(cr, uid, inv.line_ids.ids, context=context):
				product_obj.write(cr, uid, line.product_id.id, {
					'latest_inventory_adjustment_date': datetime.now(),
					'latest_inventory_adjustment_employee_id': inv.employee_id and inv.employee_id.id or None,
				})
		return result
	
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
	
	def _check_employee_doing_another_stock_inventory(self, cr, uid, employee_id, context=None):
		"""
		Method to check whether employee have another stock inventory in draft or in progress state or not.
		If the employee does, raise error.
		"""
		if self._is_employee_doing_another_stock_inventory(cr, uid, employee_id, context=context):
			raise osv.except_osv(_('Stock Inventory Error'),
				_('Employee have another draft or in progress stock inventory.'))
	
	def _is_employee_doing_another_stock_inventory(self, cr, uid, employee_id, context=None):
		cr.execute("""
			SELECT id, employee_id
			FROM stock_inventory
			WHERE (state = 'draft' OR state = 'confirm') AND employee_id = {}
		""".format(employee_id))
		other_stock_inventory_ids = cr.dictfetchall()
		if other_stock_inventory_ids and len(other_stock_inventory_ids):
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
	}

# ==========================================================================================================================
