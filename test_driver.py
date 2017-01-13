from __future__ import print_function
import os, sys
import importlib as ilib
import pkgutil


# Read config file
# import all test files
# run each test and collect its returned status object
# go through all status objects and prepare a test report

import xml.etree.ElementTree as ET
utils = ilib.import_module('utils.utils')

fnames = os.listdir('.')
config_file = None
for f in fnames:
	if '.xml' in f:
		config_file = f
if not config_file:
	print('Please provide an environment configuration file in xml form.')
	os.exit(1)


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
	print(options)


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


env.set('utils', utils)
env.set('nc', nc)
env.set('np', np)

if len(sys.argv) >1:
	test_dir = sys.argv[1]
else:
	if not root.get('test_dir'):
		print('You failed to provide the location of the MPAS source code to be tested. This can be provided in the xml file or on the command line.')
		sys.exit(3)
	test_dir = root.get('test_dir')

popdir = os.getcwd()
try:
	os.chdir(test_dir)
except OSError:
	print(test_dir+': Unknown directory. Please provide a valid path to the MPAS source code to be tested.')
	os.exit(2)
test_dir = os.getcwd()
os.chdir(popdir)

pwd = os.getcwd()
tparams = {'test_dir':test_dir, 'pwd':pwd, 'env':env}
results = []
for subdir in os.listdir('.'):
	if len(subdir.split('.')) > 1:
		continue
	if subdir[0] == '.' or 'test_driver' in subdir or 'utils' in subdir or 'results' in subdir or '.xml' in subdir:
		continue
	try:
		mod = ilib.import_module(subdir+'.'+subdir)
	except ImportError:
		print("'"+subdir+"' is not a test module, skipping it")
		continue
	
	print("\nRunning "+subdir+" test\n\n")

	prec = mod.setup(tparams)
	if 'files' in prec:
		files = prec['files']
		if 'locations' in prec:
			locations = prec['locations']
		else:
			locations = [pwd]*len(files)
		found_files=[False]*len(files)
		for i in range(len(files)):
			if utils.retrieveFileFromSL(files[i], locations[i], env):
				found_files[i] = True
		tparams['found_files'] = found_files


	results.append(mod.test(tparams))

os.system('rm -r results')
os.system('mkdir results')

import datetime
timestamp = datetime.datetime.now().isoformat()
tfname = 'Results.'+timestamp+'.tex'
os.chdir('results')
f = open(tfname, 'w')
utils.writeReportTex(f, results)
f.close()
os.system('pdflatex -halt-on-error -interaction=batchmode '+tfname)
os.chdir('..')


for r in results:
	if(not r.get('completed_test')):
		print('Test did not complete.')
	print(r.get('name')+' test ' + 'succeeded' if r.get('success') else 'failed')
	if r.get('success') == False:
		err = r.get('err')
		if type(err) == list:
			print('List of items in error:')
			for e in err:
				print('    '+str(e))

		elif type(err) == str:
			print(err)


