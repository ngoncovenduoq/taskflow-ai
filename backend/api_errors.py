"""Map third-party API errors to safe, predictable FastAPI responses."""

from fastapi import HTTPException


# Mapping cac loai exception sang HTTP status code
_ERROR_STATUS_BY_NAME = {
    "TooManyRequestsResponseError": 429,
    "RateLimitError": 429,
    "UsageLimitExceededError": 429,
    "TavilyKeylessLimitError": 429,

    "PaymentRequiredResponseError": 402,

    "PayloadTooLargeResponseError": 413,

    "BadRequestResponseError": 400,
    "BadRequestError": 400,

    "InvalidAPIKeyError": 401,
    "MissingAPIKeyError": 401,
    "UnauthorizedResponseError": 401,

    "ForbiddenError": 403,
    "ForbiddenResponseError": 403,

    "RequestTimeoutResponseError": 504,
    "APITimeoutError": 504,
    "TimeoutError": 504,
    "ReadTimeout": 504,
    "ConnectTimeout": 504,
    "Timeout": 504,

    "APIConnectionError": 503,
    "ConnectionError": 503,
    "ConnectError": 503,
    "RemoteProtocolError": 503,
    "ServiceUnavailableResponseError": 503,
}


# Lay HTTP status tu exception
def upstream_status(error: Exception) -> int | None:

    response = getattr(
        error,
        "response",
        None
    )

    for raw_status in (
        getattr(error, "status_code", None),
        getattr(response, "status_code", None),
        getattr(error, "status", None),
    ):

        if (
            isinstance(raw_status, int)
            and 400 <= raw_status <= 599
        ):
            return raw_status

    return _ERROR_STATUS_BY_NAME.get(
        type(error).__name__
    )


# Chuyen loi API thanh HTTPException
def to_http_exception(error: Exception) -> HTTPException:

    status = upstream_status(error)

    name = type(error).__name__

    # Tavily het han muc tim kiem
    if name in {
        "UsageLimitExceededError",
        "TavilyKeylessLimitError"
    }:

        http_status = 429
        code = "SEARCH_LIMIT_REACHED"

        message = (
            "Tavily đã chạm giới hạn tìm kiếm. "
            "Hãy kiểm tra hạn mức sử dụng."
        )

    # OpenRouter het credit
    elif status == 402:

        http_status = 402
        code = "AI_CREDITS_EXHAUSTED"

        message = (
            "OpenRouter không đủ credit. "
            "Hãy kiểm tra số dư tài khoản."
        )

    # Vuot rate limit
    elif status == 429:

        http_status = 429
        code = "RATE_LIMITED"

        message = (
            "Dịch vụ AI đang giới hạn số lần gọi. "
            "Vui lòng thử lại sau."
        )

    # Request qua lon
    elif status == 413:

        http_status = 413
        code = "REQUEST_TOO_LARGE"

        message = (
            "Nội dung gửi tới model quá lớn. "
            "Hãy rút ngắn yêu cầu."
        )

    # Timeout
    elif status in (408, 504):

        http_status = 504
        code = "UPSTREAM_TIMEOUT"

        message = (
            "Dịch vụ AI hoặc tìm kiếm phản hồi quá chậm. "
            "Hãy thử lại sau."
        )

    # API key khong hop le hoac khong du quyen
    elif status in (401, 403):

        http_status = 503
        code = "UPSTREAM_ACCESS_ERROR"

        message = (
            "Dịch vụ bên ngoài từ chối truy cập. "
            "Hãy kiểm tra API key và hạn mức."
        )

    # Request khong hop le
    elif status == 400:

        http_status = 400
        code = "UPSTREAM_BAD_REQUEST"

        message = (
            "Yêu cầu không được model chấp nhận. "
            "Hãy thử rút ngắn hoặc sửa nội dung."
        )

    # Dich vu ben ngoai gap loi
    elif status is not None and status >= 500:

        http_status = 503
        code = "UPSTREAM_UNAVAILABLE"

        message = (
            "Dịch vụ AI hoặc tìm kiếm đang gặp sự cố. "
            "Hãy thử lại sau."
        )

    # Loi khong xac dinh
    else:

        http_status = 500
        code = "INTERNAL_ERROR"

        message = (
            "Đã xảy ra lỗi xử lý yêu cầu. "
            "Vui lòng thử lại sau."
        )

    return HTTPException(
        status_code=http_status,
        detail={
            "code": code,
            "message": message
        }
    )