#!/bin/bash

while true; do
    sudo nc -ll -p 80 -e /tmp/lb_script_3.sh;
done > /dev/null &

