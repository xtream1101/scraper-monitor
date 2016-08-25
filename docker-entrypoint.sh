#!/bin/sh
set -e

cmd=$1

if [ "$cmd" = 'manage' ]; then
    shift
    python3 /src/manage.py $@

elif [ $# == 0 ]; then

    python3 /src/manage.py db migrate
    python3 /src/main.py

else

    exec $@

fi
