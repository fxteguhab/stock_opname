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
		'views/stock_opname.xml',
		'views/stock_view.xml',
		'menu/stock_opname.xml',
		'cron/stock_opname.xml',
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