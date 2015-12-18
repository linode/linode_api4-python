from linode import mappings

class ApiError(RuntimeError):
    def __init__(self, message, status=400):
        super(RuntimeError, self).__init__(message)
        self.status=status
