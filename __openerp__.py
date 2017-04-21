{
	'name': 'IPC IDSS',
	'version': '1.0',
	'author': 'Christyan Juniady and Associates',
	'maintainer': 'Christyan Juniady and Associates',
	'category': 'General',
	'sequence': 21,
	'website': 'http://www.chjs.biz',
	'summary': '',
	'description': """
		Custom implementation for Indonesia Port Corporation
	""",
	'author': 'Christyan Juniady and Associates',
	'images': [
	],
	'depends': ['base','board','web','document','web_tree_image'],
	'data': [
		'views/stock_opname.xml',
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