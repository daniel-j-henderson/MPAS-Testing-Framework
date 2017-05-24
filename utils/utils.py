import os, sys
import threading, multiprocessing
import multiprocessing.managers as mm

"""
What's Included (for test writers):
	Result class
	Environment class
	modelRun class

	compareFiles() method
	searchForFile() method
	retreiveFileFromSL() method
	linkAllFiles() method

	Note: if you utilize the setup() method in your test, there is no
			need to use the searchForFile() or retreiveFileFromSL() methods.	

"""

class Result:
	"""
	Result Class
	Used to store the results of a test or method. At present, is effectively like a wrapper around a dictionary. 
	Same syntax as Environment Class

	Note: the result for the test() method must set the 'completed' key, and should in most cases also set the 
			'success', 'err', 'err_msg', and 'err_code' keys
	"""
	
	def __init__(self):
		self.attributes = {}

	def get(self, attname):
		try:
			return self.attributes[attname]
		except KeyError:
			return None

	def set(self, attname, value):
		self.attributes[attname] = value
		return

	def remove(self, attname):
		try:
			del self.attributes[attname]
			return True
		except KeyError:
			return False


class Environment:
	"""
	Environment class
	Used to store parameters/objects specific to the computing environment the tests are running on, like
	Yellowstone, Cheyenne, or a local mmm machine.
	
	get
		pname
			type: string	
			content: key, name of parameter
		return 
			type: any
			content: could be a module, integer, string etc. specific to the computing environment
	"""

	NONE = 0 # No supercomputing environment. MMM local machine
	ENVLSF = 1 # LSF system
	ENVPBS = 2 # PBS batch system
	
	def __init__(self):
		self.params = {}
		self.modsets = {}

	def get(self, pname):
		try:
			return self.params[pname]
		except KeyError:
			return None

	def set(self, pname, value):
		self.params[pname] = value
		return

	def add_modset(self, name, root):
		self.modsets[name] = root

	def module(self, *args):
		if not self.get('LMOD_CMD'):
			print('Module command not found.')
			return False
		import string
		import subprocess as sp
		a = sp.Popen(self.get('LMOD_CMD')+' python '+string.join(args), shell=True, stdout=sp.PIPE)
		exec a.stdout.read()
		return a.wait()

	def contains_modset(self, name):
		return (name in self.modsets)

	def mod_reset(self, name, versions={}):

		if not self.contains_modset(name):
			return False 
		modset = self.modsets[name]
		e = self.module('purge')
		if e:
			print('purge failed')

		# Start by resetting to the base modules. All modsets are built off of the base modset.
		if name is not 'base':
			e = self.mod_reset('base')
			if e:
				return e
		for mod in modset:
			if mod.tag == 'module':
				modname = mod.get('name')
				if modname in versions: # if a version was requested, append it to the modname
					if versions[modname] in [c.get('v') for c in mod]:
						modname = modname+'/'+versions[modname]
					elif len(mod) > 0:
						modname = modname+'/'+mod[0].get('v')
				elif len(mod) > 0:
					modname = modname+'/'+mod[0].get('v')
				
				e = self.module('load', modname)
				if e:
					return e

			# the xml tag was for an environment variable
			elif mod.tag == 'env_var':
				os.environ[mod.get('name')] = mod.get('value')

class ResultManager(mm.BaseManager):
  	# Private to the utils module, test writer need not use 
   pass

ResultManager.register('Result', Result)




class modelProcess(multiprocessing.Process):
  	# Private to the utils module, test writer need not use 
	def __init__(self, pre=None, post=None, main=None, nprocs=1, args={}, result = None):
		multiprocessing.Process.__init__(self)
		self.main = main
		self.pre = pre
		self.post = post
		self.num_procs = nprocs
		self.finished = False
		self.result = result
		self.args = args
		self.started= False

	def run(self):
		self.pre(self.args['dir'])
		self.started = True
		res = self.main(self.args)
		self.result.set('completed', res[0])
		self.result.set('err_code', res[1])
		self.post(self.args['dest'])
		self.finished = True

	def get_result(self):
		return self.result
		
	def has_started(self):
		return self.started

	def is_finished(self):
		return self.finished

	def get_num_procs(self):
		return self.num_procs




