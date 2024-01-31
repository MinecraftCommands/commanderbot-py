import asyncio
from typing import Any

import feedparser

__all__ = ("parse_async",)


async def parse_async(
    url_file_stream_or_string,
    etag=None,
    modified=None,
    agent=None,
    referrer=None,
    handlers=None,
    request_headers=None,
    response_headers=None,
    resolve_relative_uris=None,
    sanitize_html=None,
) -> dict[str, Any]:
    """
    Parse a feed from a URL, file, stream, or string.

    Parameters
    ----------
    url_file_stream_or_string :
        File-like object, URL, file path, or string. Both byte and text strings
        are accepted. If necessary, encoding will be derived from the response
        headers or automatically detected.

        Note that strings may trigger network I/O or filesystem access
        depending on the value. Wrap an untrusted string in
        a :class:`io.StringIO` or :class:`io.BytesIO` to avoid this. Do not
        pass untrusted strings to this function.

        When a URL is not passed the feed location to use in relative URL
        resolution should be passed in the ``Content-Location`` response header
        (see ``response_headers`` below).
    etag : ``str``
        HTTP ``ETag`` request header.
    modified : :type:`str | time.struct_time | datetime.datetime`
        HTTP ``Last-Modified`` request header.
    agent : ``str``
        HTTP ``User-Agent`` request header, which defaults to the value of :data:`feedparser.USER_AGENT`.
    referrer :
        HTTP ``Referrer`` [sic] request header.
    request_headers : :class:`dict[str, str]`
        A mapping of HTTP header name to HTTP header value to add to the
        request, overriding internally generated values.
    response_headers : :class:`dict[str, str]`
        A mapping of HTTP header name to HTTP header value. Multiple values may
        be joined with a comma. If a HTTP request was made, these headers
        override any matching headers in the response. Otherwise this specifies
        the entirety of the response headers.
    resolve_relative_uris : ``bool``
        Should feedparser attempt to resolve relative URIs absolute ones within
        HTML content?  Defaults to the value of
        :data:`feedparser.RESOLVE_RELATIVE_URIS`, which is ``True``.
    sanitize_html : ``bool``
        Should feedparser skip HTML sanitization? Only disable this if you know
        what you are doing!  Defaults to the value of
        :data:`feedparser.SANITIZE_HTML`, which is ``True``.

    Returns
    -------
    :class:`FeedParserDict`
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        feedparser.parse,
        url_file_stream_or_string,
        etag,
        modified,
        agent,
        referrer,
        handlers,
        request_headers,
        response_headers,
        resolve_relative_uris,
        sanitize_html,
    )
