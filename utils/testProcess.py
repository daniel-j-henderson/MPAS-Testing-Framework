import multiprocessing
import multiprocessing.managers as mm
import utils
import os

#
#
# Class for the process objects for each test.
# The 'myTest' member is be a test() method from a test module.
#
#

class ResultManager(mm.BaseManager):
	pass

ResultManager.register('Result', utils.Result)

class testProcess(multiprocessing.Process):
   
	def __init__(self, func=None, setup=None, nprocs=1, tparams={}, initpath='.', name='', result=None, group=None):
		multiprocessing.Process.__init__(self)
		self.myTest = func
		self.setup = setup
		self.group = group
		self.num_procs = nprocs
		self.finished = False
		self.tparams = tparams
		self.cwd = initpath
		self.name = name
		self.result = result	

	def run(self):
		
		import time
		import datetime as dt
		os.chdir(self.cwd)
		t = time.time()
		self.myTest(self.tparams, self.result)
		t = time.time() - t
		self.result.set('Elapsed Time (hh:mm:ss)', str(dt.timedelta(seconds=round(t))))
		self.finished = True

	def get_num_procs(self):
		return self.num_procs

	def get_cwd(self):
		return self.cwd	

	def get_name(self):
		return self.name
	
	def is_finished(self):
		return self.finished

	def get_result(self):
		return self.result

	def get_group(self):
		return self.group