class modelRun:

	"""
	Class modelRun
	Used to handle running the MPAS model in a test. When using, first initialize the object with all the parameters
	necessary (described below), then either choose to use either runModelNonblocking() or runModelBlocking().
	If runModelNonblocking() is used, then terminate() must be called after the model run has finished.

	__init__
		dir
			type: string
			content: absolute path to directory in which the model will run.
		exename
			type: string
			content: name of executable, e.g. atmosphere_model, init_atmosphere_model, toy
		n	
			type: integer
			content: number of MPI tasks to use
		env
			type: Environment object
		add_lsfoptions
			type: dictionary
			content: additional options for LSF systems, e.g. '-W':'0:05' for a wall clock time of 5 minutes, '-e':'run.err' to write standard error to run.err file
		add_pbsoptions
			type: dictionary
			content: additional options for PBS systems

		Note: the test writer should provide all of these parameters, although PBS systems are not yet supported
  

	runModelNonblocking
		Runs model in non-blocking mode. This method returns immediately and the model runs in the background.
		Use the has_started() and is_finished() methods to determine when the model has finished running. The
		terminate() method must be called at some point after the model run finishes (or, if the model run is 
		still going, it terminates it early).

		return
			type: logical
			content: method finished successfully

	runModelBlocking
		Runs model in blocking mode. This method blocks while the model is running, returning only after the run has finished. 
		There is no need to use the terminate() method after runModelBlocking.
		
		return
			type: logical
			content: method finished successfully
	
	dummyModelRun
		Returns a result object without running the model. Used as a prototype/simulated model run for examples/development purposes.
	
		type
			type: string
			content: 'success' or 'failure'. 
		return
			type: Result object
			content: a result corresponding to either a successful or failed model run

	has_started
		return
			type: logical
			content: model run has started (meaning the model run process has been started, not necessarily that the job is 
						running on the cluster, i.e. job may still be pending in the LSF queue)

	is_finished
		return
			type: logical
			content: model run has completed

	get_result
		return
			type: Result object
			content: result of the model run. Keys 'completed':logical, 'err_code':return code from the executable.
	"""

	def __init__(self, dir, exename, n, env, add_lsfoptions={}, add_pbsoptions={}): 
		self.run_dir = dir
		self.exename = exename
		self.n_tasks = n
		self.env = env
		self.add_lsfoptions = add_lsfoptions
		self.add_pbsoptions = add_pbsoptions
		self.started = False
		self.finished = False
		self.t = None
		self.result_manager = None

	def runModelNonblocking(self):
		self.result_manager = ResultManager()
		self.result_manager.start()
		self.result = self.result_manager.Result() 
		self.t = modelProcess(pre=setupModelRun, post=returnFromModelRun, main=__runModelNonblocking__, nprocs = self.n_tasks, 
									args={'dir':self.run_dir, 'exename':self.exename, 'n':self.n_tasks, 'env':self.env, 'dest':self.run_dir, 'add_lsfoptions':self.add_lsfoptions, 'add_pbsoptions':self.add_pbsoptions}, result = self.result)
		self.started = True
		self.t.start()
		return True 

	def runModelBlocking(self):
		self.started = True
		popdir = setupModelRun(self.run_dir)
		r = runModel(self.run_dir, self.exename, self.n_tasks, self.env, add_lsfoptions=self.add_lsfoptions, add_pbsoptions=self.add_pbsoptions)
		self.result = Result()
		self.result.set('completed', r[0])
		self.result.set('err_code', r[1])
		returnFromModelRun(popdir)	
		self.finished = True
		return True

	def dummyModelRun(self, type='success'):
		res = Result()
		if type == 'success':
			res.set('success', True)
			res.set('err_code', 0)
			res.set('err_msg', 'Test was successful')
		else:
			res.set('success', False)
			res.set('err_code', 1)
			res.set('err_msg', 'Test failed')
		res.set('completed', True)
		self.started = True
		self.finished = True
		self.result = res

	def has_started(self):
		return self.started

	def is_finished(self):
		if not self.started:
			return False	
		if self.t:
			self.finished = not self.t.is_alive()
		return self.finished

	def get_result(self):
		if self.result_manager:
			return self.result._getvalue()
		else:
			return self.result

	def terminate(self):
		if not self.has_started():
			print('Terminating a job which was never started.')
		if self.t:
			self.t.terminate()
		if self.result_manager:
			self.result = self.result._getvalue()
			self.result_manager.shutdown()
			self.result_manager = None



#		
# The following 4 methods should be considered private and not used by the test writer
#
def setupModelRun(dir):
	# Always runs before runModel()
	if (not os.path.isdir(dir)):
		print('Invalid directory supplied to runModel: ' + dir)
		return False
	popdir = os.getcwd()
	os.chdir(dir)
	return popdir

def returnFromModelRun(dir):
	# Always runs after runModel()
	os.chdir(dir)

