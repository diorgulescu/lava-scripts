import os
import sys
sys.path.insert(1,os.path.dirname(os.path.abspath(__file__)))
from lib import bootCommandExtractor
from optparse import OptionParser


def main(argv):
	deviceFile = ''
	outputDir = ''
	commandTypes = ''
	processCommands = ''
	
	parser = OptionParser()
	parser.add_option("-d", "--dev-file", dest="devfile",
			action="store", type="string",
			help="supply a device file to parse", metavar="FILE")
	parser.add_option("-o", "--out-dir", dest="outdir",
			action="store", type="string",
			help="supply a device file to parse", metavar="OUTDIR")
	parser.add_option("-c", "--commands", dest="commands",
			action="store", type="string",
			help="specify (as comma separated vals) which command types to extract. Ex: boot_cmds,boot_cmds_nfs,boot ", metavar="CMDS")

	(options, args) = parser.parse_args()

	if not options.devfile:   # if filename is not given
		parser.error('No device file was supplied. Use -h for more instructions.')
		sys.exit(2)
	
	if not options.outdir:   # if filename is not given
		parser.error('The output directory has not been specified.Use -h for more instructions.')
		sys.exit(2)
	
	# If not command types are specified, extract all.
	if not options.commands:
		options.commands="boot_cmds,boot_cmds_nfs,boot_cmds_ramdisk"

	processCommands = bootCommandExtractor.BootCommandExtractor(options.devfile, options.outdir)	
	filelist = processCommands.extractCommands(options.commands)
	if not filelist:
		print "FAILED: Errors enountered.\n"
		sys.exit(2)
	else:
		print "\n\n\nSUCCESS: All operations were completed successfully\n"
		print "===========\nThe following files contain the commands you requested:\n"
		for resultedFile in filelist:
			if resultedFile:
				print "* " + resultedFile.name

		print "\n\nAdditional info:"
		print "-----------------------------"
		print '* The device file you provided: ' + options.devfile
		print '* Output dir: ' + options.outdir
		print "=============================\n"

	
if __name__ == "__main__":
	main(sys.argv[1:])
