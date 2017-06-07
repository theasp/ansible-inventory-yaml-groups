#!/usr/bin/python

import argparse
import json
import yaml
import sys
import os.path

def get(data, key, default):
    if key not in data:
        data[key] = default

    return data[key]


def output_list_inventory(data):
    '''
    Output the --list data structure as JSON
    '''

    groups = dict()
    meta = dict()
    groups["_meta"] = meta

    host_vars = dict()
    meta["hostvars"] = host_vars

    for group_name, data_group in get(data, "groups", dict()).iteritems():
        new_group = get(groups, group_name, dict())
        if "vars" in data_group:
            get(new_group, "vars", dict()).update(data_group["vars"])
    
    for host_name, host in get(data, "hosts", dict()).iteritems():
        if "vars" in host:
            host_vars[host_name] = host["vars"]
        
        for group_name in get(host, "groups", list()):
            group = get(groups, group_name, dict())
            group_hosts = get(group, "hosts", list())
            group_hosts.append(host_name)

            
    print json.dumps(groups)


def find_host(data, host_name):
    '''
    Find the given variables for the given host and output them as JSON
    '''

    host = get(hosts, host_name, dict())
    host_vars = get(host, "vars", dict())
    print json.dumps(host_vars)

def main():
    '''
    Output dynamic inventory as JSON from statically defined data structures
    '''

    # Argument parsing
    parser = argparse.ArgumentParser(description="Ansible dynamic inventory")
    parser.add_argument("--list", help="Ansible inventory of all of the groups",
                        action="store_true", dest="list_inventory")
    parser.add_argument("--host", help="Ansible inventory of a particular host", action="store",
                        dest="ansible_host", type=str)

    cli_args = parser.parse_args()
    list_inventory = cli_args.list_inventory
    ansible_host = cli_args.ansible_host

    data = yaml.load(sys.stdin)

    if list_inventory:
        output_list_inventory(data)

    if ansible_host:
        find_host(data, ansible_host)


if __name__ == "__main__":
    main()
