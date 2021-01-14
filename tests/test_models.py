from unittest import mock

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory, TestCase
from django.utils.timezone import now as tz_now
from freezegun import freeze_time

from request_log.models import RequestLog, RequestParser

# from unittest.case import TestCase
NOW = tz_now()


@pytest.mark.parametrize(
    "x_forwarded_for,remote_addr,result",
    [
        ("", "192.168.0.1", "192.168.0.1"),
        ("127.0.0.1", "192.168.0.1", "127.0.0.1"),
        ("127.0.0.1,127.0.0.2", "192.168.0.1", "127.0.0.1"),
    ],
)
def test_parse_remote_addr(x_forwarded_for, remote_addr, result):
    """Test the RequestParser.parse_remote_addr method."""
    factory = RequestFactory()
    request = factory.get(
        "/", X_FORWARDED_FOR=x_forwarded_for, REMOTE_ADDR=remote_addr
    )
    assert request.META["X_FORWARDED_FOR"] == x_forwarded_for
    assert request.META["REMOTE_ADDR"] == remote_addr
    RequestParser.parse_remote_addr(request) == result


class TestRequestParser:
    def test_request_properties(self):
        factory = RequestFactory()
        request = factory.post(
            "/foo/bar?a=b",
            HTTP_USER_AGENT="Mozilla/5.0",
            HTTP_REFERER="google.com",
            X_FORWARDED_FOR="127.0.0.2",
        )
        request.user = User()
        request.session = mock.Mock(session_key="fake_session")
        parser = RequestParser(request)
        assert parser.user == request.user
        assert parser.session_key == "fake_session"
        assert parser.http_method == "POST"
        assert parser.request_path == "/foo/bar"
        assert parser.query_string == "a=b"
        assert parser.http_user_agent == "Mozilla/5.0"
        assert parser.http_referer == "google.com"
        assert parser.remote_addr == "127.0.0.2"

    def test_remote_addr(self):
        factory = RequestFactory()
        request = factory.get("/", X_FORWARDED_FOR="127.0.0.2")
        parser = RequestParser(request)
        parser.remote_addr == "127.0.0.2"

    def test_user_anonymous(self):
        factory = RequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()
        parser = RequestParser(request)
        assert parser.user is None

    def test_user_authenticated(self):
        factory = RequestFactory()
        request = factory.get("/")
        request.user = User()
        parser = RequestParser(request)
        assert parser.user == request.user


class TestRequestLogManager(TestCase):
    @freeze_time(NOW)
    def test_create_log(self):
        factory = RequestFactory()
        request = factory.get("/?a=b", HTTP_USER_AGENT="Mozilla/5.0")
        request.user = AnonymousUser()
        request.session = mock.Mock(session_key="foo")
        log: RequestLog = RequestLog.objects.create_log(
            request, category="foo", label="bar"
        )
        assert log.user is None
        assert log.session_key == "foo"
        assert log.http_method == "GET"
        assert log.request_path == "/"
        assert log.query_string == "a=b"
        assert log.http_user_agent == "Mozilla/5.0"
        assert log.http_referer == ""
        assert log.remote_addr == "127.0.0.1"
        assert log.category == "foo"
        assert log.label == "bar"
        assert log.timestamp == NOW
