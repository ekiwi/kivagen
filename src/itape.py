
import os, re

class ITapeFile():
	"""
	Represents an instance of the itapeERC kiva settings file.
	"""

	def __init__(self, name, logger=None):
		if logger == None:
			self.log = Logger()
		else:
			self.log = logger
		self._open(name)

	def _open(self, name):
		line_format = re.compile(r"(?P<number>[\.e\+\-0-9]+)\s+!(?P<comment>[\S ]+)")
		decimal_places = re.compile(r"[\+\-0-9]+.(?P<dec>[0-9]+)")
		self.name = name
		if not os.path.isfile(self.name):
			self.log.error("'%s' not found." % self.name)
			return
		self.values = []
		f = open(self.name, "r")
		lines = f.readlines()
		f.close()
		# find value width == spaces untill !
		self.width = lines[0].find('!')
		ii = 0
		for line in lines:
			ii = ii + 1
			if line.find('!') >= 0 and line.find('!') != self.width:
				self.log.warn("In line %s: line.find('!') != self.width; %s != %s"
					% (ii, line.find('!'), self.width))
		for line in lines:
			match = line_format.search(line)
			if match:
				number = match.group('number')
				# number_str = number
				comment = match.group('comment')
				# try to generate format string that matches input format
				if '.' in number:	# if this is not an integer
					# Count decimal places
					match = decimal_places.search(number)
					if match:
						places = len(match.group("dec"))
					else:
						places = 0
					if 'e' in number:
						format = '{:.%se}' % places
					else:
						format = '{:.%sf}' % places
					number = float(number)
				else:
					format = '{:d}'
					number = int(number)
				self.values.append([number, comment, format])
				# number_str_new = format.format(number).replace('+', '')
				# if number_str != number_str_new:
				#	self.log.warn("%s != %s" % (number_str, number_str_new))
			else:
				self.values.append([line])

	def getId(self, name):
		"""
		Returns the id of the first value with matching comment name found.
		Returns -1 if no value is found.
		"""
		ii = 0
		for value in self.values:
			if len(value) > 1 and value[1] == name:
				return ii
			ii = ii + 1
		return -1

	def getValue(self, id):
		return self.values[id][0]

	def setValue(self, id, value):
		if isinstance(self.values[id][0], int):
			self.values[id][0] = int(value)
		elif isinstance(self.values[id][0], float):
			self.values[id][0] = float(value)
		else:
			self.log.warn("Could not write %s to self.values[%s)." % (value, id))

	def save(self, name):
		"""
		Save values to itape file that will have the same format as the
		file that the values were loaded from.
		"""
		f = open(name,'w')
		for value in self.values:
			if len(value) == 3:
				line = value[2].format(value[0]).replace('+', '')
				line = line.ljust(self.width) + '!' + value[1]
			else:
				line = value[0]
			f.write(line + '\n')
		f.close()



