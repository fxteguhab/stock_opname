from datetime import datetime
from openerp.osv import osv, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

# ==========================================================================================================================

class stock_inventory(osv.osv):
	
	_inherit = 'stock.inventory'
	
	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'expiration_date': fields.datetime('Expiration Date', readonly=True),
		'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
	}
	
	# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	def action_done(self, cr, uid, ids, context=None):
		result = super(stock_inventory, self).action_done(cr, uid, ids, context=context)
		product_obj = self.pool.get('product.product')
		inventory_line_obj = self.pool.get('stock.inventory.line')
		for inv in self.browse(cr, uid, ids, context=context):
			for line in inventory_line_obj.browse(cr, uid, inv.line_ids, context=context).ids:
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
	
	# CRON ------------------------------------------------------------------------------------------------------------------
	
	def cron_autocancel_expired_stock_opname(self, cr, uid, context=None):
		"""
		Autocancel expired stock inventory based on expiration_date and today's time
		"""
		today = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
	# Pool every stock.inventory with draft or confirmed state
		stock_inventory_ids = self.search(cr, uid, [('state', 'in', ['draft', 'confirm'] )])
		for stock_inventory in self.browse(cr, uid, stock_inventory_ids):
			if today > stock_inventory.expiration_date:
			# If it is expired, cancel stock.inventory
				self.action_cancel_inventory(cr, uid, [stock_inventory.id], context)
			pass
		pass

# ==========================================================================================================================

class stock_inventory_line(osv.osv):
	
	_inherit = 'stock.inventory.line'
	
	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'inject_id': fields.many2one('stock.opname.inject', 'Inject'),
	}

# ==========================================================================================================================
