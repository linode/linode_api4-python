#!/usr/local/bin/python3

from linode import LinodeClient
import config

token = input("Please provide an OAuth Token: ")
client = LinodeClient(token, base_url=config.api_base_url)
s = client.linode.create_stackscript('Demonstration_Public', '#!/bin/bash',
        client.linode.get_distributions(), is_public=True)
print("StackScript created, use this ID: {}".format(s.id))
