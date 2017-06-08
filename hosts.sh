#!/bin/bash

set -e

DIR=$(dirname $0)

exec $DIR/hosts.py "$@" < ${ANSIBLE_HOSTS_YML:-$DIR/hosts.yml}
