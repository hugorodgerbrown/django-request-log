from __future__ import annotations

from django.contrib import admin

from .models import RequestLog


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    """Admin model for RequestLog objects."""

    list_display = ("user", "http_method", "request_path", "query_string", "timestamp")
    readonly_fields = (
        "user",
        "session_key",
        "request_path",
        "query_string",
        "http_method",
        "http_user_agent",
        "http_referer",
        "remote_addr",
        "timestamp",
    )
    list_filter = ("category",)
