import os
from datetime import datetime

from linode_api4 import UnexpectedResponseError
from linode_api4.common import SSH_KEY_TYPES
from linode_api4.groups import Group
from linode_api4.objects import (
    AuthorizedApp,
    MappedObject,
    PersonalAccessToken,
    Profile,
    ProfileLogin,
    SSHKey,
    TrustedDevice,
)


class ProfileGroup(Group):
    """
    Collections related to your user.
    """

    def __call__(self):
        """
        Retrieve the acting user's Profile, containing information about the
        current user such as their email address, username, and uid.  This is
        intended to be called off of a :any:`LinodeClient` object, like this::

           profile = client.profile()

        API Documentation: https://www.linode.com/docs/api/profile/#profile-view

        :returns: The acting user's profile.
        :rtype: Profile
        """
        result = self.client.get("/profile")

        if not "username" in result:
            raise UnexpectedResponseError(
                "Unexpected response when getting profile!", json=result
            )

        p = Profile(self.client, result["username"], result)
        return p

    def trusted_devices(self):
        """
        Returns the Trusted Devices on your profile.

        API Documentation: https://www.linode.com/docs/api/profile/#trusted-devices-list

        :returns: A list of Trusted Devices for this profile.
        :rtype: PaginatedList of TrustedDevice
        """
        return self.client._get_and_filter(TrustedDevice)

    def user_preferences(self):
        """
        View a list of user preferences tied to the OAuth client that generated the token making the request.
        """

        result = self.client.get(
            "{}/preferences".format(Profile.api_endpoint), model=self
        )

        return MappedObject(**result)

    def security_questions(self):
        """
        Returns a collection of security questions and their responses, if any, for your User Profile.

        API Documentation: https://www.linode.com/docs/api/profile/#security-questions-list
        """

        result = self.client.get(
            "{}/security-questions".format(Profile.api_endpoint), model=self
        )

        return MappedObject(**result)

    def security_questions_answer(self, questions):
        """
        Adds security question responses for your User. Requires exactly three unique questions.
        Previous responses are overwritten if answered or reset to null if unanswered.

        Example question:
        {
            "question_id": 11,
            "response": "secret answer 3"
        }
        """

        if len(questions) != 3:
            raise ValueError("Exactly 3 security questions are required.")

        params = {"security_questions": questions}

        result = self.client.post(
            "{}/security-questions".format(Profile.api_endpoint),
            model=self,
            data=params,
        )

        return MappedObject(**result)

    def user_preferences_update(self, **preferences):
        """
        Updates a user’s preferences.
        """

        result = self.client.put(
            "{}/preferences".format(Profile.api_endpoint),
            model=self,
            data=preferences,
        )

        return MappedObject(**result)

    def phone_number_delete(self):
        """
        Delete the verified phone number for the User making this request.

        API Documentation: https://www.linode.com/docs/api/profile/#phone-number-delete

        :returns: Returns True if the operation was successful.
        :rtype: bool
        """

        resp = self.client.delete(
            "{}/phone-number".format(Profile.api_endpoint), model=self
        )

        if "error" in resp:
            raise UnexpectedResponseError(
                "Unexpected response when deleting phone number!",
                json=resp,
            )

        return True

    def phone_number_verify(self, otp_code):
        """
        Verify a phone number by confirming the one-time code received via SMS message
        after accessing the Phone Verification Code Send (POST /profile/phone-number) command.

        API Documentation: https://www.linode.com/docs/api/profile/#phone-number-verify

        :param otp_code: The one-time code received via SMS message after accessing the Phone Verification Code Send
        :type otp_code: str

        :returns: Returns True if the operation was successful.
        :rtype: bool
        """

        if not otp_code:
            raise ValueError("OTP Code required to verify phone number.")

        params = {"otp_code": str(otp_code)}

        resp = self.client.post(
            "{}/phone-number/verify".format(Profile.api_endpoint),
            model=self,
            data=params,
        )

        if "error" in resp:
            raise UnexpectedResponseError(
                "Unexpected response when verifying phone number!",
                json=resp,
            )

        return True

    def phone_number_verification_code_send(self, iso_code, phone_number):
        """
        Send a one-time verification code via SMS message to the submitted phone number.

        API Documentation: https://www.linode.com/docs/api/profile/#phone-number-verification-code-send

        :param iso_code: The two-letter ISO 3166 country code associated with the phone number.
        :type iso_code: str

        :param phone_number: A valid phone number.
        :type phone_number: str

        :returns: Returns True if the operation was successful.
        :rtype: bool
        """

        if not iso_code:
            raise ValueError("ISO Code required to send verification code.")

        if not phone_number:
            raise ValueError("Phone Number required to send verification code.")

        params = {"iso_code": iso_code, "phone_number": phone_number}

        resp = self.client.post(
            "{}/phone-number".format(Profile.api_endpoint),
            model=self,
            data=params,
        )

        if "error" in resp:
            raise UnexpectedResponseError(
                "Unexpected response when sending verification code!",
                json=resp,
            )

        return True

    def logins(self):
        """
        Returns the logins on your profile.

        API Documentation: https://www.linode.com/docs/api/profile/#logins-list

        :returns: A list of logins for this profile.
        :rtype: PaginatedList of ProfileLogin
        """
        return self.client._get_and_filter(ProfileLogin)

    def tokens(self, *filters):
        """
        Returns the Person Access Tokens active for this user.

        API Documentation: https://www.linode.com/docs/api/profile/#personal-access-tokens-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of tokens that matches the query.
        :rtype: PaginatedList of PersonalAccessToken
        """
        return self.client._get_and_filter(PersonalAccessToken, *filters)

    def token_create(self, label=None, expiry=None, scopes=None, **kwargs):
        """
        Creates and returns a new Personal Access Token.

        API Documentation: https://www.linode.com/docs/api/profile/#personal-access-token-create

        :param label: The label of the new Personal Access Token.
        :type label: str
        :param expiry: When the new Personal Accses Token will expire.
        :type expiry: datetime or str
        :param scopes: A space-separated list of OAuth scopes for this token.
        :type scopes: str

        :returns: The new Personal Access Token.
        :rtype: PersonalAccessToken
        """
        if label:
            kwargs["label"] = label
        if expiry:
            if isinstance(expiry, datetime):
                expiry = datetime.strftime(expiry, "%Y-%m-%dT%H:%M:%S")
            kwargs["expiry"] = expiry
        if scopes:
            kwargs["scopes"] = scopes

        result = self.client.post("/profile/tokens", data=kwargs)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Personal Access Token!",
                json=result,
            )

        token = PersonalAccessToken(self.client, result["id"], result)
        return token

    def apps(self, *filters):
        """
        Returns the Authorized Applications for this user

        API Documentation: https://www.linode.com/docs/api/profile/#authorized-apps-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Authorized Applications for this user
        :rtype: PaginatedList of AuthorizedApp
        """
        return self.client._get_and_filter(AuthorizedApp, *filters)

    def ssh_keys(self, *filters):
        """
        Returns the SSH Public Keys uploaded to your profile.

        API Documentation: https://www.linode.com/docs/api/profile/#ssh-keys-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of SSH Keys for this profile.
        :rtype: PaginatedList of SSHKey
        """
        return self.client._get_and_filter(SSHKey, *filters)

    def ssh_key_upload(self, key, label):
        """
        Uploads a new SSH Public Key to your profile  This key can be used in
        later Linode deployments.

        API Documentation: https://www.linode.com/docs/api/profile/#ssh-key-add

        :param key: The ssh key, or a path to the ssh key.  If a path is provided,
                    the file at the path must exist and be readable or an exception
                    will be thrown.
        :type key: str
        :param label: The name to give this key.  This is purely aesthetic.
        :type label: str

        :returns: The newly uploaded SSH Key
        :rtype: SSHKey
        :raises ValueError: If the key provided does not appear to be valid, and
                            does not appear to be a path to a valid key.
        """
        if not key.startswith(SSH_KEY_TYPES):
            # this might be a file path - look for it
            path = os.path.expanduser(key)
            if os.path.isfile(path):
                with open(path) as f:
                    key = f.read().strip()
            if not key.startswith(SSH_KEY_TYPES):
                raise ValueError("Invalid SSH Public Key")

        params = {
            "ssh_key": key,
            "label": label,
        }

        result = self.client.post("/profile/sshkeys", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when uploading SSH Key!", json=result
            )

        ssh_key = SSHKey(self.client, result["id"], result)
        return ssh_key
