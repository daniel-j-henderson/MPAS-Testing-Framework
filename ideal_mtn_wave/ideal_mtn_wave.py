import os, sys, time

nprocs=1
compatible_environments = ['kuusi','cheyenne']
dependencies=['compile_gnu_mtn_wave']

def setup(tparams):

	files = ['mtn_wave_grid.nc']
	return {'files':files, 'modset':'gnu'}

def test(tparams, res):

	env = tparams['env']
	utils=env.get('utils')	

	res.set('completed', False)
	res.set('name', 'Mountain Wave')

	if not env:
		print('No environment object passed to Mountain Wave test, quitting')
		return res
	if not utils:
		print('No utils module in test environment, quitting Mountain Wave test')
		return res

	if not env.contains_modset('gnu'):
		res.set('err_msg', 'In Mountain Wave test(), no modset for gnu')
		return res

	e = env.mod_reset('gnu', {})
	if e:
		res.set('err_msg', "In Mountain Wave test(), error resetting to the modset 'gnu'.")
		res.set('err_code', e)
		return res

	if not all(tparams['found_files']):
		not_found = [tparams['files'][i] for i in range(len(tparams['files'])) if not tparams['found_files'][i]]
		not_found_string = " ".join(not_found)
		res.set('err_msg', 'In Mountain Wave test(), some required files were not found in the standard library: '+not_found_string)
		return res

	template_dir = tparams['SMARTS_dir']+'/ideal_mtn_wave'
	sandbox_dir = tparams['test_dir']
	exe_dir = tparams['test_dir']+'/../compile_gnu_mtn_wave'

	os.system('ln -s '+exe_dir+'/init_atmosphere_model .')
	os.system('ln -s '+exe_dir+'/atmosphere_model .')

	utils.linkAllFiles(template_dir+'/inputs', './')
	init = utils.modelRun('./', 'init_atmosphere_model', 1, env, add_lsfoptions={'-W':'0:30', '-e':'run.err', '-o':'run.out'}, add_pbsoptions={'-l walltime=00:30:00':''})
	init.runModelBlocking()
	mtn_wave = utils.modelRun('./', 'atmosphere_model', 1, env, add_lsfoptions={'-W':'0:30', '-e':'run.err', '-o':'run.out'}, add_pbsoptions={'-l walltime=00:30:00':''})
	mtn_wave.runModelBlocking()

	e_init = init.get_result()
	e_mtn_wave = mtn_wave.get_result()
        err_code = e_init.get('err_code')+e_mtn_wave.get('err_code')
        err_code = 0

	res.set('err_code', err_code)
	if err_code == 0:
		os.system('ncl mtn_wave_w.ncl')
		os.system('mkdir figures')
		os.system('mv mtn_wave_w.pdf figures')
		res.set('figures_directory', sandbox_dir+'/figures')
		res.set('success', True)
		res.set('err_msg', 'Mountain Wave test passed')
	else:
		res.set('success', False)
		res.set('err_msg', 'Mountain Wave test failed')

	res.set('completed', True)
	
	return
