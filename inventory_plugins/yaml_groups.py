from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    inventory: yaml_groups
    short_description: Uses a specifically YAML file as inventory source.
    description:
        - Alternative YAML formatted inventory for Ansible.
        - Allows you to to assign groups to hosts as well as hosts to groups
        - Easily make new groups that are supersets and subsets of other groups.
    notes:
        - To function it requires being whitelisted in configuration.
    options:
        yaml_extensions:
            description: list of 'valid' extensions for files containing YAML
            type: list
            default: ['.yaml', '.yml', '.json']
    url:
'''
EXAMPLES = '''
---
groups:
  app1-prod:
    include:
      - app1
    require:
      - prod

  app1-dev:
    include:
      - app1
    require:
      - prod

  app2-prod:
    hosts:
      - app2-web1

  app2:
    include:
      - app2-prod
      - app2-dev

  all-apps:
    include:
      - app1
      - app2

hosts:
  web-app1-prod.location1.com:
    groups:
      - app1
      - location1
      - prod
      - web

  db-app1-prod.location1.com:
    groups:
      - app1
      - location1
      - prod
      - db

  app1-dev.location1.com:
    vars:
      EXAMPLE: "true"
    groups:
      - app1
      - location2
      - dev
      - web
      - db
'''

import os
from collections import MutableMapping, Sequence

from ansible import constants as C
from ansible.errors import AnsibleParserError
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native
from ansible.parsing.utils.addresses import parse_address
from ansible.plugins.inventory import BaseFileInventoryPlugin, detect_range, expand_hostname_range

def is_sequence(obj):
    return isinstance(obj, Sequence) and not isinstance(obj, basestring)

def is_dict(obj):
    return isinstance(obj, MutableMapping)

def must_be_sequence(obj, name=None):
    if not is_sequence(obj):
        if name:
            raise AnsibleParserError('Invalid "%s" entry, requires a sequence, found "%s" instead.' % (name, type(obj)))
        else:
            raise AnsibleParserError('Invalid data, requires a sequence, found "%s" instead.' % (name, type(obj)))

    return obj

def must_be_dict(obj, name=None):
    if not is_dict(obj):
        if name:
            raise AnsibleParserError('Invalid "%s" entry, requires a dictionary, found "%s" instead.' % (name, type(obj)))
        else:
            raise AnsibleParserError('Invalid data, requires a dictionary, found "%s" instead.' % (name, type(obj)))

    return obj

def must_not_be_plugin(obj):
    if 'plugin' in obj:
        raise AnsibleParserError('Plugin configuration YAML file, not YAML groups inventory')

    if 'all' in obj:
        raise AnsibleParserError('Standard configuration YAML file, not YAML groups inventory')
    
    return obj

class InventoryModule(BaseFileInventoryPlugin):
    NAME = 'yaml-groups'

    def __init__(self):
        super(InventoryModule, self).__init__()

    def verify_file(self, path):
        valid = False
        if super(InventoryModule, self).verify_file(path):
            file_name, ext = os.path.splitext(path)
            if not ext or ext in C.YAML_FILENAME_EXTENSIONS:
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):
        ''' parses the inventory file '''
        super(InventoryModule, self).parse(inventory, loader, path)

        try:
            data = self.loader.load_from_file(path)
        except Exception as e:
            raise AnsibleParserError(e)

        if not data:
            raise AnsibleParserError('Parsed empty YAML file')

        must_be_dict(data)
        must_not_be_plugin(data)

        if 'hosts' in data:
            self._parse_hosts(data['hosts'])

        if 'groups' in data:
            self._parse_groups(data['groups'])

    def _parse_hosts(self, hosts):
        must_be_dict(hosts, name='hosts')
        for host_name in hosts:
            self._parse_host(host_name, hosts[host_name])

    def _parse_host(self, host_pattern, host):
        '''
        Each host key can be a pattern, try to process it and add variables as needed
        '''
        must_be_dict(host)
        (host_names, port) = self._expand_hostpattern(host_pattern)

        for host_name in host_names:
            self.inventory.add_host(host_name, port=port)

        if 'groups' in host:
            self._parse_host_groups(host_names, host['groups'])

        if 'vars' in host:
            self._parse_host_vars(host_names, host['vars'])

    def _parse_host_vars(self, host_names, host_vars):
        must_be_dict(host_vars, name='vars')
        self.populate_host_vars(host_names, host_vars)

    def _parse_host_groups(self, host_names, host_groups):
        must_be_sequence(host_groups, name='groups')
        for group_name in host_groups:
            self.inventory.add_group(group_name)
            for host_name in host_names:
                self.inventory.add_child(group_name, host_name)

    def _parse_groups(self, groups):
        must_be_dict(groups, name='groups')
        for group_name in sorted(groups):
            self._parse_group(group_name, groups[group_name])

    def _parse_group(self, group_name, group_data):
        must_be_dict(group_data, name=('groups/%s %s' % (group_name, group_data)))
        self.inventory.add_group(group_name)
        group = self.inventory.groups[group_name]

        if 'vars' in group_data:
            group_vars = must_be_dict(group_data['vars'], name='vars')
            for var_name in group_vars:
                group.set_variable(var_name, group_vars[var_name])

        if 'hosts' in group_data:
            host_names = must_be_sequence(group_data['hosts'], name='hosts')
            for host_name in host_names:
                self.inventory.add_host(host_name)
                group.add_host(host_name)

        if 'include' in group_data:
            include_names = must_be_sequence(group_data['include'], name='include')
            for include_name in include_names:
                self._parse_group_include(group, include_name)

        if 'require' in group_data:
            require_names = must_be_sequence(group_data['require'], name='require')
            for require_name in require_names:
                self._parse_group_require(group, require_name)

        if 'exclude' in group_data:
            exclude_names = must_be_sequence(group_data['exclude'], name='exclude')
            for exclude_name in exclude_names:
                self._parse_group_exclude(group, exclude_name)

    def _parse_group_include(self, group, include_name):
        if include_name not in self.inventory.groups:
            raise AnsibleParserError('Group "%s" includes non-existant group "%s"' % (group_name, include_name))

        include_group = self.inventory.groups[include_name]
        for host_name in include_group.get_hosts():
            group.add_host(host_name)

    def _parse_group_require(self, group, require_name):
        if require_name not in self.inventory.groups:
            raise AnsibleParserError('Group "%s" requires non-existant group "%s"' % (group_name, require_name))

        require_group = self.inventory.groups[require_name]
        for host_name in group.get_hosts():
            if host_name not in require_group.get_hosts():
                group.remove_host(host_name)

    def _parse_group_exclude(self, group, exclude_name):
        if exclude_name not in self.inventory.groups:
            raise AnsibleParserError('Group "%s" excludes non-existant group "%s"' % (group_name, exclude_name))

        exclude_group = self.inventory.groups[exclude_name]
        for host_name in exclude_group.get_hosts():
            if host_name in group.get_hosts():
                group.remove_host(host_name)

    def _expand_hostpattern(self, hostpattern):
        '''
        Takes a single host pattern and returns a list of host_names and an
        optional port number that applies to all of them.
        '''
        # Can the given hostpattern be parsed as a host with an optional port
        # specification?

        try:
            (pattern, port) = parse_address(hostpattern, allow_ranges=True)
        except:
            # not a recognizable host pattern
            pattern = hostpattern
            port = None

        # Once we have separated the pattern, we expand it into list of one or
        # more host_names, depending on whether it contains any [x:y] ranges.

        if detect_range(pattern):
            host_names = expand_hostname_range(pattern)
        else:
            host_names = [pattern]

        return (host_names, port)
