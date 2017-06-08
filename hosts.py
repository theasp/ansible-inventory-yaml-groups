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

    for host_name, host in get(data, "hosts", dict()).iteritems():
        if "vars" in host:
            host_vars[host_name] = host["vars"]

        for group_name in get(host, "groups", list()):
            group = get(groups, group_name, dict())
            group_hosts = get(group, "hosts", list())
            group_hosts.append(host_name)

    for group_name, data_group in get(data, "groups", dict()).iteritems():
        new_group = get(groups, group_name, dict())
        hosts = get(new_group, "hosts", list())

        if "hosts" in data_group:
            hosts.append(data_group["hosts"])

        if "vars" in data_group:
            get(new_group, "vars", dict()).update(data_group["vars"])

        if "children" in data_group:
            get(new_group, "children", list()).append(data_group["children"])

        if "include" in data_group:
            for include_name in data_group["include"]:
                include_group = get(groups, include_name, dict())
                hosts.extend(get(include_group, "hosts", list()))

        if "require" in data_group:
            for require_name in data_group["require"]:
                require_group = get(groups, require_name, dict())
                require_hosts = get(require_group, "hosts", list())
                hosts[:] = [host_name for host_name in hosts if host_name in require_hosts]

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
