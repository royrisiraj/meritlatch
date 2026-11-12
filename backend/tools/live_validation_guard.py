"""Validation-only, counted one-request transport for the existing SDK adapter.

No independent model integration, policy imports, credentials in diagnostics,
automatic retry, proxy routing, redirect, or second outbound request is allowed.
"""

import re

import httpx2


class DenySyncTransport(httpx2.BaseTransport):
    def handle_request(self, request):
        raise RuntimeError("Synchronous network requests are disabled for this validation.")


class SingleRequestGuard(httpx2.AsyncBaseTransport):
    def __init__(self, model_id="gemini-3.8-flash", transport=None):
        if model_id != "gemini-3.8-flash":
            raise ValueError("This checkpoint authorizes only gemini-3.8-flash.")
        self.model_id = model_id
        self.request_count = 0
        self.response_metadata = {}
        self.inner = transport if transport is not None else httpx2.AsyncHTTPTransport(retries=0, trust_env=False)

    async def handle_async_request(self, request):
        url = request.url
        if (request.method != "POST" or url.scheme != "https" or
            url.host != "generativelanguage.googleapis.com" or url.port not in {None, 443} or
            url.path != f"/v1beta/models/{self.model_id}:generateContent" or url.query or url.userinfo):
            raise RuntimeError("Validation destination is not the single approved inference endpoint.")
        if self.request_count:
            raise RuntimeError("One-request validation budget exhausted; no retry permitted.")
        # No await between checking/consuming the budget. Count attempted sends,
        # not proof of Google's processing, delivery, or billing.
        self.request_count += 1
        response = await self.inner.handle_async_request(request)
        await response.aread()
        # Keep only bounded numeric usage and a safe finish label, never payloads,
        # prompt text, headers, URLs, credentials, or reasoning traces.
        if response.is_success and len(response.content) <= 1_048_576:
            try:
                body = response.json()
                usage = body.get("usageMetadata") or {}
                names = {"promptTokenCount", "candidatesTokenCount", "totalTokenCount", "thoughtsTokenCount", "cachedContentTokenCount"}
                self.response_metadata["usage"] = {name: value for name, value in usage.items()
                    if name in names and type(value) is int and value >= 0}
                candidates = body.get("candidates") or []
                finish = candidates[0].get("finishReason") if candidates else None
                if isinstance(finish, str) and re.fullmatch(r"[A-Z_]{1,80}", finish):
                    self.response_metadata["finish_reason"] = finish
            except (ValueError, TypeError, AttributeError, KeyError, IndexError):
                pass
        return response

    def client_factory(self, **kwargs):
        from google import genai

        options = kwargs.pop("http_options")
        if options.retry_options.attempts != 1 or kwargs.get("vertexai") is not False or kwargs.get("enterprise") is not False:
            raise ValueError("One-attempt Developer API configuration required.")
        guarded = options.model_copy(update={
            "client_args": {"transport": DenySyncTransport(), "follow_redirects": False, "trust_env": False},
            "async_client_args": {"transport": self, "follow_redirects": False, "trust_env": False}})
        return genai.Client(http_options=guarded, **kwargs)

    async def aclose(self):
        await self.inner.aclose()
