import os, sys, time

def setup(tparams):
	return {'exename':'toy', 'nprocs':7}

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

	dirA = cwd + '/A'
	dirB = cwd + '/B'
	os.system('mkdir '+dirA)
	os.system('mkdir '+dirB)
	os.chdir('A')
	os.system('ln -s ../toy .')
	os.chdir('../B')
	os.system('ln -s ../toy .')
	os.chdir('..')
	A = utils.modelRun(dirA, 'toy', 4, env, add_lsfoptions={'-W':'0:01', '-e':'run.err', '-o':'run.out'})
	B = utils.modelRun(dirB, 'toy', 3, env, add_lsfoptions={'-W':'0:01', '-e':'run.err', '-o':'run.out'})
	A.runModelNonblocking()
	while not A.has_started():
		pass
	print('A has started')
	B.runModelBlocking()
#	while not B.has_started():
#		pass
	print('B has finished')
	#B = utils.runModelNonblocking(dirB, 'toy', 3, env, cwd, add_lsfoptions={'-W':'0:01', '-e':'run.err', '-o':'run.out'})
	#while not B.has_started():
#		pass
	#time.sleep(.2)
	#print('Both runs have started')
	#import multiprocessing
	#while not (A.is_finished() and B.is_finished()):
	#	print('Waiting...'+str(len(multiprocessing.active_children())))
#		time.sleep(1)

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

#	res.set('success', eb.get('completed'))
#	res.set('errcode', eb.get('err_code'))
	res.set('success', ea.get('completed') and eb.get('completed'))
	res.set('err_code', (ea.get('err_code'), eb.get('err_code')))

	#e = utils.runModelBlocking(test_dir, 'toy', 4, env, add_lsfoptions={'-K':'', '-W':'0:01', '-e':'run.err', '-o':'run.out'})
	# = (True, 0)
	#res.set('success', e[0])	
	#res.set('errcode', e[1])
	res.set('completed', True)
	return res
