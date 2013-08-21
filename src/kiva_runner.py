
import sys, os, csv, shutil, subprocess, time
from logger.logger import Logger
from itape import ITapeFile

class KivaRunner:
	"""
	This class can run kiva with a certain set of parameters
	and different temperture inputs.
	"""

	def __init__(self, working_dir, log_dir, compare_file, parameter_format, logger=None):
		"""
		parameter_format specifies what parameters from which files are needed.
		[file, name, min, max, step]
		"""
		if logger == None:
			self.log = Logger()
		else:
			self.log = logger
		self.error = False
		self.working_dir = working_dir
		self.log_dir = log_dir
		self.kiva_path = '../ext'
		self.kiva_name = 'kiva_0D'
		self.kiva_parameter_files = ['itape17', 'itape5', 'itapeERC', 'itapeRs']
		self.parameter_format = parameter_format
		self.log.debug("Parameter Format: %s" % self.parameter_format)
		# this will later hold all kiva_parameter_files that
		# need to be loaded as ITapeFile objects
		self.itapes = {}
		self.compare_file = compare_file
		# Check if working directory exists and that it is empty
		self.working_dir_indicator = os.path.join(self.working_dir, 'kivagen.working.dir')
		if not os.path.isdir(self.working_dir):
			self.log.error("'%s' does not exist." % self.working_dir)
			self.error = True
			self.working_dir = None
		elif os.listdir(self.working_dir):	# not empty
			if not os.path.isfile(self.working_dir_indicator):
				self.log.error("'%s' does not seem to be a working directory." % self.working_dir)
				self.error = True
				self.working_dir = None
				return
		else:
			open(self.working_dir_indicator, 'a').close()
		# Check that log dir exists
		if not os.path.isdir(self.log_dir):
			self.log.error("'%s' does not exist." % self.log_dir)
			self.error = True
			self.log_dir = None
		# Check if input files exist
		input_files = [self.compare_file]
		input_files.append(os.path.join(self.kiva_path, self.kiva_name))
		for parameter_file in self.kiva_parameter_files:
			input_files.append(os.path.join(self.kiva_path, parameter_file))
		for input_file in input_files:
			if not os.path.isfile(input_file):
				self.log.error("'%s' not found." % input_file)
				self.error = True
		# Parse compare file
		self.compare_values = self._readCompareFile(self.compare_file)
		# self.log.debug("self.compare_values = %s" % self.compare_values)
		# Load Parameters
		self.loadParameters()
		# self.log.debug("self.param_list = %s" % self.param_list)

# --------------- Parameters --------------------------------------------------
	def loadParameters(self):
		"""
		Loads the start parameters from the itape files.
		"""
		self.param_list = []
		# relaod parameters from file
		for itape in self.itapes.values():
			itape._open(itape.name)
		for param in self.parameter_format:
			# if file has not been loaded before
			if param[0] not in self.itapes:
				f = os.path.join(self.kiva_path, param[0])
				if param[0] in self.kiva_parameter_files:
					if param[0] in ['itapeERC', 'itapeRs']:
						self.itapes[param[0]] = ITapeFile(f, self.log)
					else:
						self.log.error("Failed to read %s. Can only read itapeERC and itapeRs." % f)
				else:
					self.log.error("Failed to read %s. Not in self.kiva_parameter_files (%s)" % self.kiva_parameter_files)
			# try to get parameter id
			ii = self.itapes[param[0]].getId(param[1])
			if ii < 0:
				self.log.error("Could not find '%s' in '%s'." % (param[1], param[0]))
				self.param_list.append(None) # append None to get index right
			else:
				value = self.itapes[param[0]].getValue(ii)
				self.param_list.append(self._checkParameter(value, param))
		# now we should have collected all parameters
		if len(self.param_list) != len(self.parameter_format):
			sel.log.error("Only found %s elements. Expected %s!"
							% (self.param_list, len(self.parameter_format)))

	def getParameters(self):
		"""
		Returns parameter list.
		"""
		return self.param_list

	def setParameters(self, parameters):
		"""
		Hand a new set of parameters to this class.
		They will be used for the next kiva runs.
		"""
		# 1.) check if parameter list length is correct
		if len(parameters) != len(self.parameter_format):
			sel.log.error("Parameter list needs to contain exactly %s elements. Not %s!"
							% (len(self.parameter_format), len(parameters)))
			return
		# 2.) Check if parameters are correct
		for ii in range(0, len(parameters)):
			if self._checkParameter(parameters[ii], self.parameter_format[ii]) == None:
				return
		# 3.) Replace parameter list
		self.param_list = parameters


	def _checkParameter(self, value, format_line):
		"""
		Returns None if parameter is out of range.
		Else retruns value.
		"""
		if value < format_line[2]:
			self.log.error("%s < %s (min)." % (value, format_line[2]))
			return None
		if value > format_line[3]:
			self.log.error("%s > %s (max)." % (value, format_line[3]))
			return None
		return value

# --------------- CompareFile -------------------------------------------------
	def _readCompareFile(self, compare_file):
		"""
		Read the compare file and returns temperature and delay as lists.
		"""
		compare_values = []
		with open(compare_file, 'rb') as csvfile:
			csvreader = csv.reader(csvfile, delimiter=',')
			for row in csvreader:
				try:
					temperature = 1000.0 / float(row[0])
					temperature = round(temperature, 0) # we do not need decimal places
					time = float(row[1])
					compare_values.append([temperature, time])
				except ValueError:
					pass
		return compare_values

