#!/bin/bash

while true; do
    # Get the current minute
    CURRENT_MINUTE=$(date +%M)

    if [ "$CURRENT_MINUTE" -eq "00" ] ; then
        python3 ./main.py
	sleep 60
    else
        # Wait for 60 seconds before the next check
        echo $CURRENT_MINUTE
        sleep 60
    fi
done

