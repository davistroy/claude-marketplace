"""Tests for the SSRF guard on concept_analyzer's URL fetching.

Verifies that fetch_url_content (and its underlying validation helpers)
refuse to contact private, loopback, link-local, reserved, or otherwise
internal destinations -- including the cloud metadata address
169.254.169.254 -- before any network request is made, while still
allowing normal public hosts through. DNS resolution and the HTTP client
are mocked throughout; no real network calls are made.
"""

from __future__ import annotations

import socket
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from visual_explainer.concept_analyzer import (
    SSRFError,
    _check_host_is_safe,
    _validate_url_target,
    fetch_url_content,
)


def _fake_addrinfo(ip: str, family: int = socket.AF_INET) -> list[tuple]:
    """Build a socket.getaddrinfo-shaped result resolving to a single IP."""
    if family == socket.AF_INET:
        sockaddr = (ip, 0)
    else:
        sockaddr = (ip, 0, 0, 0)
    return [(family, socket.SOCK_STREAM, 6, "", sockaddr)]


class TestCheckHostIsSafe:
    """Tests for _check_host_is_safe -- the DNS resolution + IP range guard."""

    @pytest.mark.parametrize(
        "blocked_ip",
        [
            "169.254.169.254",  # cloud metadata endpoint
            "127.0.0.1",  # loopback
            "10.0.0.5",  # RFC-1918 private
            "172.16.0.1",  # RFC-1918 private
            "192.168.1.1",  # RFC-1918 private
            "169.254.0.1",  # link-local
            "0.0.0.0",  # unspecified
        ],
    )
    def test_rejects_blocked_ipv4_targets(self, blocked_ip):
        """Blocked IPv4 ranges must raise SSRFError."""
        with patch("socket.getaddrinfo", return_value=_fake_addrinfo(blocked_ip)):
            with pytest.raises(SSRFError):
                _check_host_is_safe("blocked.example.com")

    def test_rejects_ipv6_loopback(self):
        """IPv6 loopback (::1) must be rejected."""
        with patch(
            "socket.getaddrinfo",
            return_value=_fake_addrinfo("::1", family=socket.AF_INET6),
        ):
            with pytest.raises(SSRFError):
                _check_host_is_safe("blocked-v6.example.com")

    def test_rejects_ipv6_link_local(self):
        """IPv6 link-local (fe80::/10) must be rejected."""
        with patch(
            "socket.getaddrinfo",
            return_value=_fake_addrinfo("fe80::1", family=socket.AF_INET6),
        ):
            with pytest.raises(SSRFError):
                _check_host_is_safe("blocked-v6-linklocal.example.com")

    def test_rejects_ipv6_unique_local(self):
        """IPv6 unique local addresses (fc00::/7) must be rejected."""
        with patch(
            "socket.getaddrinfo",
            return_value=_fake_addrinfo("fd00::1", family=socket.AF_INET6),
        ):
            with pytest.raises(SSRFError):
                _check_host_is_safe("blocked-v6-ula.example.com")

    def test_allows_public_ipv4_host(self):
        """A hostname resolving to a public IP must be allowed through."""
        with patch("socket.getaddrinfo", return_value=_fake_addrinfo("93.184.216.34")):
            _check_host_is_safe("public.example.com")  # should not raise

    def test_raises_on_dns_failure(self):
        """A hostname that fails to resolve must raise SSRFError."""
        with patch("socket.getaddrinfo", side_effect=socket.gaierror("no such host")):
            with pytest.raises(SSRFError):
                _check_host_is_safe("nonexistent.invalid")


class TestValidateUrlTarget:
    """Tests for _validate_url_target -- scheme + host validation."""

    @pytest.mark.parametrize(
        "scheme_url", ["ftp://example.com/x", "file:///etc/passwd", "gopher://example.com"]
    )
    def test_rejects_disallowed_schemes(self, scheme_url):
        """Only http/https schemes are allowed."""
        with pytest.raises(SSRFError):
            _validate_url_target(scheme_url)

    def test_rejects_url_with_no_hostname(self):
        """A URL with no hostname (e.g. malformed) must be rejected."""
        with pytest.raises(SSRFError):
            _validate_url_target("http://")

    def test_allows_public_https_url(self):
        """A normal public https URL must pass validation."""
        with patch("socket.getaddrinfo", return_value=_fake_addrinfo("93.184.216.34")):
            _validate_url_target("https://public.example.com/page")  # should not raise


class TestFetchUrlContentSSRFGuard:
    """Tests that fetch_url_content applies the SSRF guard before fetching."""

    async def test_blocks_metadata_endpoint_before_any_request(self):
        """A URL resolving to the cloud metadata IP must be refused with no HTTP call made."""
        with (
            patch("socket.getaddrinfo", return_value=_fake_addrinfo("169.254.169.254")),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        ):
            with pytest.raises(SSRFError):
                await fetch_url_content("http://metadata.internal/latest/meta-data/")

            mock_get.assert_not_called()

    async def test_blocks_loopback_before_any_request(self):
        """A URL resolving to loopback must be refused with no HTTP call made."""
        with (
            patch("socket.getaddrinfo", return_value=_fake_addrinfo("127.0.0.1")),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        ):
            with pytest.raises(SSRFError):
                await fetch_url_content("http://sneaky.example.com/")

            mock_get.assert_not_called()

    async def test_blocks_private_ip_before_any_request(self):
        """A URL resolving to an RFC-1918 private address must be refused."""
        with (
            patch("socket.getaddrinfo", return_value=_fake_addrinfo("10.1.2.3")),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        ):
            with pytest.raises(SSRFError):
                await fetch_url_content("http://internal.example.com/")

            mock_get.assert_not_called()

    async def test_allows_normal_public_host(self):
        """A normal public host should be fetched and its text content returned."""
        mock_response = httpx.Response(
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"<html><body><main><p>Hello world</p></main></body></html>",
            request=httpx.Request("GET", "https://public.example.com/"),
        )

        with (
            patch("socket.getaddrinfo", return_value=_fake_addrinfo("93.184.216.34")),
            patch(
                "httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response
            ) as mock_get,
        ):
            result = await fetch_url_content("https://public.example.com/")

        assert "Hello world" in result
        mock_get.assert_called_once()

    async def test_rejects_redirect_to_private_address(self):
        """A redirect from a public host to a private address must be refused."""
        redirect_response = httpx.Response(
            status_code=302,
            headers={"location": "http://169.254.169.254/latest/meta-data/"},
            request=httpx.Request("GET", "https://public.example.com/"),
        )

        # First getaddrinfo call (initial URL) resolves public; the redirect
        # target re-validation call resolves to the metadata IP.
        addr_results = iter(
            [
                _fake_addrinfo("93.184.216.34"),  # initial validate
                _fake_addrinfo("169.254.169.254"),  # redirect target validate
            ]
        )

        with (
            patch("socket.getaddrinfo", side_effect=lambda *a, **kw: next(addr_results)),
            patch(
                "httpx.AsyncClient.get",
                new_callable=AsyncMock,
                return_value=redirect_response,
            ) as mock_get,
        ):
            with pytest.raises(SSRFError):
                await fetch_url_content("https://public.example.com/")

            # Only the initial request should have been made; the redirect
            # must be blocked before a second request is issued.
            mock_get.assert_called_once()

    async def test_rejects_disallowed_scheme_before_any_request(self):
        """A non-http(s) scheme must be rejected without touching the network."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            with pytest.raises(SSRFError):
                await fetch_url_content("file:///etc/passwd")

            mock_get.assert_not_called()
