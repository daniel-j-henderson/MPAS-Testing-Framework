import os, sys, time

"""
This 'toytest' demonstrates a blocking and non-blocking model run going at the same time. We
use a dummy 'toy' program instead of MPAS for testing purposes. The code for this toy program 
can be found in the examples folder, or really any toy program that can take any number of MPI
tasks will do. 

The 'toytest' directory should be placed one level up, with all the other tests.
The 'toy' executable should be placed in the 'src_dir'. 
"""


nprocs = 7

def setup(tparams):
	return {'exename':'toy'}

def test(tparams, res):
	env = tparams['env']
	utils=env.get('utils')
	

	res.set('completed', False)
	res.set('name', 'Toy Test (4)')

	if not env:
		print('No environment object passed to Restartability test, quitting Toy test')
		return res
	if not utils:
		print('No utils module in test environment, quitting Toy test')
		return res
	

	test_dir = tparams['test_dir'] # file path of src code, absolute
	my_dir = tparams['SMARTS_dir']+'/toytest'

	cwd = os.getcwd()

	# Prepare directories for each of the model runs
	dirA = cwd + '/A'
	dirB = cwd + '/B'
	os.system('mkdir '+dirA)
	os.system('mkdir '+dirB)
	os.chdir('A')
	os.system('ln -s ../toy .')
	os.chdir('../B')
	os.system('ln -s ../toy .')
	os.chdir('..')

	# Call the modelRun object constructors
	A = utils.modelRun(dirA, 'toy', 4, env, add_lsfoptions={'-W':'0:01', '-e':'run.err', '-o':'run.out'})
	B = utils.modelRun(dirB, 'toy', 3, env, add_lsfoptions={'-W':'0:01', '-e':'run.err', '-o':'run.out'})
	# Run the toy model in nonblocking mode. Returns immediately.
	A.runModelNonblocking()
	while not A.has_started():
		pass
	print('A has started')
	# Run the toy model in blocking mode. Returns when run is finished.
	B.runModelBlocking()
	print('B has finished')
	#B = utils.runModelNonblocking(dirB, 'toy', 3, env, cwd, add_lsfoptions={'-W':'0:01', '-e':'run.err', '-o':'run.out'})
	#while not B.has_started():
#		pass
	#time.sleep(.2)
	#print('Both runs have started')

#	while not A.is_finished() or not B.is_finished():
	while not A.is_finished():
		time.sleep(1)
		print('Waiting on A...')
	print('Finished')
#	while not B.is_finished():
#		time.sleep(1)
#		print('Waitingon B...')
#	print('Finished')
	A.terminate()
	B.terminate()
	print('Terminated')
	ea = A.get_result()
	eb = B.get_result()

	res.set('success', ea.get('completed') and eb.get('completed'))
	res.set('err_code', (ea.get('err_code'), eb.get('err_code')))

	res.set('completed', True)
	return res
