from husk.core.exceptions import HuskError, NotFound, Unauthorized


class PreviewTokenNotFound(NotFound):
    code = "preview_token_not_found"


class PreviewTokenExpired(Unauthorized):
    code = "preview_token_expired"


class PreviewTokenInvalid(HuskError):
    status_code = 400
    code = "preview_token_invalid"
