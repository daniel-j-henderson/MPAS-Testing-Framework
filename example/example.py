import os, sys

# 'nprocs': max number of MPI tasks this test may use at any given time.
# 'compatible_environments': list of environments this test can run on. Optional. default: all.
# 'dependencies': list, the names of any specific tests which must be performed before this test.
nprocs = 4
compatible_environments = ['all']


def setup(tparams):
	#return the name of the executable you want (it will be linked into your testing sandbox) 
	#and the max number of processors your test will use at a given time. Also, return a list of the files you
	#want from the Standard Library, and they will be put in your test_dir.

	#setup() is run in your test sandbox directory, so you can make any changes
	#to it that you need. Note: setup is not necessarily run directly before 
	#test(), so it is unwise to make any changes that might be reverted by some
	#other test before the test() function is called

	files = ['x1.2562.grid.nc', 'x1.2562.graph.info.part.4'] #list of desired files from the SL
	# optional :: locations  = [a, b ...] list of locations (absolute filepaths) to put each file in 'files'
													# len(locations) == len(files)
	return {'files':files, 'exename':'atmosphere_model'}

	"""
	Return Items (in a dictionary)
	'files': list of desired files from SL. 
	'locations': list of paths in which to place those files.
	'exename': name of executable the test would like to use (will be linked into the testing sandbox).
	"""

def test(tparams, res):
	#Arguments: tparams, a dictionary of useful things (like the environment object
	#and various directory paths) and res, the result object for the test. Res is already initialized.
	
	"""
	tparams =  {'src_dir':top-level MPAS directory path, 
					'SMARTS_dir':path to SMARTS directory, 
					'env':environment object, 
					'test_dir':path to testing sandbox (absolute), 
					'found':[True, False, ..., True] list of logicals that corresponds to each file requested 
						in the setup() method and whether that file was found in the SL
					}
					type: dictionary

	res = Result() 
					res.set('key', value) :: sets a result value
					res.get('key')			 :: gets a result value
		
					type: Result object
		
					You must set the key 'completed' before returning. You should also set the keys 'name', 'success', 'err_code', 
					'err_msg', etc. as you see fit. The driver will look for common keys, but it will also try and discover 
					your keys and report them as best it can.
	"""

	env = tparams['env']
	utils=env.get('utils')	

	res.set('completed', False) #The res object must have the 'completed' attribute set upon return.
										 #Should be True only if the tests finishes without error (regardless 
									    #of whether it failed).
	res.set('name', 'Example')  #res object should have the name set to the name of your test.

	if not env:
		print('No environment object passed to Example test, quitting')
		return res
	if not utils:
		print('No utils module in test environment, quitting Example test')
		return res
	

	test_dir = tparams['test_dir'] # file path of testing sandbox, absolute
	my_dir = tparams['SMARTS_dir']+'/example' # store any small files you need, e.g. namelists, in here somewhere

	#(completed, err_code) = runAtmosphereModel(dir, exename, ntasks, env, additional_lsf_options, additional_pbs_options)
	#completed: boolean, signifies whether the function runAtmosphereModel completed or returned early
	#err_code: the return code from the model executable
	#Note: this function blocks until the model run is complete

	#If your test comes with files like namelists and such, link them in this way
	#utils.linkAllFiles(my_dir+'/namelists', test_dir)

	myRun = utils.modelRun(test_dir, 'atmosphere_model', 4, env, add_lsfoptions={'-W':'0:01', '-e':'run.err', '-o':'run.out'})
	print('Starting model run')
	#myRun.runModelNonblocking() #returns immediately, model run happening in background
	#myRun.runModelBlocking() #returns when model run is finished
	e = myRun.dummyModelRun('success') # As an example, sets the result as if a successful model run occured
	while not myRun.is_finished(): # ex. wait for a nonblocking run to finish
		pass
	myRun.terminate()
	print('Finished model run')

	e = myRun.get_result()

	figdir = my_dir+'/figures'	
	res.set('figures_directory', figdir)

	res.set('success', e.get('completed') and e.get('success'))	
	res.set('err_code', e.get('err_code'))
	res.set('err_msg', 'Example test ran fine')
	res.set('completed', True)
	
	return
