#!/usr/bin/python
from optparse import OptionParser
import time
import urllib2
import yaml
import xmlrpclib
import xml.dom.minidom
import xml.etree.cElementTree as XMLContent
import sys
import random
import string

def main(argv):
    # Process command line script arguments
    opt_parser = OptionParser()
    opt_parser.add_option("-i", "--instance", dest="lavainstance",
                        action="store", type="string",
                        help="The name or IP of the LAVA2 host you want to use",
                        metavar="lavainstance")
    opt_parser.add_option("-j", "--job-id", dest="job_id",
                        action="store", type="string",
                        help="ID of the LAVA2 job you want to extract results from",
                        metavar="job_id")
    opt_parser.add_option("-o", "--output-dir", dest="output_dir",
                        action="store", type="string",
                        help="Provide the path to a folder were the XML will be exported. It MUST end with /")
    opt_parser.add_option("-f", "--file-name", dest="filename",
                        action="store", type="string",
                        help="Supply the full path to the XML file you wish to write (WARNING: Overrides -o!)")
    opt_parser.add_option("-p", "--pretty-xml", dest="prettify",
                        action="store_true", 
                        help="Tell the script to print out a more pretty version of the XML")
    opt_parser.add_option("-d", "--wait-delta", dest="delta",
                        action="store", type="int",
                        help="Specify the sleep time used when querying the LAVA job status")
    opt_parser.add_option("-u", "--lava-url", dest="full_url",
                        action="store", type="string",
                        help="Give the full path of the LAVA2 job. OVERRIDES -i and -j!! (used as an alternative for ELTF)")
    (options, args) = opt_parser.parse_args()

    # Some script arguments are mandatory. We need to make this clear to the user.
    if not options.lavainstance:
        if options.full_url:
            print "Full LAVA URL provided, skipping -i ..."
            options.lavainstance = options.full_url.split('/')[2]
        else:
            opt_parser.error('No LAVA instance name or IP specified. Use -h for details.')
            sys.exit(2)

    if not options.job_id:
        if options.full_url:
            print "Full LAVA URL provided. Skipping -j ..."
        else:
            opt_parser.error('No LAVA job ID specified. Use -h for details.')
            sys.exit(2)

    if not options.output_dir:
        if options.filename:
            print "Will write XML contents to %s ..." % options.filename
        else:
            opt_parser.error('No output dir or specific filename specified. See -h for details.')
            sys.exit(2)

    ######################
    #      MAIN FLOW     #
    ######################

    if options.full_url:
        options.job_id = options.full_url.split('/')[-1]

    if options.prettify:
        PRETTIFY = options.prettify

    # This is the only entry point.
    get_job_status(options)
    generate_xml_results(fetch_test_suites(options), options) 

def fetch_test_suites(options):
    """Build a list of all test suites ran by the specified job"""
    # For now, it seems that test suites defined by the user start with
    # "0_", so we fetch the results in YAML format, parse the content and extract
    # only names that start with this preffix.

    # The script that processes V1 results takes the full URL as an argument.
    # This script is built around the idea that the job ID should be solely 
    # submitted. But, as a workaround, we give the option to deal with the full URL
    # just to keep things compatible (and, of course, due to the time constraints).
    # Basically, we get the old-style V1 URL that ends with the job ID
    suites = yaml.load(
                urllib2.urlopen('http://%s/results/%s/yaml' % 
                            (options.lavainstance, options.job_id)
                            ).read())

    # A place to store the name of all testsuites we found
    executed_test_suites = []
    for t_suite in suites:
        if t_suite["name"].startswith("0_"):
            executed_test_suites.append(t_suite["name"])
    return executed_test_suites

