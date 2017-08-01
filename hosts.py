#!/usr/bin/python

import argparse
import json
import yaml
import os
import sys

def get(d, key, default):
    if key in d:
        return d[key]
    else:
        return default

def get_in(d, keys, default):
    for key in keys:
        if key in d:
            d = d[key]
        else:
            return default
    return d

# Pointless..
#def assoc(d, key, value):
#    d[key] = value

def assoc_in(d, keys, value):
    for key in keys[:-1]:
        if key not in d:
            d[key] = dict()
        d = d[key]

    d[keys[-1]] = value

def update_in(d, keys, update_fn):
    value = get_in(d, keys, dict())
    assoc_in(d, keys, update_fn(value))

def update(d, key, update_fn):
    d[key] = update_fn(get(d, key, dict()))

def process_hosts(groups, data):
    for host_name, data_host in get(data, "hosts", dict()).iteritems():
        if "vars" in data_host:
            host_vars = get_in(groups, ["_meta", "hostvars", host_name], dict())
            host_vars.update(get(data_host, "vars", dict()))
            assoc_in(groups, ["_meta", "hostvars", host_name], host_vars)

        for group_name in get(data_host, "groups", list()):
            group_hosts = get_in(groups, [group_name, "hosts"], list())
            group_hosts.append(host_name)
            assoc_in(groups, [group_name, "hosts"], group_hosts)

    return groups

def process_groups(groups, data):
    #print(json.dumps(groups))
    for group_name, data_group in get(data, "groups", dict()).iteritems():
        group_hosts = get_in(groups, [group_name, "hosts"], list())
        group_vars = get_in(groups, [group_name, "vars"], dict())

        group_hosts += get(data_group, "hosts", list())

        group_vars.update(get(data_group, "vars", dict()))

        for include_name in get(data_group, "include", list()):
            group_hosts += get_in(groups, [include_name, "hosts"], list())

        for require_name in get(data_group, "require", list()):
            require_hosts = get_in(groups, [require_name, "hosts"], list())
            group_hosts[:] = [host_name for host_name in group_hosts if host_name in require_hosts]

        for exclude_name in get(data_group, "exclude", list()):
            exclude_hosts = get_in(groups, [exclude_name, "hosts"], list())
            group_hosts[:] = [host_name for host_name in group_hosts if host_name not in exclude_hosts]

        if len(group_hosts) > 0:
            assoc_in(groups, [group_name, "hosts"], group_hosts)

        if len(group_vars) > 0:
            assoc_in(groups, [group_name, "vars"], group_vars)

    return groups

def make_groups(data):
    groups = dict()
    meta = dict()
    groups["_meta"] = meta

    process_hosts(groups, data)
    process_groups(groups, data)

    for group_name, group in groups.iteritems():
        update(group, "hosts", lambda hosts: sorted(set(hosts)))

    meta.pop("hosts")
    return groups

def output_list_inventory(data):
    '''
    Output the --list data structure as JSON
    '''
    print json.dumps(make_groups(data))

def find_host(data, host_name):
    '''
    Find the given variables for the given host and output them as JSON
    '''

    print json.dumps(get_in(data, ["hosts", host_name, "vars"], dict()))

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
    parser.add_argument("--file", help="Inventory file", action="store",
                        dest="file", type=str)

    cli_args = parser.parse_args()
    list_inventory = cli_args.list_inventory
    ansible_host = cli_args.ansible_host
    inventory_file = cli_args.file

    if not inventory_file:
        if "ANSIBLE_HOSTS_YML" in os.environ:
            inventory_file = os.environ["ANSIBLE_HOSTS_YML"]

    if not inventory_file:
        inventory_file="hosts.yml"
            
    try:
        with open(inventory_file, 'r') as stream:
            data=yaml.load(stream)
            if list_inventory:
                output_list_inventory(data)

            if ansible_host:
                find_host(data, ansible_host)

    except Exception as exc:
        print(exc)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
