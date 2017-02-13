import os, sys

def setup(tparams):
	#return the name of the executable you want (it will be linked into your testing sandbox) 
	#and the max number of processors your test will use at a given time. Also, return a list of the files you
	#want from the Standard Library, and they will be put in your test_dir.

	#setup() is run in your test sandbox directory, so you can make any changes
	#to it that you need. Note: setup is not necessarily run directly before 
	#test(), so it is unwise to make any changes that might be reverted by some
	#other test before the test() function is called

	files = [x1.2562.grid.nc, x1.2562.graph.part.4]
	return {'files':files, 'exename':'atmosphere_model', 'nprocs':4}

def test(tparams, res):
	#Arguments: tparams, a dictionary of useful things (like the environment object
	#and various directory paths) and res, the result object for the test. Res is already initialized.

	env = tparams['env']
	utils=env.get('utils')	

	res.set('completed_test', False) #The res object must have the 'completed_test' attribute set upon return.
	res.set('name', 'Toy Test (4)')  #res object should have the name set to the name of your test.

	if not env:
		print('No environment object passed to Restartability test, quitting Toy test')
		return res
	if not utils:
		print('No utils module in test environment, quitting Toy test')
		return res
	

	test_dir = tparams['test_dir'] # file path of testing sandbox, absolute
	my_dir = tparams['SMARTS_dir']+'/toytest' # store any small files you need, e.g. namelists, in here somewhere

	#(completed, err_code) = runAtmosphereModel(dir, exename, ntasks, env, additional_lsf_options, additional_pbs_options)
	#completed: boolean, signifies whether the function runAtmosphereModel completed or returned early
	#err_code: the return code from the model executable
	#Note: this function blocks until the model run is complete

	utils.linkAllFIles(my_dir+'/namelists', test_dir)
	myRun = utils.modelRun(test_dir, 'atmosphere_model', 4, env, add_lsfoptions={'-W':'0:01', '-e':'run.err', '-o':'run.out'})

	myRun.runModelNonblocking() #returns immediately, model run happening in background
	#myRun.runModelBlocking() #returns when model run is finished
	while not myRun.is_finished():
		pass
	myRun.terminate()

	e = myRun.get_result()
	res.set('success', e.get('completed') and e.get('success'))	
	res.set('errcode', e.get('err_code'))
	res.set('completed', True)
	
	return
