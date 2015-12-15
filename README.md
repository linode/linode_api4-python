# linode-python

apinext python sdk

### how to use

```python3
$ python3
Python 3.4.2 (default, Jan  7 2015, 11:54:58)
[GCC 4.2.1 Compatible Apple LLVM 6.0 (clang-600.0.56)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import linode
>>> linode.initialize("my-oauth-token")
>>> serv = linode.get_services(label='linode 1024')[0]
>>> serv.label
'Linode 1024'
>>> dc = linode.get_datacenters(label='newark')[0]
>>> distro = linode.get_distributions(label='ubuntu 14.04')[0]
>>> l = linode.create_linode(serv, dc, source=distro)
>>> l = l[0] # l[1] is a generated root password
>>> l.label
'linode810475'
>>> l.group
''
>>> l.status
'being_created'
>>> l.group = 'python_sdk'
>>> l.label = 'awesome_box'
>>> l.save()
True
>>> l.status
'brand_new'
```
### setup as a shell

 1. git clone this repo
 1. cd linode-python
 1. `mkdir ~/.linode`
 1. if working in staging, `echo 'http://staging.url/v1' > ~/.linode/base_url`
 1. ./shell.py

You will be prompted for an api token: input 'token ' followed by your oauth token.

The module is already imported and initialized.  List your linodes:

```python
>>> for l in linode.get_linodes():
>>>    print l.label
```

Get all linodes in a group:

```python
>>> group = linode.get_linodes(group='my_awesome_group')
```

Make a new linode (see above)

Wait for a linode to boot:

```python
>>> l = linode.get_linodes()[-1]
>>> l.boot()
>>> while not 'running' in l.status:
>>>     pass
```

Find your linode's IP:

```python
>>> l = linode.get_linodes()[-1]
>>> l.ip_addresses.public.ipv4
>>> l.ip_addresses.private.ipv4
```
