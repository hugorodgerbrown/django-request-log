from __future__ import annotations

from typing import Callable

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpRequest, HttpResponse

from request_log.models import RequestLog


class DebugRequestLogMiddleware:
    """
    Test middleware.

    This middleware will log *all* requests - including logging in, the admin
    site etc. Its purpose is to generate as much logging as possible for local
    testing so that you can see what gets logged. Just logging in to admin and
    navigating to the request log list view will generate records.

    NEVER ENABLE ON A LIVE SITE.

    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        if not settings.DEBUG:
            raise MiddlewareNotUsed("DebugRequestLogMiddleware not used")
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        RequestLog.objects.create_log(request, category="DEBUG_MIDDLEWARE", label="")
        return self.get_response(request)
