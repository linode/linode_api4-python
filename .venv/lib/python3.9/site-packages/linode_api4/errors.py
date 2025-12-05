# Necessary to maintain compatibility with Python < 3.11
from __future__ import annotations

from builtins import super
from json import JSONDecodeError
from typing import Any, Dict, Optional

from requests import Response


class ApiError(RuntimeError):
    """
    An API Error is any error returned from the API.  These
    typically have a status code in the 400s or 500s.  Most
    often, this will be caused by invalid input to the API.
    """

    def __init__(
        self,
        message: str,
        status: int = 400,
        json: Optional[Dict[str, Any]] = None,
        response: Optional[Response] = None,
    ):
        super().__init__(message)

        self.status = status
        self.json = json
        self.response = response

        self.errors = []

        if json and "errors" in json and isinstance(json["errors"], list):
            self.errors = [e["reason"] for e in json["errors"]]

    @classmethod
    def from_response(
        cls,
        response: Response,
        message: Optional[str] = None,
        disable_formatting: bool = False,
    ) -> Optional[ApiError]:
        """
        Creates an ApiError object from the given response,
        or None if the response does not contain an error.

        :arg response: The response to create an ApiError from.
        :arg message: An optional message to prepend to the error's message.
        :arg disable_formatting: If true, the error's message will not automatically be formatted
                                 with details from the API response.

        :returns: The new API error.
        """

        if response.status_code < 400 or response.status_code > 599:
            # No error was found
            return None

        request = response.request

        try:
            response_json = response.json()
        except JSONDecodeError:
            response_json = None

        # Use the user-defined message is formatting is disabled
        if disable_formatting:
            return cls(
                message,
                status=response.status_code,
                json=response_json,
                response=response,
            )

        # Build the error string
        error_fmt = "N/A"

        if response_json is not None and "errors" in response_json:
            errors = []

            for error in response_json["errors"]:
                field = error.get("field")
                reason = error.get("reason")
                errors.append(f"{field + ': ' if field else ''}{reason}")

            error_fmt = "; ".join(errors)

        elif len(response.text or "") > 0:
            error_fmt = response.text

        return cls(
            (
                f"{message + ': ' if message is not None else ''}"
                f"{f'{request.method} {request.path_url}: ' if request else ''}"
                f"[{response.status_code}] {error_fmt}"
            ),
            status=response.status_code,
            json=response_json,
            response=response,
        )


class UnexpectedResponseError(RuntimeError):
    """
    An Unexpected Response Error occurs when the API returns
    something that this library is unable to parse, usually
    because it expected something specific and didn't get it.
    These typically indicate an oversight in developing this
    library, and should be fixed with changes to this codebase.
    """

    def __init__(
        self,
        message: str,
        status: int = 200,
        json: Optional[Dict[str, Any]] = None,
        response: Optional[Response] = None,
    ):
        super().__init__(message)

        self.status = status
        self.json = json
        self.response = response

    @classmethod
    def from_response(
        cls,
        message: str,
        response: Response,
    ) -> Optional[UnexpectedResponseError]:
        """
        Creates an UnexpectedResponseError object from the given response and message.

        :arg message: The message to create this error with.
        :arg response: The response to create an UnexpectedResponseError from.
        :returns: The new UnexpectedResponseError.
        """

        try:
            response_json = response.json()
        except JSONDecodeError:
            response_json = None

        return cls(
            message,
            status=response.status_code,
            json=response_json,
            response=response,
        )
