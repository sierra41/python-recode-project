import typing


from starlette.datastructures import URL, Headers
from starlette.responses import PlainTextResponse, RedirectResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

ENFORCE_DOMAIN_WILDCARD = "Domain wildcard patterns must be like '*.example.com'."

# trusted_hosts.py : starlette에 정의가 되어있는 미들웨어
# 특정 도메인을 지정하고 해당 도메인만 유효한 것으로 체크
# 다만 starlette을 그대로 사용하면 except_path을 정의할 수 있는 기능이 없음.
# aws나 애저에서 로드밸런서를 사용하게 되면 내부아이피로 healthcheck를 하게 되는데 호스트 없이 아이피로 사용되기 때문에 except_path가 없으면 healthcheck가 전부 실패하게 됨


class TrustedHostMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        allowed_hosts: typing.Sequence[str] = None,
        except_path: typing.Sequence[str] = None,
        www_redirect: bool = True,
    ) -> None:
        if allowed_hosts is None:
            allowed_hosts = ["*"]
        if except_path is None:
            except_path = []
        for pattern in allowed_hosts:
            assert "*" not in pattern[1:], ENFORCE_DOMAIN_WILDCARD
            if pattern.startswith("*") and pattern != "*":
                assert pattern.startswith("*."), ENFORCE_DOMAIN_WILDCARD
        self.app = app
        self.allowed_hosts = list(allowed_hosts)
        self.allow_any = "*" in allowed_hosts
        self.www_redirect = www_redirect
        self.except_path = list(except_path)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        print("Hello Trusted")
        if self.allow_any or scope["type"] not in ("http", "websocket",):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        host = headers.get("host", "").split(":")[0]
        is_valid_host = False
        found_www_redirect = False
        for pattern in self.allowed_hosts:
            if (
                host == pattern
                or (pattern.startswith("*") and host.endswith(pattern[1:]))
                or URL(scope=scope).path in self.except_path
            ):
                is_valid_host = True
                break
            elif "www." + host == pattern:
                found_www_redirect = True

        if is_valid_host:
            await self.app(scope, receive, send)
        else:
            if found_www_redirect and self.www_redirect:
                url = URL(scope=scope)
                redirect_url = url.replace(netloc="www." + url.netloc)
                response = RedirectResponse(url=str(redirect_url))  # type: Response
            else:
                response = PlainTextResponse("Invalid host header", status_code=400)

            await response(scope, receive, send)