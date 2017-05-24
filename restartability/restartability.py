from __future__ import print_function
import os, sys

# performs baseline 2 day run and outputs restart files every day
# moves all files that run created into subdirectory
# copies in new supporting files for restart run
# perform restarted run
# compare output files, store result in status object
# remove all files created by the test

utils = None
env = None

nprocs = 4
#dependencies=['comptest']

def setup(tparams):
	# set up any preconditions for the test
	# return a dictionary of all the items required from the driver for the test
	rundirA = tparams['test_dir']+'/runA'
	rundirB = tparams['test_dir']+'/runB'
	os.system('mkdir '+rundirA)
	os.system('mkdir '+rundirB)
	files = ['x1.2562.init.nc', 'x1.2562.graph.info.part.4', 'x1.2562.init.nc', 'x1.2562.graph.info.part.4']
	locations = [rundirA, rundirA, rundirB, rundirB]

	return {'modset':'gnu', 'exename':'atmosphere_model', 'files':files, 'locations':locations}



def test(tparams, res):
	env = tparams['env']
	utils = env.get('utils')

	res.set('completed', False)
	res.set('name', 'Restartability Test')

	if not env:
		print('No environment object passed to Restartability test, quitting Restartability test')
		return res
	if not utils:
		print('No utils module in test environment, quitting Restartability test')
		return res

	if not env.get('nc'):
		print('No netCDF module, quitting Restartability test')
		res.set('err_msg', 'No netCDF module, could not run test')
		return res
	if not env.get('np'):
		print('No numpy module, quitting Restartability test')
		res.set('err_msg', 'No numpy module, could not run test')
		return res

	# Set up all the directories we'll use and fill them with necessary files
	test_dir = tparams['test_dir'] # file path of our test sandbox, absolute 
	src_dir = tparams['src_dir']
	my_dir = tparams['SMARTS_dir']+'/restartability'
	my_config_files_A = my_dir+'/filesA'
	my_config_files_B = my_dir+'/filesB'
	rundirA = test_dir+'/runA'
	rundirB = test_dir+'/runB'
	os.chdir(rundirA)
	os.system('ln -s ../atmosphere_model .')
	os.system('ln -s '+src_dir+'/*.TBL .')
	os.system('ln -s '+src_dir+'/*.DBL .')
	os.system('ln -s '+src_dir+'/*DATA .')
	os.chdir(rundirB)
	os.system('ln -s ../atmosphere_model .')
	os.system('ln -s '+src_dir+'/*.TBL .')
	os.system('ln -s '+src_dir+'/*.DBL .')
	os.system('ln -s '+src_dir+'/*DATA .')

	# Prepare the 2-day run (A) and the restart run (B) model run objects
	utils.linkAllFiles(my_config_files_A, rundirA)
	A = utils.modelRun(rundirA, 'atmosphere_model', nprocs, env, add_lsfoptions={'-W':'0:05', '-e':'run.err', '-o':'run.out'}, add_pbsoptions={'-l':'walltime=5:00', '-N':'run'})
							 #directory in which to run the model, num mpi tasks, env object, additional lsf options

	utils.linkAllFiles(my_config_files_B, rundirB)
	B = utils.modelRun(rundirB, 'atmosphere_model', nprocs, env, add_lsfoptions={'-W':'0:05', '-e':'run.err', '-o':'run.out'}, add_pbsoptions={'-l':'walltime=5:00', '-N':'run'})

	# Start the 2day run in non-blocking mode
	# spin on the existence of the restart file
	# then start the restart run
	A.runModelNonblocking()
	
	restart_filename = 'restart.2010-10-24_00.00.00.nc'
	checkfor_filename = 'history.2010-10-24_06.00.00.nc'
	while checkfor_filename not in os.listdir(rundirA) and not A.is_finished():
		pass
	
	os.system('ln -s '+rundirA+'/restart.2010-10-24_00.00.00.nc '+rundirB)

	B.runModelNonblocking()

	while (not B.is_finished() or not A.is_finished()):
		pass

	# The terminate method must be called on all non-blocking runs after they have finished
	A.terminate()
	B.terminate()

	ra = A.get_result()
	rb = B.get_result()

	if (not ra.get('completed')):
		res.set('completed', False)
		res.set('success', False)
		res.set('err_code', ra.get('err_code'))
		res.set('err_msg', 'Initial run (run A) failed to run properly.')
		return res
		
	if (not rb.get('completed')):
		res.set('completed', False)
		res.set('success', False)
		res.set('err_code', rb.get('err_code'))
		res.set('err_msg', 'Initial run (run B) failed to run properly.')
		return res

	# Do the comparison
	diff = utils.compareFiles(rundirA+'/restart.2010-10-25_00.00.00.nc', rundirB+'/restart.2010-10-25_00.00.00.nc', env)
	if not diff:
		res.set('err_msg', 'File comparison failed to run.')
		return res

	res.set('success', len(diff.get('diff_fields')) == 0)
	if not res.get('success'):
		res.set('err', diff.get('diff_fields'))
		res.set('err_msg', "Check the restartability test directory for files to help you debug the reason for this error.")
		res.set('RMS Error', diff.get('rms_error'))
	res.set('completed', True)
	return res