def get_job_status(options):
    """Poll the LAVA2 server in order to get the current status of the specified
    job."""
    # TODO: remove hardcoded credentials
    username = "jenkins"
    token = "7qtcpezuyf7l805786od3mn6p6q5hlbpc7mjnoms561zahlj8pel62tafts3e5zl00wusj0ycggjpz7zumgmzify6jiamqf20do4xn2ee9qf0gm4zaonhioe59tzh9kn"
    lava_server_conn = xmlrpclib.ServerProxy("http://%s:%s@%s/RPC2" % (username, token, options.lavainstance))
    while True:
        job_status = lava_server_conn.scheduler.job_status(options.job_id)["job_status"]
        
        if job_status == "Running":
            print("Job %s is still running. Waiting..." % options.job_id)
            time.sleep(options.delta)
            continue
        if job_status == "Submitted":
            print("Job %s is in the queue. Waiting..." % options.job_id)
            time.sleep(options.delta)
            continue
        if job_status == "Complete":
            print("Job %s has completed!" % options.job_id)
            return True
        else:
            print("Job %s was %s in LAVA!" % (options.job_id, job_status))
            sys.exit(2)


def fetch_test_results(test_suite_name, options):
    """Used for obtaining the test results from the server."""
    url = 'http://%s/results/%s/%s/yaml' % (options.lavainstance, options.job_id, test_suite_name)

    test_results = yaml.load(urllib2.urlopen(url).read())
    return test_results

def generate_random_string(size=6, chars=string.ascii_uppercase + string.digits):
    """A simple utility method for generating random strings"""
    return ''.join(random.choice(chars) for _ in range(size))

def generate_xml_results(executed_test_suites, options):
    """Converts the provided info into a JUnit-compatible format
    and returns the XML tree element object."""

    # We keep the count for how many tests were run, how many failed
    # and how many were skipped
    test_failures = 0
    tests_skipped = 0
    test_counter = 0

    # Create the root XML node 
    root = XMLContent.Element("testsuites")

    for test_suite in executed_test_suites:
        # Create a new subnode with the test suite's name
        t_suite = XMLContent.SubElement(root, "testsuite")
        t_suite.set("name", test_suite)

        # A place to store the test results for the current test suite
        results_dictionary = fetch_test_results(test_suite, options)

        # Go through each test case result collection from the dictionary 
        # and extract the necessary information
        for test_case in results_dictionary:
            # Each test case will have it's own element
            t_case = XMLContent.SubElement(t_suite, "testcase")
            t_case.set("name", test_case["name"])


            # If the test failed, mark it as so according to JUnit formatting
            # conventions. Also, increase the test_failures counter.
            if test_case["result"] == "fail":
                failed = XMLContent.SubElement(t_case, "failure")
                # TBD - get a message from LAVA and set it as the
                # "message" attribute
                test_failures += 1

            # If the test case was skipped, mark it as skipped and increase the 
            # tests_skipped counter
            if test_case["result"] == "skip":
                failed = XMLContent.SubElement(t_case, "skipped")
                tests_skipped += 1

            # Increase the total test_counter each time we finish processing a 
            # test result
            test_counter += 1

        # Use the counters we've set up at the beginning to set XML attributes
        # for the "<testsuite> element"
        t_suite.set("tests", str(test_counter))
        t_suite.set("skipped", str(tests_skipped))
        t_suite.set("failures", str(test_failures))    

    # Build the XML tree
    tree = XMLContent.ElementTree(root)
    # Write the contents to a temporary file or to the final file, in case
    # the "-pretty" script argument was not passed
    
    final_file_path = ""

    if options.output_dir:
        final_file_path = options.output_dir + generate_random_string() + '.xml'
    else:
        final_file_path = options.filename 

    if options.prettify:
        tempXML = "./" + generate_random_string() + '.xml'
        tree.write(tempXML)
        xml_parser = xml.dom.minidom.parse(tempXML)
        xml_content_as_string = xml_parser.toprettyxml()
        file_handle = open(final_file_path, 'w')
        file_handle.write(xml_content_as_string)
        file_handle.close()
    else:
        file_to_write = final_file_path
        tree.write(file_to_write)

    print "Successfully generated test results XML: %s" % final_file_path

if __name__ == "__main__":
    main(sys.argv[1:])

