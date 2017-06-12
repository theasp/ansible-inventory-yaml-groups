# ansible-inventory-yml
Alternative YAML formatted inventory for Ansible. This allows you to to assign groups to hosts as well as hosts to groups, and easily make new groups that are supersets and subsets of other groups.

*NOTE:* Ansible supports it's own YML formatted inventory, see: https://github.com/ansible/ansible/blob/devel/examples/hosts.yaml

# Usage
Copy `hosts.py` and `hosts.sh` into the directory you are using ansible from.  In `ansible.cfg`, set `inventory` to `hosts.sh`.

```
[defaults]
inventory = hosts.sh
```

You can control the name of the `hosts.yml` file by setting `ANSIBLE_HOSTS_YML`.

# Format of `hosts.yml`

The YAML file is divided into two sections, `groups` and `hosts`.

## Groups (optional)
Entries in `groups` are optional, but they allow the creation groups by listing it's `hosts`, and/or `vars` as in the standard Ansible inventory file.  Hosts listed in `hosts` will be created even if there is no corresponding entry in the `hosts` section.

You can also provide a list of groups to `include` all hosts from, a list of groups to `require` that each host belong to, and a list of groups to `exclude` that each host must not belong to.

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

# Debugging

To see the generated inventory, run:
``` bash
./hosts.sh --list
```

You can use `jq` to make it a bit more readable:
``` bash
./hosts.sh --list | jq .
```


# See Also
- https://github.com/ansible/ansible/blob/devel/examples/hosts.yaml
- https://github.com/jtyr/ansible-yaml_inventory
