class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400
    ):
        super().__init__(message)

        self.code = code
        self.message = message
        self.status_code = status_code


def success(data):
    return {
        "success": True,
        "data": data,
        "error": None
    }


def error_payload(code: str, message: str):
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message
        }
    }
