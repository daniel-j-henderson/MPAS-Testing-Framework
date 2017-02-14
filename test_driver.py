#
# MPAS Regression Testing Framework
#

# test_driver.py


#
#
# Import all necessary modules
#
#
from __future__ import print_function
import os, sys
import importlib as ilib
import pkgutil
import threading
import datetime
import multiprocessing
import xml.etree.ElementTree as ET
import multiprocessing.managers as mm

utils = ilib.import_module('utils.utils')

if pkgutil.find_loader('netCDF4'):
	nc = ilib.import_module('netCDF4')
	print("Found netCDF module")
else:
	nc = None
if pkgutil.find_loader('numpy'):
	np = ilib.import_module('numpy')
	print("Found numpy module")
else:
	np = None

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
   
	def __init__(self, func=None, nprocs=1, tparams={}, initpath='.', name='', result=None, group=None):
		multiprocessing.Process.__init__(self)
		self.myTest = func
		self.group = group
		self.num_procs = nprocs
		self.finished = False
		self.tparams = tparams
		self.cwd = initpath
		self.name = name
		self.result = result	

	def run(self):

		os.chdir(self.cwd)
		self.myTest(self.tparams, self.result)
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

#
#
# Set up the environment object
#
#
timestamp = datetime.datetime.now().replace(microsecond=0).isoformat().replace('T', '_').replace(':', '.')
fnames = os.listdir('.')
config_file = None
cmdargs = sys.argv[:]

try:
	i = cmdargs.index('-env')
	config_file = cmdargs[i+1]
	print('config file == '+config_file)
	cmdargs.pop(i+1)
	cmdargs.pop(i)
except IndexError:
	if 'Environment.xml' in fnames:
		config_file = 'Environment.xml'
except ValueError:
	if 'Environment.xml' in fnames:
		config_file = 'Environment.xml'

if not config_file:
	print('Please provide an environment configuration file in xml form.')
	os._exit(1)

env = utils.Environment()
root = ET.parse(config_file).getroot()
filepath = root.get('path')
env.set('name', root.get('name'))
env.set('pathSL', root.get('pathSL'))
if root.get('PYTHONPATH'):
	os.environ['PYTHONPATH'] = root.get('PYTHONPATH')


# Depending on the batch system, put the necessary options (things like
# project codes or queue names) in the environment object in a dict
if root.get('batchsystem') == 'LSF':
	env.set('batchsystem', 'LSF')
	options = {}
	for lsf_option in root.findall('lsf_option'):
		options[lsf_option.get('name')] = lsf_option.get('value')
	env.set('lsf_options', options)


env.set('utils', utils)
env.set('nc', nc)
env.set('np', np)

total_procs = 8
try:
	i = cmdargs.index('-n')
	total_procs = int(cmdargs[i+1])
	cmdargs.pop(i+1)
	cmdargs.pop(i)
except IndexError:
	print("Please provide the max number of cores you'd like to run the reg tests on.")
except ValueError:
	print("Please provide the max number of cores you'd like to run the reg tests on.")
print('Max Cores: '+str(total_procs))
	
try:
	i = cmdargs.index('-src')
	src_dir = cmdargs[i+1]
	popdir = os.getcwd()
	os.chdir(src_dir)
	src_dir = os.getcwd()
	os.chdir(popdir)
	cmdargs.pop(i+1)
	cmdargs.pop(i)
except IndexError:
	src_dir = os.getcwd()
except ValueError:
	src_dir = os.getcwd()

pwd = os.getcwd()
SMARTS_dir = os.path.dirname(os.path.realpath( __file__ ))

tests = {}
root = ET.parse(SMARTS_dir+'/Tests.xml').getroot()
for el in root:
	if el.tag == 'test_group' and el.get('name') in cmdargs:
		group_name = el.get('name')
		tests[group_name] = []
		for t in el:
			tests[group_name].append(t.get('name'))
for key in tests:
	if key in cmdargs:
		cmdargs.remove(key)

if len(cmdargs) > 1:
	tests['misc'] = []
	for i in range(1,len(cmdargs)):
		tests['misc'].append(cmdargs[i])


results = []
tparams_base = {'src_dir':src_dir, 'SMARTS_dir':SMARTS_dir, 'env':env}

