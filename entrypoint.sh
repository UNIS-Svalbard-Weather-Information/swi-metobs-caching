#!/bin/bash

# Check if the conditions are met
if [ "$SWI_INSTANCE_SERVE_ONLY" = "false" ] && [ "$SWI_DOCKER_INSTANCE" = "true" ]; then
    # Copy the cron file to the cron.d directory
    cp /app/cron/swi-cron /etc/cron.d/swi-cron

    # Give execution rights on the cron file
    chmod 0644 /etc/cron.d/swi-cron

    # Apply cron job
    crontab /etc/cron.d/swi-cron

    # Create the log file to be able to run tail
    touch /var/log/cron_swi_seaice.log
    touch /var/log/cron_swi_metdata.log
    touch /var/log/cron_swi_avalanche.log

    printenv > /etc/environment
    
    # Start cron in the background
    cron
fi

# Start Gunicorn
exec gunicorn -w 4 -b 0.0.0.0:5000 run:application