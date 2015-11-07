from linode import api

def get_distributions():
    return api.get_objects('/distributions', 'distributions')

def get_linodes():
    return api.get_objects('/linodes', 'linodes')
