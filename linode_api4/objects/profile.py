from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects import Base, Property


class AuthorizedApp(Base):
    """
    An application with authorized access to an account.

    API Documentation: https://www.linode.com/docs/api/profile/#authorized-app-view
    """

    api_endpoint = "/profile/apps/{id}"

    properties = {
        "id": Property(identifier=True),
        "scopes": Property(),
        "label": Property(),
        "created": Property(is_datetime=True),
        "expiry": Property(is_datetime=True),
        "thumbnail_url": Property(),
        "website": Property(),
    }


class PersonalAccessToken(Base):
    """
    A Person Access Token associated with a Profile.

    API Documentation: https://www.linode.com/docs/api/profile/#personal-access-token-view
    """

    api_endpoint = "/profile/tokens/{id}"

    properties = {
        "id": Property(identifier=True),
        "scopes": Property(),
        "label": Property(mutable=True),
        "created": Property(is_datetime=True),
        "token": Property(),
        "expiry": Property(is_datetime=True),
    }


class WhitelistEntry(Base):
    """
    DEPRECATED: Limited to customers with a feature tag
    """

    api_endpoint = "/profile/whitelist/{id}"

    properties = {
        "id": Property(identifier=True),
        "address": Property(),
        "netmask": Property(),
        "note": Property(),
    }


class Profile(Base):
    """
    A Profile containing information about the current User.

    API Documentation: https://www.linode.com/docs/api/profile/#profile-view
    """

    api_endpoint = "/profile"
    id_attribute = "username"

    properties = {
        "username": Property(identifier=True),
        "uid": Property(),
        "email": Property(mutable=True),
        "timezone": Property(mutable=True),
        "email_notifications": Property(mutable=True),
        "referrals": Property(),
        "ip_whitelist_enabled": Property(mutable=True),
        "lish_auth_method": Property(mutable=True),
        "authorized_keys": Property(mutable=True),
        "two_factor_auth": Property(),
        "restricted": Property(),
        "authentication_type": Property(),
        "authorized_keys": Property(),
        "verified_phone_number": Property(),
    }

    def enable_tfa(self):
        """
        Enables TFA for the token's user.  This requies a follow-up request
        to confirm TFA.  Returns the TFA secret that needs to be confirmed.

        API Documentation: https://www.linode.com/docs/api/profile/#two-factor-secret-create

        :returns: The TFA secret
        :rtype: str
        """
        result = self._client.post("/profile/tfa-enable")

        return result["secret"]

    def confirm_tfa(self, code):
        """
        Confirms TFA for an account.  Needs a TFA code generated by enable_tfa

        API Documentation: https://www.linode.com/docs/api/profile/#two-factor-authentication-confirmenable

        :returns: Returns true if operation was successful
        :rtype: bool
        """
        self._client.post(
            "/profile/tfa-enable-confirm", data={"tfa_code": code}
        )

        return True

    def disable_tfa(self):
        """
        Turns off TFA for this user's account.

        API Documentation: https://www.linode.com/docs/api/profile/#two-factor-authentication-disable

        :returns: Returns true if operation was successful
        :rtype: bool
        """
        self._client.post("/profile/tfa-disable")

        return True

    @property
    def grants(self):
        """
        Returns grants for the current user

        API Documentation: https://www.linode.com/docs/api/profile/#grants-list

        :returns: The grants for the current user
        :rtype: UserGrants
        """
        from linode_api4.objects.account import (  # pylint: disable-all
            UserGrants,
        )

        resp = self._client.get(
            "/profile/grants"
        )  # use special endpoint for restricted users

        grants = None
        if resp is not None:
            # if resp is None, we're unrestricted and do not have grants
            grants = UserGrants(self._client, self.username, resp)

        return grants

    @property
    def whitelist(self):
        """
        Returns the user's whitelist entries, if whitelist is enabled

        DEPRECATED: Limited to customers with a feature tag
        """
        return self._client._get_and_filter(WhitelistEntry)

    def add_whitelist_entry(self, address, netmask, note=None):
        """
        Adds a new entry to this user's IP whitelist, if enabled

        DEPRECATED: Limited to customers with a feature tag
        """
        result = self._client.post(
            "{}/whitelist".format(Profile.api_endpoint),
            data={
                "address": address,
                "netmask": netmask,
                "note": note,
            },
        )

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response creating whitelist entry!"
            )

        return WhitelistEntry(result["id"], self._client, json=result)


class SSHKey(Base):
    """
    An SSH Public Key uploaded to your profile for use in Linode Instance deployments.

    API Documentation: https://www.linode.com/docs/api/profile/#ssh-key-view
    """

    api_endpoint = "/profile/sshkeys/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "ssh_key": Property(),
        "created": Property(is_datetime=True),
    }


class TrustedDevice(Base):
    """
    A Trusted Device for a User.

    API Documentation: https://www.linode.com/docs/api/profile/#trusted-device-view
    """

    api_endpoint = "/profile/devices/{id}"

    properties = {
        "id": Property(identifier=True),
        "created": Property(is_datetime=True),
        "expiry": Property(is_datetime=True),
        "last_authenticated": Property(is_datetime=True),
        "last_remote_addr": Property(),
        "user_agent": Property(),
    }


class ProfileLogin(Base):
    """
    A Login object displaying information about a successful account login from this user.

    API Documentation: https://www.linode.com/docs/api/profile/#login-view
    """

    api_endpoint = "profile/logins/{id}"

    properties = {
        "id": Property(identifier=True),
        "datetime": Property(is_datetime=True),
        "ip": Property(),
        "restricted": Property(),
        "status": Property(),
        "username": Property(),
    }
