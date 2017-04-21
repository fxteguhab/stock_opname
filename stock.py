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

	# CRON ------------------------------------------------------------------------------------------------------------------
	
	def debug_cron(self, cr, uid, ids, context=None):
		self.cron_autocancel_expired_stock_opname(cr, uid, context)
	
	def cron_autocancel_expired_stock_opname(self, cr, uid, context=None):
		"""
		Autocancel expired stock inventory based on expiration_date and today's time
		"""
		today = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
	# Pool every stock.inventory with draft or confirmed state
		stock_inventory_ids = self.search(cr, uid, [('state', 'in', 'draft, confirm')])
		for stock_inventory in self.browse(cr, uid, stock_inventory_ids):
		# If it is expired, cancel stock.inventory
			if stock_inventory.expiration_date > today:
				stock_inventory.state.action_cancel_inventory(cr, uid, [stock_inventory.id], context)
			pass
		pass

# ==========================================================================================================================

class stock_inventory_line(osv.osv):
	
	_inherit = 'stock.inventory.line'
	
	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'is_inject': fields.boolean('Is Inject?'),
	}

# ==========================================================================================================================
