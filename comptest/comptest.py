import os, sys

# number of processors a compiler test uses should be 1
nprocs = 1
# list of environments this test is compatible with
compatible_environments = ['mmm', 'yellowstone']

def setup(tparams):
	return {'modset':'intel'}


def test(tparams, res):

	env = tparams['env']
	utils = env.get('utils')
	res.set('name', 'Compilation test (ifort)')
	res.set('completed_test', False)

	# Check to be sure there exists a modset you wish to reset to
	if not env.contains_modset('intel'):
		res.set('err_msg', 'In Comptest test(), no modset for intel')
		return res

	# Load the modules/environment variables required for the modset 'intel'
	# If available, use the versions specified in the second argument (optional)
	e = env.mod_reset('intel', {'intel':'16.0.3', 'pnetcdf':'1.6.0'})
	if e:
		res.set('err_msg', "In Comptest test(), error resetting to the modset 'intel'.")
		res.set('err_code', e)
		return res

	# Compile the MPAS source code (used by all tests, not a 'sandbox')
	src_dir = tparams['src_dir']
	
	r = utils.compile(src_dir, 'atmosphere', 'ifort')
	
	# Returns 0 if successfull. You may need to clean the code if the first try fails
	if r != 0:
		res.set('err_msg', 'Compile test first try returned '+str(r)+', trying again with clean on.')
		r = utils.compile(src_dir, 'atmosphere', 'ifort', True) # clean=True
	res.set('completed_test', True)
	res.set('success', r == 0)
	res.set('err_code', r)