def __runModelNonblocking__(args):
	return runModel(args['dir'], args['exename'], args['n'], args['env'], args['add_lsfoptions'], args['add_pbsoptions'])

def runModel(dir, exename, n, env, add_lsfoptions={}, add_pbsoptions={}):

	if env.get('name') == 'yellowstone' or env.get('type') == Environment.ENVLSF:
		args = []
		lsf_options = env.get('lsf_options')
		lsf_options['-K'] = ''
		for key, value in lsf_options.items():
			if key in add_lsfoptions:
				continue
			args.append(str(key) + ' ' + str(value))
		for key, value in add_lsfoptions.items():
			args.append(str(key) + ' ' + str(value))

		cmd = 'bsub -n ' + str(n) + ' '
		for option in args:
			cmd += option + ' '
		cmd += 'mpirun.lsf ./'+exename
		print(cmd)

	elif env.get('type') == Environment.ENVPBS:
		print('Running on '+env.get('name')+', a PBS system.')
		args = []
		pbs_options = env.get('pbs_options')
		pbs_options['-W'] = 'block=true'
		pbs_options['-N'] = exename
		for key, value in pbs_options.items():
			if key in add_pbsoptions:
				continue
			args.append(str(key) + ' ' + str(value))
		for key, value in add_pbsoptions.items():
			args.append(str(key) + ' ' + str(value))

		args.append(' -l select=1:ncpus=' + str(n) + ':mpiprocs=' + str(n) + ' ')
		os.system('echo \'#PBS ' + ' '.join(args) + '\' > script.' + exename)
		os.system('echo \'mpiexec_mpt ./' + exename + '\' >> script.' + exename)
		cmd = 'qsub script.' + exename
		print(cmd)

	elif env.get('name') == 'mmm' or env.get('type') == Environment.NONE:
		cmd = 'mpirun -n '+str(n)+' ./'+exename
		print(cmd)

	completed = False
	print(os.getcwd())
	err = os.system(cmd)
	print(os.getcwd())
	if (err):
		print('error running '+exename+' in '+dir+', error code '+str(err))
	else:
		completed = True	
	return completed, err
#
#
#



def compile(src_dir, core, target, clean=False):
	popdir = os.getcwd()
	os.chdir(src_dir)
	if clean:
		r = os.system('make clean CORE='+core)
		if r != 0:
			return r
	r = os.system('make '+target+' CORE='+core)
	os.chdir(popdir)
	return r

#
# The following 4 methods are utilities for the test writer to utilize.
#

def compareFiles(a, b, env, ignore=[]):
	"""
	Compares netcdf files 'a' and 'b' on the environment 'env' and returns a result containing info about any differences found.
	a, b
		type: string
		content: absolute filepath of each netcdf file to be compared
	env
		type: Environment object
	ignore:
		type: list
		content: names (strings) of fields for which we need not compare the 2 files. Optional.
	return
		type: Result object
		content:
					'diff_fields' // type: list(string), names of each field which is not bitwise identical between files a and b
					'num_diffs' // type: list(int), number of differences for each differing field
					'rms_error' // type: list(float), RMS difference for each differing field
	Note: any fields not present in both files are skipped
	"""

	nc = env.get('nc')
	np = env.get('np')
	if not nc:
		print('In utils module, netcdf module not provided in environment object')
		return -1
	if not nc:
		print('In utils module, numpy module not provided in environment object')
		return -1

	r = Result()
	r.attributes['diff_fields'] = []
	r.attributes['num_diffs'] = []
	r.attributes['rms_error'] = []

	if not os.path.isfile(a):
		print(str(a)+': File not found, cannot compare to '+str(b))
		return False
	if not os.path.isfile(b):
		print(str(b)+': File not found, cannot compare to '+str(a))
		return False
		

	f1 = nc.Dataset(a, 'r')
	f2 = nc.Dataset(b, 'r')

	for k in f1.variables.keys():
		if k in ignore:
			continue
		if k not in f2.variables:
			print('compareFiles: Element '+k+' is in '+f1+' but not '+f2)
			continue
		if not np.array_equal(f1.variables[k][:], f2.variables[k][:]):
			r.attributes['diff_fields'].append(k)
			i = 0
			n = 0
			rms = 0
			a = np.ndarray.flatten(f1.variables[k][:])
			b = np.ndarray.flatten(f2.variables[k][:])
			if len(a) != len(b):
				print('Error: 2 comparable fields are dimensioned differently')
				os._exit(5)
			for i in range(0, len(a)):
				if a[i] != b[i]:
					n += 1
					rms += (a[i] - b[i])**2
			rms = rms / float(n)
			rms = rms**.5
			r.attributes['rms_error'].append(rms)
			r.attributes['num_diffs'].append(n)
	f1.close()
	f2.close()
	return r


