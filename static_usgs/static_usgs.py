import os, sys, time

nprocs=1
compatible_environments = ['kuusi','cheyenne']
dependencies=['compile_gnu']

def setup(tparams):

	files = ['x1.40962.grid.nc', 'WPS_GEOG']
	return {'files':files, 'modset':'gnu'}

def test(tparams, res):

	env = tparams['env']
	utils=env.get('utils')	

	res.set('completed', False)
	res.set('name', 'Static interpolation (USGS)')

	if not env:
		print('No environment object passed to Example test, quitting')
		return res
	if not utils:
		print('No utils module in test environment, quitting Example test')
		return res

	if not env.contains_modset('gnu'):
		res.set('err_msg', 'In Static/USGS test(), no modset for gnu')
		return res

	e = env.mod_reset('gnu', {})
	if e:
		res.set('err_msg', "In Static/USGS test(), error resetting to the modset 'gnu'.")
		res.set('err_code', e)
		return res

	if not all(tparams['found_files']):
		not_found = [tparams['files'][i] for i in range(len(tparams['files'])) if not tparams['found_files'][i]]
		not_found_string = " ".join(not_found)
		res.set('err_msg', 'In Static/USGS test(), some required files were not found in the standard library: '+not_found_string)
		return res

	template_dir = tparams['SMARTS_dir']+'/static_usgs'
	sandbox_dir = tparams['test_dir']
	exe_dir = tparams['test_dir']+'/../compile_gnu'

	os.system('ln -s '+exe_dir+'/init_atmosphere_model .')
	utils.linkAllFiles(template_dir+'/inputs', './')

	myRun = utils.modelRun('./', 'init_atmosphere_model', 1, env, add_lsfoptions={'-W':'1:30', '-e':'run.err', '-o':'run.out'}, add_pbsoptions={'-l walltime=01:30:00':''})
	myRun.runModelNonblocking()

	while not (myRun.is_finished()):
		time.sleep(1)
		pass

	myRun.terminate()

	err = myRun.get_result()
	print('Error code is '+repr(err.get('err_code')))

	res.set('err_code', err.get('err_code'))

	res.set('err_msg', 'Static interplation (USGS) passed')

	res.set('completed', True)
	
	return
