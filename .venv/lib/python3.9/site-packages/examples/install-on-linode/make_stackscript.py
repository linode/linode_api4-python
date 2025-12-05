#!/usr/local/bin/python3

from linode_api4 import LinodeClient, Image
import config

token = input("Please provide an OAuth Token: ")
client = LinodeClient(token)
s = client.linode.stackscript_create('Demonstration_Public', '#!/bin/bash',
                                     client.images(Image.is_public==True), is_public=True)
print("StackScript created, use this ID: {}".format(s.id))
