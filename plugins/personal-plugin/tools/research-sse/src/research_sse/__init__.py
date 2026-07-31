"""Accumulate an Anthropic Messages streaming (SSE) response into report text.

Reads an event stream on stdin, writes the concatenated assistant text to
stdout, and reports the terminal outcome through the process exit status.
Stdlib only — this package parses a stream somebody else fetched, so it needs
no HTTP client, no SDK, no API key, and no network.
"""

__version__ = "0.1.0"
