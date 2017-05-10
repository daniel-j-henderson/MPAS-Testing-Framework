import os, sys, time

nprocs=1
compatible_environments = ['kuusi']
dependencies=['compile_gnu']

def setup(tparams):

	files = ['x1.40962.grid.nc', 'WPS_GEOG']
	return {'files':files, 'modset':'gnu'}

def test(tparams, res):

	env = tparams['env']
	utils=env.get('utils')	

	res.set('completed', False)
	res.set('name', 'Static interpolation (MODIS)')

	if not env:
		print('No environment object passed to Example test, quitting')
		return res
	if not utils:
		print('No utils module in test environment, quitting Example test')
		return res

	if not env.contains_modset('gnu'):
		res.set('err_msg', 'In Static/MODIS test(), no modset for gnu')
		return res

	e = env.mod_reset('gnu', {})
	if e:
		res.set('err_msg', "In Static/MODIS test(), error resetting to the modset 'gnu'.")
		res.set('err_code', e)
		return res
	

	template_dir = tparams['SMARTS_dir']+'/static_modis'
	sandbox_dir = tparams['test_dir']
	exe_dir = tparams['test_dir']+'/../compile_gnu'

	os.system('ln -s '+exe_dir+'/init_atmosphere_model .')
	utils.linkAllFiles(template_dir+'/inputs', './')

	#(completed, err_code) = runAtmosphereModel(dir, exename, ntasks, env, additional_lsf_options, additional_pbs_options)
	#completed: boolean, signifies whether the function runAtmosphereModel completed or returned early
	#err_code: the return code from the model executable
	#Note: this function blocks until the model run is complete

	#If your test comes with files like namelists and such, link them in this way
	myRun = utils.modelRun('./', 'init_atmosphere_model', 1, env, add_lsfoptions={'-W':'1:30', '-e':'run.err', '-o':'run.out'})
	myRun.runModelNonblocking() #returns immediately, model run happening in background

	while not (myRun.is_finished()):
		time.sleep(1)
		pass

	myRun.terminate()

	e = myRun.get_result()

	res.set('err_code', e.get('err_code'))

	res.set('err_msg', 'Static interplation (MODIS) passed')

	res.set('completed', True)
	
	return
