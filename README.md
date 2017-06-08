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

## Hosts (optional)
Each host in the `hosts` section can have `groups` to define it's group membership, and `vars` to define host variables.

```yaml
hosts:
  app1-web:
    groups:
      - app1
      - web
      - prod

  app1-db:
    groups:
      - app1
      - db
      - prod

  app1-dev:
    vars:
      EXAMPLE: "true"
    groups:
      - app1
      - web
      - db
      - dev      
```

## Groups (optional)

Entries in `groups` are optional, but they allow the creation groups by listing it's `hosts`, `children`, and/or `vars` as in the standard Ansible inventory file.  You can also use `include` to include all hosts from another group, and `require` to remove hosts that are not part of the other group, for instance all production web servers.  This is useful when combined with `group_vars` files

``` yaml
groups:

  app1-dev1:
    include:
      - app1
    require:
      - dev
      
  app1-web:
    include:
      - app1
    require:
      - web
  
  app2-web:
    hosts:
      - app2-web1
  
  apps:
    children:
      - app1
      - app2
```

# See Also
- https://github.com/ansible/ansible/blob/devel/examples/hosts.yaml
- https://github.com/jtyr/ansible-yaml_inventory
