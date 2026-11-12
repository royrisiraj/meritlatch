"""Bound JSON request bodies before parsing, including chunked/missing-length input."""

from fastapi.responses import JSONResponse


class BoundedBody:
    def __init__(self, app, maximum=16384):
        self.app = app
        self.maximum = maximum

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        messages = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.maximum:
                response = JSONResponse(status_code=413, headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
                    content={"decision": "DENY", "reason_codes": ["REQUEST_TOO_LARGE"], "guidance": "Use a JSON request under 16 KiB."})
                await response(scope, receive, send)
                return
            messages.append(message)
            if not message.get("more_body", False):
                break

        async def bounded_receive():
            if messages:
                return messages.pop(0)
            return await receive()

        await self.app(scope, bounded_receive, send)
