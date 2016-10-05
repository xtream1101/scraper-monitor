#!/bin/bash
# Simple script to increment the version number and push to docker hub

for i in "$@"
do
    case $i in
        -M|--major)
        UPDATE_MAJOR=1
        shift
        ;;
        -m|--mid)
        UPDATE_MID=1
        shift
        ;;
        -H=*|--docker-host=*)
        export DOCKER_HOST="${i#*=}"
        shift
        ;;
        *)
        # unkown option
        echo "usage: deploy.sh [options]
-M | --major: increment major version not minor
-m | --mid: increment middle version not minor
-H | --docker-host <hostname:[port]>: use this docker host
Default behavior is to increment the minor version number"
        ;;
    esac
done

MAJOR=$(cat VERSION | cut -f1 -d.)
MID=$(cat VERSION | cut -f2 -d.)
MINOR=$(cat VERSION | cut -f3 -d.)

if [ -n "$UPDATE_MAJOR" ]; then
    MINOR=0
    MID=0
    MAJOR=$(expr $MAJOR + 1)
elif [ -n "$UPDATE_MID" ]; then
    MINOR=0
    MID=$(expr $MID + 1)
else
    MINOR=$(expr $MINOR + 1)
fi

echo "New version $MAJOR.$MID.$MINOR"
echo "$MAJOR.$MID.$MINOR" > VERSION

git add VERSION
git commit -m "autoinc version to $MAJOR.$MID.$MINOR"
git tag -a "$MAJOR.$MID.$MINOR" -m "version $MAJOR.$MID.$MINOR"
git push
git push origin --tags

docker build -t "scraper-monitor" -t "xtream1101/scraper-monitor:$MAJOR.$MID.$MINOR" -t "xtream1101/scraper-monitor:latest" .
docker push "xtream1101/scraper-monitor:$MAJOR.$MID.$MINOR"
docker push "xtream1101/scraper-monitor:latest"
