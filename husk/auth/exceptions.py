"""Auth-domain exceptions."""

from husk.core.exceptions import HuskError, NotFound, Unauthorized


class InvalidApiKey(Unauthorized):
    code = "invalid_api_key"


class ApiKeyNotFound(NotFound):
    code = "api_key_not_found"


class DuplicateApiKeyName(HuskError):
    status_code = 409
    code = "duplicate_api_key_name"


class InvalidCredentials(Unauthorized):
    code = "invalid_credentials"
