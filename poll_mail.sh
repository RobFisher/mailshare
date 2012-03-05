#!/bin/bash
# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

# Shell script to poll emails

# loop forever because the Python code still does not catch all exceptions
while [ 1 ]
do
    python poll_mail.py
    sleep 10 # stop us spinning fast if there is a network problem
done
