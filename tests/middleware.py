from __future__ import annotations

from typing import Callable

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpRequest, HttpResponse

from request_log.models import RequestLog


class DebugRequestLogMiddleware:

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        if not settings.DEBUG:
            raise MiddlewareNotUsed("DebugRequestLogMiddleware not used")
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        RequestLog.objects.log_request(request)
        return self.get_response(request)
