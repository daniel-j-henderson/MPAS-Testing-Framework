import os, sys

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


class modelThread(threading.Thread):
   
	def __init__(self, pre=None, post=None, main=None, nprocs=1, args={}):
		threading.Thread.__init__(self)
		self.main = main
		self.pre = pre
		self.post = post
		self.num_procs = nprocs
		self.finished = False
		self.args = args
		self.result = None
		self.ready = False

	def run(self):
		self.pre(self.args['dir'])
		self.started = True
		self.result = self.main(self.args)
		self.post(self.args['dest'])
		self.finished = True
		
	def has_started(self):
		return self.started

	def is_finished(self):
		return self.finished

	def get_num_procs(self):
		return self.num_procs

def runModelNonblocking(dir, exename, n, env, dest, add_lsfoptions={}, add_pbsoptions{}):
	t = modelThread(pre=setupModelRun, post=returnFromModelRun, main=__runModelNonblocking__, nprocs = n, args={'dir':dir, 'exename':exename, 'n':n, 'env':env, 'dest':dest, 'add_lsfoptions':add_lsfoptions, 'add_pbsoptions':add_pbsoptions})
	t.start()
	return t 

def runModelBlocking(dir, exename, n, env, add_lsfoption={}, add_pbsoptions={}):
	popdir = setupModelRun(dir)
	r = runModel(dir, exename, n, env, add_lsfoption={}, add_pbsoptions={})
	returnFromModelRun(popdir)	
	return r

def setupModelRun(dir):
	if (not os.path.isdir(dir)):
		print('Invalid directory supplied to runModel: ' + dir)
		return False
	popdir = os.getcwd()
	os.chdir(dir)
	return popdir

def returnFromModelRun(dir):
	os.chdir(popdir)

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
	err = os.system(cmd)
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
			for i in range(0, len(f1.variables[k][:])):
				if f1.variables[k][i] != f2.variables[k][i]:
					n += 1
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

	if env.get('name') == 'Yellowstone':
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
	f.write('\\section{Successful Tests}\n')
	for r in results:
		if r.attributes:
			if not r.get('success'):
				continue
			f.write('\\subsection{'+r.get('name')+'}\n')
			f.write('\\begin{tabular}{|p{.3\\textwidth} |p{.7\\textwidth} |} \\hline\n')
			for k, v in r.attributes.items():
				f.write(translate(str(k)) + ' & ' + translate(str(v)) + ' \\\\ \\hline \n')
			f.write('\\end{tabular}\n')
	f.write('\\section{Failed Tests}\n')
	for r in results:
		if r.get('success'):
			continue
		f.write('\\subsection{'+r.get('name')+'}\n')
		f.write('\\begin{tabular}{|p{.3\\textwidth} |p{.7\\textwidth} |} \\hline\n')
		for k, v in r.attributes.items():
			f.write(translate(str(k)) + ' & ' + translate(str(v)) + ' \\\\ \\hline \n')
		f.write('\\end{tabular}\n')
	f.write('\\end{document}')






