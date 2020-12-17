#!/bin/sh

BRANCH="$(/usr/bin/git branch|/bin/grep \*|/usr/bin/awk {'print $2'})"

#IMAGES="server db"
IMAGES="server"

for IMAGE in ${IMAGES}; do
  /usr/bin/docker build \
    -t ${IMAGE}:${BRANCH} \
    -f ./docker/${IMAGE}/Dockerfile \
    ./docker/${IMAGE}/.
done
