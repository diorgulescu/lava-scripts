import os
import sys
import string
import random
import re
# Since this module could be missing on some machines, it's best that we display
# a more explicit error, with details on how to solve this issue.
try:
        import configparser
except ImportError:
        print "ERROR: The configparser module could not be found on this machine.\nIn order to run this script, you need to install the module. Make sure you\nhave administrative permissions on this machine beforehand.\nExample: pip install configparser\n"
        sys.exit(2)

class BootCommandExtractor:
	"""Implements the functionality for parsing the given board config file and extract the boot commands it was requested.
	
	The entry-point for this class is the extractCommands() method. This is the only one that should be directly invoked, since it goes through the whole flow.
	All other methods are basically helper methods for extractCommands(). Nevertheless, if one finds any
	of them useful, they may be directly invoked, provided the appropriate arguments are supplied.
	"""
	
	def __init__(self, deviceFile, outputDir):
		"""Object constructor
		
		Keyword arguments:
		deviceFile -- The ABSOLUTE path to the device file we want to use
		outputDir  -- The ABSOLUTE path to the directory in which we want to store the extracted commands
		"""
		self.config = configparser.ConfigParser()
		self.suppliedDeviceFile = deviceFile
		self.preparedFilePath = ""
		self.textOutputDir = outputDir
		self.deviceName = os.path.splitext(deviceFile)[0]
		self._resultingFiles = []

	def __del__(self):
		"""Object destructor
		
		In our context, we just perform a small cleanup operation, erasing the temporary files created
		at runtime.
		"""
		os.unlink(self.preparedFilePath)
		
	def extractCommands(self, commandsToExtract):
		"""Extracts the Boot Commands and exports them into a separate text file
		
		Keyword arguments:
		commandsToExtract -- comma-separated values comprising an enumeration of the commands we wish
		to extract. Example: "boot_cmds,boot_cmds_ramdisk,boot_cmds_nfs" without any additional whitespaces
		"""
		
		# First, we "prepare" the given device file
		self.prepareConfigFile()
		
		# Once done, load the "parsable" version
		self.loadClonedDeviceFile()
		
		# Build a list of all command types we're going to extract
		_commandsToProcess = commandsToExtract.split(',')

		# Extract each specified command type 
		for commandType in _commandsToProcess:
			self._resultingFiles.append(self.writeOutCommands(commandType))
		
		return self._resultingFiles
			
	# HELPER METHODS 
	def prepareConfigFile(self):
		"""Creates a temporary copy of the provided file and makes it readable by the 
		ConfigParser() module"""
		
		with open(self.suppliedDeviceFile) as originalDeviceFile:
			# Create a new temporary file and give it a randomly generated name
			__tmpFPath = self.deviceName + self.randomString()

			with open(__tmpFPath, "w") as clonedDeviceFile:
				# Add the "default" section 
				clonedDeviceFile.write("[default]\n")
				for line in originalDeviceFile:
					clonedDeviceFile.write(line) 
				self.preparedFilePath = clonedDeviceFile.name
		
	def loadClonedDeviceFile(self):
		"""Loads the prepared device file into the ConfigParser instance"""
		self.config.read(self.preparedFilePath)
	
	def randomString(self, size=6, chars=string.ascii_uppercase + string.digits):
		"""Generate a random string which will be used as the filename for the temporary device file"""
		return ''.join(random.choice(chars) for _ in range(size))
	
	def writeOutCommands(self, cmdType):
		"""Go through the prepared device file and extract the commands matching the specified category"""
		_cmds = ""
		_ip_addr_regex = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
		_ip_substitute = "<TFTP Server IP>"
		_outputFileName = self.textOutputDir + cmdType + ".txt"
		
		if self.config.has_option('default', cmdType):
			_cmds = self.config['default'][cmdType].split('\n')
			#print "[DEBUG] _cmds: "
			#print _cmds

			with open(_outputFileName, 'w') as _outputFileName:
				for command in _cmds:
                                        #+--------------------------------------------+
                                        # Additional text processing can be added here|
                                        #+--------------------------------------------+
                                        # TO DO: maybe, in the future, externalize this part
                                        # so that what needs to be replaced is specified in an
                                        # additional INI-type file, thus eliminating the need
                                        # to alter the code whenever additional rules have to be
                                        # introduced

                                        # Perform additional processing ONLY if the fetched line
                                        # is NOT empty
                                        if command:
                                                # Replace any existing IP address
                                                command = re.sub(_ip_addr_regex, _ip_substitute, command)

                                                # Replace "{KERNEL}"
                                                if "{KERNEL}" in command:
                                                        command = command.replace("{KERNEL}", "</path/to/kernel_file>")

                                                # Replace "{SERVER_IP}"
                                                if "{SERVER_IP}" in command:
                                                        command = command.replace("{SERVER_IP}", "<NFS Server IP>")

                                                # Replace "{DTB}"
                                                if "{DTB}" in command:
                                                        command = command.replace("{DTB}", "</path/to/dtb_file>")

						if "," in command:
							command = command.replace(",", "")

                                                # Finally, write out the line
                                                _outputFileName.write(command + "\n")

					print "INFO: Successfully extracted " + cmdType  + " commands"
                                return _outputFileName


		else:	
			print "INFO: The specified boot command type could not be found: " + cmdType + ". Skipping..."
		
		
		




