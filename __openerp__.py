{
	'name': 'Stock Opname',
	'version': '1.0',
	'author': 'Christyan Juniady and Associates',
	'maintainer': 'Christyan Juniady and Associates',
	'category': 'General',
	'sequence': 21,
	'website': 'http://www.chjs.biz',
	'summary': '',
	'description': """
		Stock Opname
	""",
	'author': 'Christyan Juniady and Associates',
	'images': [
	],
	'depends': ['base','board','web','stock'],
	'data': [
		'views/stock_opname_view.xml',
		'views/stock_view.xml',
		'views/product_view.xml',
		'menu/stock_opname_menu.xml',
		'cron/stock_opname_cron.xml',
	],
	'demo': [
	],
	'test': [
	],
	'installable': True,
	'application': True,
	'auto_install': False,
	'qweb': [
		'static/src/xml/ipc_idss.xml'
	 ],
}