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
from distutils import spawn
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


#
#
# Check for any necessary executables
#
#

if not spawn.find_executable('pdflatex'):
	print("The executable 'pdflatex' could not be found, so a pdf report of test results cannot be made. If you would like to see a basic results printout on the screen, or generate the '.tex.' file for reference/future use, continue. Would you like to continue?")
	choice = raw_input('y/n: ')
	if choice in ['n', 'N', 'no', 'NO']:
		os._exit(4)


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
env.set('modules', root.get('modules'))

if env.get('modules'):
	env.set('LMOD_CMD', root.get('LMOD_CMD'))
for modset in root.findall('modset'):
	env.add_modset(modset.get('name'), modset)
	if modset.get('default') in ['true', 'True', 'TRUE']:
		env.set('default_build_env', modset.get('name'))
		env.set('default_build_target', modset.get('compiler'))
if not env.get('default_build_env'):
	env.set('default_build_env', 'intel')
	env.set('default_build_target', 'ifort')
if not env.contains_modset('base'):
	print('Environment XML file must contain base modset.')
	os._exit(1)	
if root.get('PYTHONPATH'):
	sys.path.append(root.get('PYTHONPATH'))
env.mod_reset('base')

# Depending on the batch system, put the necessary options (things like
# project codes or queue names) in the environment object in a dict
if root.get('batchsystem') == 'LSF':
	env.set('batchsystem', 'LSF')
	options = {}
	for lsf_option in root.findall('lsf_option'):
		options[lsf_option.get('name')] = lsf_option.get('value')
	env.set('lsf_options', options)
if root.get('max_cores'):
	total_procs = int(root.get('max_cores'))

env.set('utils', utils)
env.set('nc', nc)
env.set('np', np)

try:
	i = cmdargs.index('-n')
	total_procs = int(cmdargs[i+1])
	cmdargs.pop(i+1)
	cmdargs.pop(i)
except IndexError:
	pass
except ValueError:
	pass
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
# Make a process for each test
#
#
unfinished_tests = []
managers = {}

for group_name, test_arr in tests.items():
	for subdir in test_arr:
		
		try:
			sys.path.append(SMARTS_dir+'/'+subdir)
			mod = ilib.import_module(subdir)
		except ImportError:
			print("'"+subdir+"' is not a test module, skipping it")
			continue

		try:
			if env.get('name') not in mod.compatible_environments and 'all' not in mod.compatible_environments:
				print('The '+subdir+' test is not compatible with this environment ('+env.get('name')+')')
				continue
		except AttributeError:
			pass

		test_dir = container+'/'+subdir
		if mod.nprocs > total_procs:
			print('Cannot perform '+subdir+' test due to resource constraints')
			continue	

		managers[subdir] = ResultManager()
		managers[subdir].start()
		r = managers[subdir].Result()
		unfinished_tests.append(testProcess(func=mod.test, setup=mod.setup, nprocs=mod.nprocs, initpath=test_dir, name=subdir, result=r, group=group_name))
		try:
			unfinished_tests[-1].dependencies = mod.dependencies
		except AttributeError:
			pass


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
			try:
				
				depends = t.dependencies
				if len(finished_tests) > 0:
					finished = [test.get_name() for test in finished_tests]
				else:
					finished = []
				if len(unfinished_tests) > 0:
					unfinished = [test.get_name() for test in unfinished_tests]
				else:
					unfinished = []
				if len(tests_in_progress) > 0:
					inprogress = [test.get_name() for test in tests_in_progress]
				else:
					inprogress = []
				ready = True
				for dep in depends:
					if dep not in finished:
						if dep not in unfinished and dep not in inprogress:
							print('Test '+t.get_name()+' depends on a test which we are not testing, so it will be skipped.')
							unfinished_tests.remove(t)
						ready = False
						continue
				if not ready:
					continue
			except AttributeError:
				pass

			if t.get_num_procs() <= total_procs - procs_in_use:
				procs_in_use += t.get_num_procs()
				tests_in_progress.append(t)
				unfinished_tests.remove(t)
				tname = tests_in_progress[-1].get_name()
				print('\nStarting '+tname+' test.')


				test_dir = container+'/'+tname
				os.system('mkdir '+test_dir)
				tparams = tparams_base.copy()
				tparams['test_dir'] = test_dir


				popdir = os.getcwd()
				os.chdir(test_dir)
				prec = t.setup(tparams)
				os.chdir(popdir)

				if 'exename' in prec:
					exenames = prec['exename']
					if type(exenames) != type([]):
						exenames = [exenames]
					for exename in exenames:
						if not os.path.exists(src_dir+'/'+exename):
							env.mod_reset(env.get('default_build_env'))
							e = utils.compile(src_dir, exename.replace('_model', ''), env.get('default_build_target'))
							if e:
								r = utils.compile(src_dir, exename.replace('_model', ''), env.get('default_build_target'), clean=True)
								if r:
									print(exename+' does not exist in '+src_dir+' and cannot be built')
									os._exit(1)
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

				t.tparams = tparams
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
if spawn.find_executable('pdflatex'):
	os.system('pdflatex -halt-on-error -interaction=batchmode '+tfname)
	os.system('rm *.aux *.log *.tex')
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
