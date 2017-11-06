# ansible-inventory-yaml-groups
Alternative YAML formatted inventory for Ansible. This allows you to to assign groups to hosts as well as hosts to groups, and easily make new groups that are supersets and subsets of other groups.

*NOTE:* Ansible supports it's own YAML formatted inventory, see: https://github.com/ansible/ansible/blob/devel/examples/hosts.yaml

# Installation

If you are using Ansible 2.4 or later you can use the inventory version, otherwise you must use the dynamic inventory version.

## Inventory Plugin (2.4+)

Add the following to `ansible.cfg`:
```ini
[defaults]
inventory = hosts.yml
inventory_plugins = /path/to/ansible-inventory-yaml-groups/inventory_plugins

[inventory]
enable_plugins = host_list, script, yaml_groups, ini
```

## Dynamic Inventory (Any)

In `ansible.cfg`, set `inventory` to `yaml_groups.py`.  Addthe following to `ansible.cfg`:
```ini
[defaults]
inventory = /path/to/ansible-inventory-yaml-groups/yaml_groups.py
```

You can control the name of the `hosts.yml` file by setting `ANSIBLE_HOSTS_YML`.

# Format of `hosts.yml`

The YAML file is divided into two sections, `groups` and `hosts`.

## Groups (optional)
Entries in `groups` are optional, but they allow the creation groups by listing it's `hosts`, and/or `vars` as in the standard Ansible inventory file.  Hosts listed in `hosts` will be created even if there is no corresponding entry in the `hosts` section.

You can also provide a list of groups to `include` all hosts from, a list of groups to `require` that each host belong to, and a list of groups to `exclude` that each host must not belong to.  The order in which these groups are updated is undefined.  You can use the implicit `all` group here, which is only useful for `include`.

## Hosts (optional)
Each host in the `hosts` section can have a list of `groups` that it will be a member of, and host varibles defined in `vars`.  Groups will be created even if there is no corresponding group in the groups section.

## Example: `hosts.yml`
```yaml
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
```

# See Also
- https://github.com/ansible/ansible/blob/devel/examples/hosts.yaml
- https://github.com/jtyr/ansible-yaml_inventory
