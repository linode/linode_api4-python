from __future__ import absolute_import

import os


def load_and_validate_keys(authorized_keys):
    """
    Loads authorized_keys as taken by create_linode, create_disk or rebuild, and
    loads in any keys from any files provided.

    :param authorized_keys: A list of keys or paths to keys, or a single key

    :returns: A list of raw keys
    :raises: ValueError if keys in authorized_keys don't appear to be a raw
             key and can't be opened.
    """
    if not authorized_keys:
        return None

    if not isinstance(authorized_keys, list):
        authorized_keys = [authorized_keys]

    ret = []

    for k in authorized_keys:
        accepted_types = ('ssh-dss', 'ssh-rsa', 'ecdsa-sha2-nistp', 'ssh-ed25519')
        if any([ t for t in accepted_types if k.startswith(t) ]):
            # this looks like a key, cool
            ret.append(k)
        else:
            # it doesn't appear to be a key.. is it a path to the key?
            k = os.path.expanduser(k)
            if os.path.isfile(k):
                with open(k) as f:
                    ret.append(f.read().rstrip())
            else:
                raise ValueError("authorized_keys must either be paths "
                                 "to the key files or a list of raw "
                                 "public key of one of these types: {}".format(accepted_types))
    return ret
