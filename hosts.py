#!/usr/bin/python

import argparse
import json
import yaml
import sys
import os.path

def get(d, key, default):
    if key in d:
        return d[key]
    else:
        return default

def output_list_inventory(data):
    '''
    Output the --list data structure as JSON
    '''

    groups = dict()
    meta = dict()
    groups["_meta"] = meta

    host_vars = dict()
    meta["hostvars"] = host_vars

    for host_name, data_host in get(data, "hosts", dict()).iteritems():
        if "vars" in data_host:
            this_host_vars = get(host_vars, host_name, dict())
            this_host_vars.update(data_host["vars"])
            host_vars[host_name] = this_host_vars

        for group_name in get(data_host, "groups", list()):
            group = get(groups, group_name, dict())
            group_hosts = get(group, "hosts", list())
            group_hosts.append(host_name)
            group["hosts"] = group_hosts
            groups[group_name] = group

    #print(json.dumps(groups))
    for group_name, data_group in get(data, "groups", dict()).iteritems():
        group = get(groups, group_name, dict())
        group_hosts = get(group, "hosts", list())
        group_vars = get(group, "vars", dict())

        if "hosts" in data_group:
            group_hosts += data_group["hosts"]

        if "vars" in data_group:
            group_vars.update(data_group["vars"])

        if ("include" in data_group and isinstance(data_group["include"], list)):
            for include_name in data_group["include"]:
                include_group = get(groups, include_name, dict())
                include_hosts = get(include_group, "hosts", list())
                group_hosts += include_hosts

        if "require" in data_group:
            for require_name in data_group["require"]:
                require_group = get(groups, require_name, dict())
                require_hosts = get(require_group, "hosts", list())
                group_hosts.extend(require_hosts)

        if "exclude" in data_group:
            for exclude_name in data_group["exclude"]:
                exclude_group = get(groups, exclude_name, dict())
                exclude_hosts = get(exclude_groups, "hosts", list())
                group_hosts[:] = [host_name for host_name in group_hosts if host_name not in exclude_hosts]

        group["hosts"] = group_hosts
        if len(group_vars) > 0:
            group["vars"] = group_vars
        groups[group_name] = group

    for group_name, group in groups.iteritems():
        if 'hosts' in group:
            group["hosts"] = sorted(set(group["hosts"]))

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