# --------------- Setup and run -----------------------------------------------
	def _setupWorkingDir(self):
		"""
		Prepare working directory for a kiva run.
		"""
		if self.working_dir == None:
			self.log.error("No valid working dir set.")
			return False
		# Delete contents
		for node in os.listdir(self.working_dir):
			if os.path.isdir(os.path.join(self.working_dir, node)):
				shutil.rmtree(os.path.join(self.working_dir, node))
			else:
				os.unlink(os.path.join(self.working_dir, node))
		# Recreate working dir indicator
		open(self.working_dir_indicator, 'a').close()
		# Create Directory containing all input files
		path = os.path.join(self.working_dir, 'run0')
		os.makedirs(path)
		for f in self.kiva_parameter_files:
			if f in self.itapes:
				dst = os.path.join(path, os.path.basename(self.itapes[f].name))
				self.itapes[f].save(dst)
			else:
				src = os.path.join(self.kiva_path, f)
				dst = os.path.join(path, f)
				shutil.copy(src, dst)
		# Create as many copies of it as there are compare_values
		for ii in range(1, len(self.compare_values)):
			shutil.copytree(path, os.path.join(self.working_dir, 'run' + str(ii)))
		# patch temperature in every directory's itape5 file line 230
		for ii in range(0, len(self.compare_values)):
			f = os.path.join(self.working_dir, 'run' + str(ii), 'itape5')
			if not os.path.isfile(f):
				self.log.error("'%s' does not exist." % f)
				return False
			# load file
			with open(f, 'r') as file:
				data = file.readlines()
			# change line
			line = "'tempi',     "
			line += '{0:.1f}'.format(self.compare_values[ii][0]) + '\n'
			data[230 - 1] = line
			# write data back
			with open(f, 'w') as file:
				file.writelines( data )
		return True

	def _collectIgnitionDelay(self):
		"""
		This needs to be called after kiva is run.
		Data from the runXX/T_ign.dat files is collected.
		"""
		self.results = []
		for ii in range(0, len(self.compare_values)):
			f = os.path.join(self.working_dir, 'run' + str(ii), 'T_ign.dat')
			if not os.path.isfile(f):
				self.log.error("'%s' does not exist." % f)
				delay = 0	# probably kiva was killed
				# save log
				log = os.path.join(self.log_dir, str(int(time.time())))
				if not os.path.isdir(log):
					os.makedirs(log)
				shutil.move(os.path.join(self.working_dir, 'run' + str(ii)), log)
				src = os.path.join(self.working_dir, 'run' + str(ii) + '.log')
				des = os.path.join(log, 'run' + str(ii) + '.log')
				os.rename(src, des)
				src = os.path.join(self.working_dir, 'run' + str(ii) + '.error')
				des = os.path.join(log, 'run' + str(ii) + '.error')
				os.rename(src, des)
			else:
				with open(f, 'r') as file:
					delay = float(file.readlines()[0].strip())
			compare = self.compare_values[ii]
			delta = delay - compare[1]
			delta_abs = abs(delta)
			delta_rel = round((delta_abs * 100 / compare[1]), 2)
			self.log.debug("Delay for Temperatur %s: \texpected: %s \tcomputed: %s" % (compare[0], compare[1], delay))
			self.log.debug("Delta: %s \tabs: %s \trelative: %s%%" % (delta, delta_abs, delta_rel))
			self.results.append([delay, compare[1]])

	def run(self, time_out=120):
		"""
		Executes kiva with current parameter set.
		Once for every compare_value.
		"""
		if not self._setupWorkingDir():
			return False
		# Start one kiva process for every folder
		processes = []
		# devnull = open('/dev/null', 'w')
		kiva = os.path.abspath(os.path.join(self.kiva_path, self.kiva_name))
		for ii in range(0, len(self.compare_values)):
			log = os.path.join(self.working_dir, 'run' + str(ii) + '.log')
			log_file = open(log, 'w')
			error = os.path.join(self.working_dir, 'run' + str(ii) + '.error')
			error_file = open(error, 'w')
			d = os.path.join(self.working_dir, 'run' + str(ii))
			p = subprocess.Popen(kiva, cwd=d, stdout=log_file, stderr=error_file)
			processes.append([p, d, True, log_file, error_file])
			self.log.debug("kiva in '%s' spawned." % d)
		# Check for all kiva processes to terminate
		# TODO: add timeout
		all_finished = False
		start_time = time.time()
		while not all_finished:
			all_finished = True
			for p in processes:
				if p[2]:
					if p[0].poll() == 0:
						self.log.debug("kiva in '%s' terminated." % p[1])
						p[2] = False
						p[3].close() # close log file
						p[4].close() # close error file
					else:
						all_finished = False
			# is time up?
			if time.time() - start_time > time_out:
				self.log.warn("Timed out! (%s s)" % time_out)
				for p in processes:
					if p[2]:
						p[0].kill()
						p[3].close() # close log file
						p[4].close() # close error file
						self.log.warn("kiva in '%s' killed!" % p[1])
				all_finished = True
			# do not use up all CPU time
			time.sleep(1)
		# Collect Results
		self._collectIgnitionDelay()
		return True

	def getFitness(self):
		"""
		Call this after calling run.
		This will return a fitness value based on the temperatures computed.
		"""
		score = 0.0
		for value in self.results:
			score += abs(value[0] - value[1])
		score = 1000 / score
		return score

if __name__ == "__main__":
	"""
	Some test code
	"""
	import parameters
	l = Logger()
	l.setLogLevel('debug')
	runner = KivaRunner('../work', '../log', '../ext/Detalierte Mechanismus.csv', parameters.parameter_format, l)
	l.debug("Default Parameter Set: %s" % runner.getParameters())
	runner.run(10)
	l.debug("Fitness: %s" % runner.getFitness())

