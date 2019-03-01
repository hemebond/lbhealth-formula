# lbhealth-formula #

This Salt formula sets up a SystemD socket as an HTTP end-point for load-balancers check requests.

This script is used to act as an HTTP end-point for load-balancers and return a response based on one or more commands. If all commands execute successfully (return an exit code of 0) then an HTTP 200 response is returned. Any other result will return an HTTP 500 response.

## Checks ##

When an HTTP request is received (`http://localhost:9000/`) the configuration file (`/etc/lbhealth.json`) will be read and each command in the file will be executed. If any of the commands return an exit code greater than zero, the script will return a 500 HTTP error.

## Kill-Switch ##

The existence of a kill-switch file (`/etc/lbhealth.kill`) can be used to disable the commands and instantly return a failed result.

