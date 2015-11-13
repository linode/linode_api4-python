# linode-python

apinext python sdk

### how to use

```python3
$ python3
Python 3.4.2 (default, Jan  7 2015, 11:54:58)
[GCC 4.2.1 Compatible Apple LLVM 6.0 (clang-600.0.56)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import linode
>>> serv = linode.get_services(label='linode 1024')[0]
>>> serv.label
'Linode 1024'
>>> dc = linode.get_datacenters(label='newark')[0]
>>> distro = linode.get_distributions(label='ubuntu 14.04')[0]
>>> l = linode.create_linode(serv, dc, source=distro, opts={'root_pass':'password123'})
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