def searchForFile(tag, name, relpath):
	"""
	Recursively searches the xml tree 'tag' for the file 'name', appending the subdirectories traveled to the list 'relpath'
	tag
		type: ElementTree object 
		content: tag of the Library.xml tree
	name
		type: string
		content: filename
	relpath
		type: list
		content: subdirectories traveled (in reverse order) to find 'name'
	return
		type: logical
		content: tag for file 'name' found in the subtree 'tag'
	"""
	
	import xml.etree.ElementTree as ET
	for child in tag:
		if child.tag == 'file':
			if child.get('name') == name:
				relpath.append(name)
				return True
	for child in tag:
		if child.tag == 'subdir':
			if searchForFile(child, name, relpath):
				relpath.append(child.get('subpath'))
				return True
	return False


def retrieveFileFromSL(name, dest, env):
	"""
	Retreives file 'name' from the SL on the 'env' environment and places it in the 'dest' directory'.
	name
		type: string
		content: name of file
	dest
		type: string
		content: absolute path to destination directory
	env
		type: Environment object

	return
		type: logical
		content: file was found and copied successfully
	"""

	import xml.etree.ElementTree as ET

	# Sanity checks during development
	if env.get('name') == 'yellowstone':
		print('On yellowstone, looking for '+name)
	elif env.get('name') == 'mmm':
		print('On an MMM machine, looking for '+name)
	else:
		print('Unknown environment.')

	# move to the SL if it exists
	popdir = os.getcwd()
	if env.get('pathSL'):
		os.chdir(env.get('pathSL'))
	else:
		print('No SL in this environment')
		return False

	#TODO check for existence
	root = ET.parse('Library.xml').getroot()
	filepath = root.get('path')
	relpath = []
	
	found = searchForFile(root, name, relpath)
	if found:
		for subpath in reversed(relpath):
			filepath += subpath
		print('file found: '+filepath)
		os.system('ln -sf '+filepath+' '+dest)
	else:
		print("didn't find the item")
	os.chdir(popdir)

	return found

def linkAllFiles(dirA, dirB):
	"""
	Attempts to link all files from dirA into dirB. A little more convenient to the test writer than
	linking specific files.
	dirA, dirB :: absolute paths to directories A and B
					  type: string
	"""
	for file in os.listdir(dirA):
		if (file[0] == '.'):
			print(file)
			continue
		if file in os.listdir(dirB):
			print('replacing '+dirB+'/'+file)
			os.system('rm '+dirB+'/'+file)
		os.system('ln -s '+dirA+'/'+file +' '+ dirB+'/'+file)

#
# The following methods should be considered private and not used by the test writer. They are for 
# use in the test_driver script.
#
def translate(string):
	# Used only in writeReportTex()
	str = ''
	if type(string) != type(str):
		return ''

	return string.replace('_', '\\_')

	
def writeReportTex(f, results):

	preamble = '\\documentclass{article} \n\\usepackage{graphicx}\n\\usepackage[top=3cm,bottom=2cm,left=3cm,right=3cm,marginparwidth=1.75cm]{geometry} \n\\title{MPAS Testing Framework Test Results} \n\\begin{document} \n\\maketitle'
	f.write(preamble)
	f.write('\n')
	current_group = None
	for t in results:
		r = t[0]
		if t[1] != current_group:
			current_group = t[1]
		f.write('\\section{'+translate(current_group)+'}\n')
		if r.attributes:
			f.write('\\subsection{'+translate(r.get('name'))+'}\n')
			f.write('\\begin{tabular}{|p{.3\\textwidth} |p{.7\\textwidth} |} \\hline\n')
			f.write('Result & '+ ('success' if r.get('success') else 'failed') + ' \\\\ \\hline \n')
			for k, v in r.attributes.items():
				f.write(translate(str(k)) + ' & ' + translate(str(v)) + ' \\\\ \\hline \n')
			f.write('\\end{tabular}\n')
		if r.get('figures_directory'):
			figdir = r.get('figures_directory')
			print(figdir)
			for file in os.listdir(r.get('figures_directory')):
				f.write('\\includegraphics[width=6.5in]{'+figdir+'/'+file+'}\n')
	f.write('\\end{document}')
#
#
#

"""
END MODULE UTILS
"""



