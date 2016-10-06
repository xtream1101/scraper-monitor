#!/bin/sh
set -e

cmd=$1

if [ "$cmd" = 'manage' ]; then
    shift
    python3 /src/manage.py $@

elif [ $# == 0 ]; then

    # Copy custom env
    python3 /src/manage.py copy_env
    # Create migrations if needed
    python3 /src/manage.py db migrate
    # Apply the migrations
    python3 /src/manage.py db upgrade
    # Start the server
    python3 /src/main.py

else

    exec $@

fi
