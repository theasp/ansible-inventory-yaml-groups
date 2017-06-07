#!/bin/bash

set -e

DIR=$(dirname $0)

cd $DIR
echo "$(date +%F-%T) Starting: $@" >> /tmp/hosts-log.txt
exec ./hosts.py "$@" < hosts.yml
