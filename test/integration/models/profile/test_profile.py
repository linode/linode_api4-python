import pytest

from linode_api4.objects import PersonalAccessToken, Profile, SSHKey


@pytest.mark.smoke
def test_user_profile(test_linode_client):
    client = test_linode_client

    profile = client.profile()

    assert isinstance(profile, Profile)


def test_get_personal_access_token_objects(test_linode_client):
    client = test_linode_client

    personal_access_tokens = client.profile.tokens()

    if len(personal_access_tokens) > 0:
        assert isinstance(personal_access_tokens[0], PersonalAccessToken)


@pytest.mark.smoke
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_get_sshkeys(test_linode_client, test_sshkey):
    client = test_linode_client

    ssh_keys = client.profile.ssh_keys()

    ssh_labels = [i.label for i in ssh_keys]

    assert isinstance(test_sshkey, SSHKey)
    assert test_sshkey.label in ssh_labels


@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_ssh_key_create(test_sshkey, ssh_key_gen):
    pub_key = ssh_key_gen[0]
    key = test_sshkey

    assert pub_key == key._raw_json["ssh_key"]