container = pwd+'/'+'regtest.'+timestamp
os.system('mkdir '+container)



#
#
# Make a process for each test, complete with the necessary preconditions
#
#
unfinished_tests = []
managers = {}
#for subdir in os.listdir(SMARTS_dir):
#	if test_names and subdir not in test_names:
#		continue
#	if len(subdir.split('.')) > 1:
#		continue
#	if subdir[0] == '.' or 'test_driver' in subdir or 'utils' in subdir or 'results' in subdir or '.xml' in subdir:
#		continue
#	try:
#		mod = ilib.import_module(subdir+'.'+subdir)
#	except ImportError:
#		print("'"+subdir+"' is not a test module, skipping it")
#		continue

for group_name, test_arr in tests.items():
	for subdir in test_arr:
		
		try:
			sys.path.append(SMARTS_dir+'/'+subdir)
			mod = ilib.import_module(subdir)
		except ImportError:
			print("'"+subdir+"' is not a test module, skipping it")
			continue



		test_dir = container+'/'+subdir
		os.system('mkdir '+test_dir)
		tparams = tparams_base.copy()
		tparams['test_dir'] = test_dir


		popdir = os.getcwd()
		os.chdir(test_dir)
		prec = mod.setup(tparams)
		os.chdir(popdir)

		if 'exename' in prec:
			exename = prec['exename']
			os.system('ln -s '+src_dir+'/'+exename+' '+test_dir)	

		if 'files' in prec:
			files = prec['files']
			if 'locations' in prec:
				locations = prec['locations']
			else:
				locations = [test_dir]*len(files)
			found_files=[False]*len(files)
			for i in range(len(files)):
				if utils.retrieveFileFromSL(files[i], locations[i], env):
					found_files[i] = True
			tparams['found_files'] = found_files

		if 'nprocs' in prec:
			nprocs = prec['nprocs']
		else:
			nprocs = 0
		if nprocs > total_procs:
			print('Cannot perform '+subdir+' test due to resource constraints')
			continue	

		managers[subdir] = ResultManager()
		managers[subdir].start()
		r = managers[subdir].Result()
		unfinished_tests.append(testProcess(func=mod.test, nprocs=nprocs, tparams=tparams, initpath=test_dir, name=subdir, result=r, group=group_name))


#
#
# Start tests, keeping the number of cores in use below the max
#
#

procs_in_use = 0
tests_in_progress = []
finished_tests = []
unfinished_tests.sort(key=lambda t: t.get_num_procs(), reverse=True)
while unfinished_tests:
	for t in tests_in_progress:
		if not t.is_alive():
			procs_in_use -= t.get_num_procs()
			finished_tests.append(t)
			tests_in_progress.remove(t)
	if procs_in_use < total_procs:
		for t in unfinished_tests:
			if t.get_num_procs() <= total_procs - procs_in_use:
				procs_in_use += t.get_num_procs()
				tests_in_progress.append(t)
				unfinished_tests.remove(t)
				print('\nStarting '+tests_in_progress[-1].get_name()+' test.')
				tests_in_progress[-1].start()
			
while tests_in_progress:
	t = tests_in_progress[0]
	t.join()
	finished_tests.append(t)
	tests_in_progress.remove(t)

finished_tests.sort(key=lambda t: t.get_group())
for t in finished_tests:
	results.append((t.get_result()._getvalue(), t.get_group()))
	managers[t.get_name()].shutdown()

# 
# 
# Report Results
#
#
result_dir = container+'/results'
os.system('mkdir '+result_dir)

tfname = 'Results.'+timestamp+'.tex'
popdir = os.getcwd()
os.chdir(result_dir)
f = open(tfname, 'w')
utils.writeReportTex(f, results)
f.close()
os.system('pdflatex -halt-on-error -interaction=batchmode '+tfname)
os.chdir(popdir)


for t in results:
	r = t[0]
	if(not r.get('completed')):
		print('Test did not complete.')

	print(r.get('name')+' test ' + ('succeeded' if r.get('success') else 'failed'))

	if r.get('err_code') is not None:
		print ('   with error code '+str(r.get('err_code')))

	if r.get('success') == False:
		err = r.get('err')

		if type(err) == list:
			print('List of items in error:')
			for e in err:
				print('    '+str(e))
		elif type(err) == str:
			print(err)

print ('Done.')
