FORMATTED_ERROR_MESSAGES: dict = {
    "ValidationError": {"short": "Invalid input", "details": None,},
    "ObjectDoesNotExist": {
        "short": "Not found",
        "details": "We were unable to locate the resource you requested.",
    },
    "NotAuthenticated": {
        "short": "Unauthorized",
        "details": "You are not currently authorized to make this request.",
    },
    "PermissionDenied": {
        "short": "Forbidden",
        "details": "You do not have permission to perform this action.",
    },
    "MultipleObjectsReturned": {
        "short": "Multiple found",
        "details": "Multiple resources were returned when only a single resource was expected",
    },
}
