import os, sys
import threading, multiprocessing
import multiprocessing.managers as mm

class Result:
	
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

class Environment:

	NONE = 0
	ENVLSF = 1
	ENVPBS = 2
	
	def __init__(self):
		self.params = {}

	def get(self, pname):
		try:
			return self.params[pname]
		except KeyError:
			return None

	def set(self, pname, value):
		self.params[pname] = value
		return

class ResultManager(mm.BaseManager):
   pass

ResultManager.register('Result', Result)

class modelProcess(multiprocessing.Process):
   
	def __init__(self, pre=None, post=None, main=None, nprocs=1, args={}, result = None):
		#threading.Thread.__init__(self)
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
		self.t = modelProcess(pre=setupModelRun, post=returnFromModelRun, main=__runModelNonblocking__, nprocs = self.n_tasks, args={'dir':self.run_dir, 'exename':self.exename, 'n':self.n_tasks, 'env':self.env, 'dest':self.run_dir, 'add_lsfoptions':self.add_lsfoptions, 'add_pbsoptions':self.add_pbsoptions}, result = self.result)
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
		
def setupModelRun(dir):
	if (not os.path.isdir(dir)):
		print('Invalid directory supplied to runModel: ' + dir)
		return False
	popdir = os.getcwd()
	os.chdir(dir)
	return popdir

def returnFromModelRun(dir):
	os.chdir(dir)

def __runModelNonblocking__(args):
	return runModel(args['dir'], args['exename'], args['n'], args['env'], args['add_lsfoptions'], args['add_pbsoptions'])

def runModel(dir, exename, n, env, add_lsfoptions={}, add_pbsoptions={}):

#	if env.get('name') != 'mmm':
#		print('Trying to run model in '+env.get('name')+' environment which is not yet supported')
#		return False


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
		cmd = ''

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


def compareFiles(a, b, env):
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
		if k not in f2.variables:
			print('compareFiles: Element '+k+' is in '+f1+' but not '+f2)
			continue
		if not np.array_equal(f1.variables[k][:], f2.variables[k][:]):
			r.attributes['diff_fields'].append(k)
			i = 0
			n = 0
			rms = 0
			for i in range(0, len(f1.variables[k][:])):
				if f1.variables[k][i] != f2.variables[k][i]:
					n += 1
					rms += (f1.variables[k][i] - f2.variables[k][i])**2
			rms = rms / float(n)
			rms = rms**.5
			r.attributes['rms_error'].append(rms)
			r.attributes['num_diffs'].append(n)
	f1.close()
	f2.close()
	return r


def searchForFile(tag, name, relpath):
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
	import xml.etree.ElementTree as ET

	if env.get('name') == 'yellowstone':
		print('On yellowstone, looking for '+name)
	elif env.get('name') == 'mmm':
		print('On an MMM machine, looking for '+name)
	else:
		print('Unknown environment.')
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
	for file in os.listdir(dirA):
		if (file[0] == '.'):
			print(file)
			continue
		if file in os.listdir(dirB):
			print('replacing '+dirB+'/'+file)
			os.system('rm '+dirB+'/'+file)
		os.system('ln -s '+dirA+'/'+file +' '+ dirB+'/'+file)


def translate(string):
	str = ''
	if type(string) != type(str):
		return ''

	return string.replace('_', '\\_')

	
def writeReportTex(f, results):

	preamble = '\\documentclass[a4paper]{article} \n\\usepackage[english]{babel} \n\\usepackage[utf8x]{inputenc} \n\\usepackage{graphicx}\n\\usepackage[T1]{fontenc} \n\\usepackage[a4paper,top=3cm,bottom=2cm,left=3cm,right=3cm,marginparwidth=1.75cm]{geometry} \n\\title{MPAS Testing Framework Test Results} \n\\begin{document} \n\\maketitle'
	f.write(preamble)
	f.write('\n')
	current_group = None
	for t in results:
		r = t[0]
		if t[1] != current_group:
			current_group = t[1]
		f.write('\\section{'+translate(current_group)+'}\n')
		if r.attributes:
			f.write('\\subsection{'+r.get('name')+'}\n')
			f.write('\\begin{tabular}{|p{.3\\textwidth} |p{.7\\textwidth} |} \\hline\n')
			f.write('Result & '+ ('success' if r.get('success') else 'failed') + ' \\\\ \\hline \n')
			for k, v in r.attributes.items():
				f.write(translate(str(k)) + ' & ' + translate(str(v)) + ' \\\\ \\hline \n')
			f.write('\\end{tabular}\n')
#	f.write('\\section{Failed Tests}\n')
#	for r in results:
#		if r.get('success'):
#			continue
#		f.write('\\subsection{'+r.get('name')+'}\n')
#		f.write('\\begin{tabular}{|p{.3\\textwidth} |p{.7\\textwidth} |} \\hline\n')
#		for k, v in r.attributes.items():
#			f.write(translate(str(k)) + ' & ' + translate(str(v)) + ' \\\\ \\hline \n')
#		f.write('\\end{tabular}\n')
	f.write('\\end{document}')






