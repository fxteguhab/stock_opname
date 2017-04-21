from openerp.osv import fields, osv


class stock_opname_rule(osv.osv):
	_name = "stock.opname.rule"
	_description = "Stock opname rule"
	
	_columns = {
		'name': fields.char('Location Name', required=True, translate=True),
	}

	# OVERRIDES -------------------------------------------------------------------------------------------------------------



# ---------------------------------------------------------------------------------------------------------------------------


class stock_opname_inject(osv.osv):
	_name = "stock.opname.inject"
	_description = "Stock opname inject"
	
	_columns = {
		'product_id': fields.many2one('product.product', 'Product', required=True),
		'priority': fields.selection([(1, '1'), (2, '2')], 'Priority'),
	}
	
	# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	
	
# ---------------------------------------------------------------------------------------------------------------------------


class stock_opname_memory(osv.osv):
	_name = "stock.opname.memory"
	_description = "Stock opname memory"
	
	_columns = {
		'date': fields.datetime('Date', required=True),
		'location_id': fields.many2one('stock.location', 'Inventoried Location'),
		# TODO Onchange: ubah location_id di line domainnya jadi yang parent_id nya location_id ini
		'employee_id': fields.many2one('hr.employee', 'Employee'),
		'line_ids': fields.one2many('stock.inventory.line', 'inventory_id', 'Inventories', help="Inventory Lines."),
	}
	
	# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	
	
# ---------------------------------------------------------------------------------------------------------------------------


class stock_opname_memory_line(osv.osv):
	_name = "stock.opname.memory.line"
	_description = "Stock opname memory line"
	
	_columns = {
		'product_id': fields.many2one('product.product', 'Product', required=True),
		'location_id': fields.many2one('stock.location', 'Location'), # TODO Domain
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