#!/bin/bash

while true; do
    sudo nc -ll -p 80 -e /tmp/lb_script_2.sh;
done > /dev/null &

