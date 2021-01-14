"""
HTTP request parsing classes.

The RequestParser class is a container for the functions that
actually parse the request into the component properties:

    >>> parser = RequestParser(request)
    >>> parser.user_agent
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6)"

The AbstractRequestLog class is an abstract Django model that
can be used as a base class for any models in your application
that need to add request parsing functionality, but where you
want the request log data to be stored with your existing model.

The RequestLog class is a concrete subclass of AbstractRequestLog
that can be used as-is. If you want to centralise request logging
from a number of apps in your project into a single table, then
use this model.

"""
from __future__ import annotations

from typing import Any, Optional

from django.conf import settings
from django.db import models
from django.http import HttpRequest
from django.utils.timezone import now as tz_now
from django.utils.translation import gettext_lazy as _lazy


class RequestParser:
    """Container for HTTP request parsing."""

    def __init__(self, request: HttpRequest):
        self.request = request

    @classmethod
    def parse_remote_addr(cls, request: HttpRequest) -> str:
        """
        Extract client IP from request.

        If the request has passed through network infrastructure that rewrites
        the source IP (e.g. firewall, load balancer), then the original source
        IP should be in the `X-Forwarded-For` header, which may contain more
        than one IP (multiple rewrites). In this case, the 'real' end user IP
        is the first one in the chain.

        """
        x_forwarded_for = request.META.get("X_FORWARDED_FOR", "")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR", "")

    @property
    def user(self) -> Optional[settings.AUTH_USER_MODEL]:
        if self.request.user.is_authenticated:
            return self.request.user
        return None

    @property
    def session_key(self) -> str:
        return self.request.session.session_key or ""

    @property
    def http_method(self) -> str:
        return self.request.method

    @property
    def request_path(self) -> str:
        return self.request.path

    @property
    def query_string(self) -> str:
        return self.request.META.get("QUERY_STRING", "")

    @property
    def http_user_agent(self) -> str:
        return self.request.headers.get("User-Agent", "")

    @property
    def http_referer(self) -> str:
        return self.request.headers.get("Referer", "")

    @property
    def remote_addr(self) -> str:
        return RequestParser.parse_remote_addr(self.request)


class AbstractRequestLog(models.Model):
    """
    Abstract base model for storing request info.

    You should use this class if you want to include all of the fields in this
    class in your own model (and related database table).

    If you want to centralise your logs, use the RequestLog model class instead.

    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    session_key = models.CharField(blank=True, max_length=40)
    http_method = models.CharField(max_length=10)
    http_user_agent = models.TextField(default="")
    http_referer = models.TextField(default="")
    request_path = models.URLField(default="")
    query_string = models.TextField(blank=True, default="")
    remote_addr = models.CharField(max_length=100, default="")
    timestamp = models.DateTimeField(default=tz_now)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return super().__str__()

    def __repr__(self) -> str:
        return super().__str__()

    def save(self, *args: Any, **kwargs: Any) -> AbstractRequestLog:
        super().save(*args, **kwargs)
        return self

    def parse_request(self, request: HttpRequest) -> None:
        """Set object properties from a request."""
        parser = RequestParser(request)
        self.user = parser.user
        self.session_key = parser.session_key
        self.http_method = parser.http_method
        self.request_path = parser.request_path
        self.query_string = parser.query_string
        self.http_user_agent = parser.http_user_agent
        self.http_referer = parser.http_referer
        self.remote_addr = parser.remote_addr


class RequestLogManager(models.Manager):
    def create_log(
        self, request: HttpRequest, category: str = "", label: str = ""
    ) -> RequestLog:
        log = RequestLog(category=category, label=label)
        log.parse_request(request)
        return log.save()


class RequestLog(AbstractRequestLog):
    """Concrete implementation of a request log."""

    category = models.CharField(
        max_length=100, help_text=_lazy("Used to filter / group logs.")
    )
    label = models.CharField(
        max_length=100, help_text=_lazy("Used to identify individual logs.")
    )

    objects = RequestLogManager()

    def __str__(self) -> str:
        if self.user:
            return (
                f"Logged request by {self.user} to '{self.request_path[:100]}' "
                f"at {self.timestamp}"
            )
        return (
            f"Logged anonymous request to '{self.request_path[:100]}' "
            f"at {self.timestamp}"
        )

    def __repr__(self) -> str:
        return (
            f"<RequestLog id={self.id} user_id={self.user_id} "
            f"timestamp='self.timestamp'>"
        )
