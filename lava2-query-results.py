#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  incomplete-results.py
#
#  Copyright 2017 Neil Williams <codehelp@debian.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

# pylint: disable=superfluous-parens,missing-docstring,line-too-long
# pylint: disable=wrong-import-order,invalid-name,unused-argument

import sys
import yaml
if sys.version_info < (3, 0):
    import xmlrpclib
else:
    import xmlrpc.client as xmlrpclib
    print("Python 2")

# configuration
USER = 'drio'
TOKEN = 'n90xdlz3z1kmp74sn7i1n9ieua6972m4e2d33castmonqq0lk0z5sypfzqx51rs9hfu09rkfa3201z5ehrkw3ep0gtigymj6itao87qdg26u69shtujd0j6854bozxp8'
QUERY = 'test-myjobs'
QUERY_USER = 'drio'
HOSTNAME = 'eltf-qemu01'
# end configuration

SUBMITTED = 0
RUNNING = 1
COMPLETE = 2
INCOMPLETE = 3
CANCELED = 4
CANCELING = 5

STATUS_CHOICES = (
    (SUBMITTED, 'Submitted'),
    (RUNNING, 'Running'),
    (COMPLETE, 'Complete'),
    (INCOMPLETE, 'Incomplete'),
    (CANCELED, 'Canceled'),
    (CANCELING, 'Canceling'),
)


# main_function
def main(args):
    # change https to http when testing with localhost
    connection = xmlrpclib.ServerProxy("http://%s:%s@%s/RPC2" % (USER, TOKEN, HOSTNAME))
    data = connection.results.run_query(QUERY, 20, QUERY_USER)
    if not data:
        return 0
    print("Job, Type, Message, Time")
    for result in data:
        job_lava = yaml.load(connection.results.get_testcase_results_yaml(result['id'], 'lava', 'job'))[0]
        job_id = job_lava['job']
        logged = job_lava['logged']
        if result['status'] == INCOMPLETE:
            error_type = job_lava['metadata']['error_type']
            msg = job_lava['metadata']['error_msg']
            print("%s, '%s', '%s', '%s'" % (job_id, error_type, msg, logged))
            continue
        elif result['status'] == COMPLETE:
            continue
        print("[%s] %s" % (job_lava['job'], STATUS_CHOICES[int(result['status'])][1]))
    return 0
# end main_function


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
