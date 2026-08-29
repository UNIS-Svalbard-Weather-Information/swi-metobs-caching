#!/bin/sh

# Check if DOCKER-CRON is set
if [ -n "$DOCKER_CRON" ]; then
    # Run the caching job once (with instance check)
    /swi/run-cron.sh

    # Add an alias for run-cron
    echo "alias run-cron='/swi/run-cron.sh'" >> ~/.bashrc
    echo "Container is now waiting for commands. You can use 'run-cron' to re-run the script."

    # Keep the container running, but respect termination signals
    exec sh -c "sleep infinity & wait"
else
    # Default behavior: just run the caching job
    exec /swi/run-cron.sh
fi
