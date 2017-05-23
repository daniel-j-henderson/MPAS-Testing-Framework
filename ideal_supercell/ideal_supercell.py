import os, sys, time

nprocs=12
compatible_environments = ['kuusi']
dependencies=['compile_gnu']

def setup(tparams):

	files = ['supercell_grid.nc', 'supercell.graph.info.part.12']
	return {'files':files, 'modset':'gnu'}

def test(tparams, res):

	env = tparams['env']
	utils=env.get('utils')	

	res.set('completed', False)
	res.set('name', 'Supercell')

	if not env:
		print('No environment object passed to Supercell test, quitting')
		return res
	if not utils:
		print('No utils module in test environment, quitting Supercell test')
		return res

	if not env.contains_modset('gnu'):
		res.set('err_msg', 'In Supercell test(), no modset for gnu')
		return res

	e = env.mod_reset('gnu', {})
	if e:
		res.set('err_msg', "In Supercell test(), error resetting to the modset 'gnu'.")
		res.set('err_code', e)
		return res

	if not all(tparams['found_files']):
		not_found = [tparams['files'][i] for i in range(len(tparams['files'])) if not tparams['found_files'][i]]
		not_found_string = " ".join(not_found)
		res.set('err_msg', 'In Supercell test(), some required files were not found in the standard library: '+not_found_string)
		return res

	template_dir = tparams['SMARTS_dir']+'/ideal_supercell'
	sandbox_dir = tparams['test_dir']
	exe_dir = tparams['test_dir']+'/../compile_gnu'

	os.system('ln -s '+exe_dir+'/init_atmosphere_model .')
	os.system('ln -s '+exe_dir+'/atmosphere_model .')

	utils.linkAllFiles(template_dir+'/inputs', './')
	init = utils.modelRun('./', 'init_atmosphere_model', 1, env, add_lsfoptions={'-W':'0:30', '-e':'run.err', '-o':'run.out'})
	init.runModelBlocking()
	supercell = utils.modelRun('./', 'atmosphere_model', 12, env, add_lsfoptions={'-W':'0:30', '-e':'run.err', '-o':'run.out'})
	supercell.runModelBlocking()

	e_init = init.get_result()
	e_supercell = supercell.get_result()
        err_code = e_init.get('err_code')+e_supercell.get('err_code')
        err_code = 0

	res.set('err_code', err_code)
	if err_code == 0:
#		os.system('ln -s /sysdisk1/duda/regtesting/mgduda/tests/regtest.2017-05-10_17.53.36/ideal_supercell/output.nc .')
		os.system('ncl supercell.ncl')
		os.system('mkdir figures')
		os.system('mv supercell.pdf figures')
		res.set('figures_directory', sandbox_dir+'/figures')
		res.set('success', True)
		res.set('err_msg', 'Supercell test passed')
	else:
		res.set('success', False)
		res.set('err_msg', 'Supercell test failed')

	res.set('completed', True)
	
	return
