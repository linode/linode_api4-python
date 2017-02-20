from linode import mappings

class ApiError(RuntimeError):
    """
    An API Error is any error returned from the API.  These
    typically have a status code in the 400s or 500s.  Most
    often, this will be caused by invalid input to the API.
    """
    def __init__(self, message, status=400, json=None):
        super(RuntimeError, self).__init__(message)
        self.status = status
        self.json = json

class UnexpectedResponseError(RuntimeError):
    """
    An Unexpected Response Error occurs when the API returns
    something that this library is unable to parse, usually
    because it expected something specific and didn't get it.
    These typically indicate an oversight in developing this
    library, and should be fixed with changes to this codebase.
    """
    def __init__(self, message, status=200, json=None):
        super(RuntimeError, self).__init__(message)
        self.status = status
        self.json = json
