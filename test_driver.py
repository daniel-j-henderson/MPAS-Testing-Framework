from __future__ import print_function
import os, sys
import importlib as ilib


# Read config file
# import all test files
# run each test and collect its returned status object
# go through all status objects and prepare a test report



utils = ilib.import_module('utils.utils')
nc = ilib.import_module('netCDF4')
np = ilib.import_module('numpy')

env = utils.Environment()
env.set('name', 'mmm')
env.set('pathSL', '/sysdisk2/hendersn/Standard-Library/')
env.set('utils', utils)
env.set('nc', nc)
env.set('np', np)

pwd = os.getcwd()
tparams = {"test_dir":"/Volumes/sysdisk2/hendersn/test/MPAS-Release", "pwd":pwd, 'env':env}
results = []
for subdir in os.listdir("."):
	if len(subdir.split('.')) > 1:
		continue
	if subdir[0] == "." or "test_driver" in subdir or "utils" in subdir or 'results' in subdir:
		continue
	mod = ilib.import_module(subdir+"."+subdir)
	
	prec = mod.setup(tparams)
	if 'files' in prec:
		files = prec['files']
		if 'locations' in prec:
			locations = prec['locations']
		else:
			locations = [pwd]*len(files)
		for f,l in zip(files, locations): #zip creates temp variable rather than iterator
			utils.retrieveFileFromSL(f, l, env)

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
	if(not r.getAttribute('completed_test')):
		print("Test did not complete.")
	print(r.getAttribute("name")+" test " + 'succeeded' if r.getAttribute("success") else 'failed')
	if r.getAttribute("success") == False:
		err = r.getAttribute("err")
		if type(err) == list:
			print("List of items in error:")
			for e in err:
				print("    "+str(e))

		elif type(err) == str:
			print(err)