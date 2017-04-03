import os, sys, time

nprocs = 1
compatible_environments = ['kuusi']

def setup(tparams):

	return {'modset':'pgi'}

def test(tparams, res):

	env = tparams['env']
	utils=env.get('utils')	

	res.set('completed', False)
	res.set('name', 'Build / PGI')

	if not env:
		print('No environment object passed to Build/PGI test, quitting')
		return res
	if not utils:
		print('No utils module in test environment, quitting Build/PGI test')
		return res

	if not env.contains_modset('pgi'):
		res.set('err_msg', 'In Build/PGI test(), no modset for pgi')
		return res

	e = env.mod_reset('pgi', {})
	if e:
		res.set('err_msg', "In Build/PGI test(), error resetting to the modset 'pgi'.")
		res.set('err_code', e)
		return res
	

	src_dir = tparams['src_dir']

	os.system('cp -R '+src_dir+'/src .')
	os.system('cp -R '+src_dir+'/Makefile .')
	os.system('make clean CORE=atmosphere > clean.log 2>&1')
	os.system('time make pgi CORE=atmosphere > make.log 2>&1')
	if os.path.isfile('atmosphere_model') and os.path.getsize('atmosphere_model') > 1000000:
		res.set('err_msg', 'PGI build test passed')
		res.set('err_code', 0)
		res.set('success', True)
	else:
		res.set('err_msg', 'PGI build test failed')
		res.set('err_code', 1)
		res.set('success', False)


	res.set('completed', True)
	
	return
