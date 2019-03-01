#!/usr/bin/env python3
import argparse
import asyncio
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

'''
This script is used to act as an HTTP end-point for load-balancers
and return a response based on one or more commands. If
all commands execute successfully (return an exit code of 0) then
an HTTP 200 response is returned. Any other result will return an HTTP 500
response.

A kill-switch file (/etc/lbhealth.kill) can be used to disable the commands
and instantly return a failed result.

The script can be configured to run behind a SystemD socket, e.g.:

# /etc/systemd/system/lbhealth.socket
[Unit]
Description=LB health check

[Socket]
ListenStream=0.0.0.0:9000
Accept=yes

[Install]
WantedBy=sockets.target

# /etc/systemd/system/lbhealth@.service
[Unit]
Description=LB health check server
Requires=lbhealth.socket

[Service]
Type=simple
WorkingDirectory=/usr/local/bin
ExecStart=/usr/local/bin/lbhealth.py %i
StandardInput=socket
StandardError=journal
TimeoutStopSec=5
PrivateTmp=yes

[Install]
WantedBy=multi-user.target

# /etc/lbhealth.json
[
	"/bin/true",
	"/usr/lib/nagios/plugins/check_disk"
]
'''



@asyncio.coroutine
def run_command(shell_command):
	'''
	Use asyncio to execute a check.
	'''
	p = yield from asyncio.create_subprocess_shell(shell_command,
	                                               stdout=asyncio.subprocess.PIPE,
	                                               stderr=asyncio.subprocess.STDOUT)
	stdout, stderr = yield from p.communicate()
	exit_code = p.returncode
	return (
		stdout,
		stderr,
		exit_code
	)



def run_checks(checks):
	'''
	Asynchronously execute all the checks and return the results
	'''

	# Get a new asyncio loop
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)

	tasks = []
	for check in checks:
		tasks.append(run_command(check))

	# Get all the futures
	commands = asyncio.gather(*tasks)

	# Wait for all the futures to finish processing
	results = loop.run_until_complete(commands)
	loop.close()

	return results



class HTTPRequest(BaseHTTPRequestHandler):
	def __init__(self, stdin):
		self.client_address = '127.0.0.1' # Manually set the client address to prevent errors
		self.rfile = stdin
		self.wfile = sys.stdout
		self.raw_requestline = self.rfile.readline()
		self.parse_request()


	def do_GET(self, checks=[]):
		results = run_checks(checks)

		logging.debug(b'lbhealth-service: got results: %s', str(results))

		# If any check returned an exit code greater than zero, the check failed
		failed = True if len(results) > 0 and max([result[2] for result in results]) > 0 else False

		if failed:
			self.send_response(500)
		else:
			self.send_response(200)

		self.send_header("Content-type", "text/plain; charset=utf-8")
		self.end_headers()

		if self.path == '/verbose' or failed:
			self.wfile.write(
				bytes(
					'\r\n\r\n'.join([
						stdout.decode().strip() for stdout, stderr, exit_code in results
					])
					, 'UTF-8'
				)
			)
			self.wfile.write(b"\r\n")
		return



if __name__ == "__main__":
	argp = argparse.ArgumentParser(description=__doc__, add_help=False)
	argp.add_argument('instance',
	                  default='0',
	                  help='The systemd instance')
	argp.add_argument('-c', '--config',
	                  default='/etc/lbhealth.json',
	                  help='JSON file with the list of check commands')
	argp.add_argument('-k', '--kill-switch',
	                  default='/etc/lbhealth.kill',
	                  help='If file exists, script will return a fail result')
	argp.add_argument('-l', '--log-level',
	                  default='ERROR',
	                  help="Console logging log level. One of 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'. Default: 'CRITICAL'.")
	args = argp.parse_args()

	logging.basicConfig(level=getattr(logging, args.log_level))

	# Use the stdin and stdout underlying binary buffer
	# https://docs.python.org/3.1/library/sys.html#sys.stdin
	sys.stdin = sys.stdin.detach()
	sys.stdout = sys.stdout.detach()

	# The connected socket is duplicated to stdin/stdout
	request = HTTPRequest(sys.stdin)
	logging.debug(request)

	# If the killswitch is required, immediately return a failed result
	if os.path.isfile(args.kill_switch):
		logging.info(b'Found kill-switch file')
		request.send_response(500, 'Kill Switch')
		request.send_header("Content-type", "text/plain; charset=utf-8")
		request.end_headers()
		exit()

	# The configuration file should be a JSON list
	# of strings, one for each check to execute
	try:
		with open(args.config, 'r') as fp:
			checks = json.load(fp)
	except IOError as e:
		logging.error(bytes(e, 'UTF-8'))
		checks = []

	# Perform the checks and return a response
	request.do_GET(checks)
