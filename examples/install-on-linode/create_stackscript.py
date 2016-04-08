#!/usr/local/bin/python3

from linode import LinodeClient
import config

token = input("Please provide an OAuth Token: ")
lc = LinodeClient(token, base_url=config.api_base_url)
s = lc.create_stackscript('Demonstration_Public', '#!/bin/bash', lc.get_distributions(), is_public=True)
print("StackScript created, use this ID: {}".format(s.id))
