import os, sys, time

nprocs = 1
compatible_environments = ['kuusi']

def setup(tparams):

	return {'modset':'intel'}

def test(tparams, res):

	env = tparams['env']
	utils=env.get('utils')	

	res.set('completed', False)
	res.set('name', 'Build / Intel')

	if not env:
		print('No environment object passed to Build/Intel test, quitting')
		return res
	if not utils:
		print('No utils module in test environment, quitting Build/Intel test')
		return res

	if not env.contains_modset('intel'):
		res.set('err_msg', 'In Build/Intel test(), no modset for intel')
		return res

	e = env.mod_reset('intel', {})
	if e:
		res.set('err_msg', "In Build/Intel test(), error resetting to the modset 'intel'.")
		res.set('err_code', e)
		return res
	

	src_dir = tparams['src_dir']

	os.system('cp -R '+src_dir+'/src .')
	os.system('cp -R '+src_dir+'/Makefile .')
	os.system('make clean CORE=atmosphere > clean.log 2>&1')
	os.system('time make ifort CORE=atmosphere > make.log 2>&1')
	if os.path.isfile('atmosphere_model') and os.path.getsize('atmosphere_model') > 1000000:
		res.set('err_msg', 'Intel build test passed')
		res.set('err_code', 0)
		res.set('success', True)
	else:
		res.set('err_msg', 'Intel build test failed')
		res.set('err_code', 1)
		res.set('success', False)


	res.set('completed', True)
	
	return
