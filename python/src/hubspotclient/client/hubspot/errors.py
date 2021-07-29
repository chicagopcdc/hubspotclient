from cdiserrors import APIError, InternalError, AuthZError


class HubspotError(APIError):
    """Generic exception related to problems with Hubspot."""

    def __init__(self, message, code):
        self.message = message
        self.code = code
        self.json = {"error": self.message, "code": self.code}


class HubspotUnhealthyError(InternalError, HubspotError):
    """Exception raised to signify the Hubspot service is unresponsive."""

    def __init__(self, message=None):
        super(HubspotUnhealthyError, self).__init__()
        self.message = message or "could not reach Hubspot service"
        self.code = 500
        self.json = {"error": self.message, "code": self.code}
