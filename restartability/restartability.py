from __future__ import print_function
import os, sys

# takes arguments of test src code directory, init file, supporting files(namelist, streams, graph.info)
# performs baseline 2 day run and outputs restart files every day
# moves all files that run created into subdirectory
# copies in new supporting files for restart run
# perform restarted run
# compare output files, store result in status object
# remove all files created by the test

utils = None
env = None

nprocs = 4


def setup(tparams):
	# set up any preconditions for the test
	# return a dictionary of all the items required from the driver for the test
	files = ['x1.2562.init.nc', 'x1.2562.graph.info.part.4']
	locations = [tparams['test_dir'], tparams['test_dir']]

	return {'files':files, 'locations':locations, 'nprocs':nprocs}



def test(tparams):
	env = tparams['env']
	utils = env.get('utils')

	if not env:
		print("No environment object passed to Restartability test, quitting Restartability test")
		return None
	if not utils:
		print("No utils module in test environment, quitting Restartability test")
		return None


	res = utils.Result()

	test_dir = tparams["test_dir"] # file path of src code, absolute
	my_dir = tparams["pwd"]+"/restartability"
	my_config_files_A = my_dir+"/filesA"
	my_config_files_B = my_dir+"/filesB"
	working_dir = my_dir+"/working"

	os.system("rm -r "+working_dir)
	os.system("mkdir "+working_dir)
	utils.linkAllFiles(my_config_files_A, test_dir)
	utils.runModel(test_dir, nprocs, env)

	os.system("mv "+test_dir+"/restart.* "+working_dir)
	os.system("rm "+test_dir+"/*.nc")
	utils.linkAllFiles(my_config_files_B, test_dir)
	os.system("ln -s "+working_dir+"/restart.2014-09-11_00.00.00.nc "+test_dir)
	utils.runModel(test_dir, nprocs, env)

	diff = utils.compareFiles(working_dir+"/restart.2014-09-12_00.00.00.nc", test_dir+"/restart.2014-09-12_00.00.00.nc", env)

	res.attributes["success"] = (len(diff.getAttribute("diff_fields")) == 0)
	# if not res.attributes["success"]:
		# put in a debug folder all the files necessary to debug the reason why the test failed
	os.system("rm "+test_dir+"/*.nc")
	os.system("rm -r "+working_dir)
	if not res.attributes["success"]:
		res.attributes["err"] = diff.getAttribute("diff_fields")
	res.attributes["name"] = "Restartability Test"
	res.attributes["completed_test"] = True
	return res