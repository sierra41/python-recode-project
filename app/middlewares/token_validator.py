import time
import typing
import re
import jwt

from fastapi.params import Header
from jwt import PyJWTError
from pydantic import BaseModel
from starlette.requests import Request
from starlette.datastructures import URL, Headers
from starlette.responses import JSONResponse
from starlette.responses import PlainTextResponse, RedirectResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from app.common import config, consts
from app.common.config import conf
from app.models import UserToken

from app.utils.date_utils import D

# token_validator.py : 들어오는 모든 요청에 대해서 토근 검증하기 위해 만든 미들웨어


class AccessControl:
    def __init__(
            self,
            app: ASGIApp,
            # except_path_list, except_path_regex 토큰 검사를 하지 않는 두가지 path.
            # 로그인과 회원가입 등을 주로 적용
            except_path_list: typing.Sequence[str] = None,
            except_path_regex: str = None,
    ) -> None:
        if except_path_list is None:
            except_path_list = ["*"]
        self.app = app
        self.except_path_list = except_path_list
        self.except_path_regex = except_path_regex

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        print(self.except_path_regex) # ^(/docs|/redoc|/auth)
        print(self.except_path_list) # ['/', '/openapi.json']

        request = Request(scope=scope)
        headers = Headers(scope=scope)

        #request.stats.temptemptmep = "무슨 값이든 적을 수 있음" : 미들웨어에서 체크한 값을 엔드포인트에서 사용가능하도록 값을 입력하는 용도
        request.state.req_time = D.datetime() # 요청시간

        request.state.start = time.time() # 해당 엔드포인트가 실행하는 데 걸린 시간을 확인하기 위하여
        request.state.inspect = None #500에러 - 어떤 파일 몇번째줄에서 에러가 발생한건지 로깅용 # sentre
        request.state.user = None #token decording 내용. 가능하면 db조회를 최소화
        request.state.is_admin_access = None
        ip_from = request.headers["x-forwarded-for"] if "x-forwarded-for" in request.headers.keys() else None
        # x-forwarded-for : aws ip

        if await self.url_pattern_check(request.url.path,
                                        self.except_path_regex) or request.url.path in self.except_path_list:
            return await self.app(scope, receive, send)

        if request.url.path.startswith("/api"):
            # api 인경우 헤더로 토큰 검사
            if "Authorization" in request.headers.keys():
                request.state.user = await self.token_decode(access_token=request.headers.get("Authorization"))
                # 토큰 없음
            else:
                if "Authorization" not in request.headers.keys():
                    response = JSONResponse(status_code=401, content=dict(msg="AUTHORIZATION_REQUIRED"))
                    return await response(scope, receive, send)
        else:
            # 템플릿 렌더링인 경우 쿠키에서 토큰 검사
            print(request.cookies)
            # request.cookies["Authorization"] = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6MTQsImVtYWlsIjoia29hbGFAZGluZ3JyLmNvbSIsIm5hbWUiOm51bGwsInBob25lX251bWJlciI6bnVsbCwicHJvZmlsZV9pbWciOm51bGwsInNuc190eXBlIjpudWxsfQ.4vgrFvxgH8odoXMvV70BBqyqXOFa2NDQtzYkGywhV48"

            if "Authorization" not in request.cookies.keys():
                response = JSONResponse(status_code=401, content=dict(msg="AUTHORIZATION_REQUIRED"))
                return await response(scope, receive, send)

            request.state.user = await self.token_decode(access_token=request.cookies.get("Authorization"))

        request.state.req_time = D.datetime()
        print(D.datetime()) # 2024-03-06 06:22:51.908516
        print(D.date()) # 2024-03-06
        print(D.date_num()) # 20240306

        print(request.cookies)
        print(headers)
        #Headers({'host': '0.0.0.0:8080', 'connection': 'keep-alive', 'cache-control': 'max-age=0', 'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'accept-encoding': 'gzip, deflate', 'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'})
        res = await self.app(scope, receive, send)
        return res

    @staticmethod
    async def url_pattern_check(path, pattern):
        result = re.match(pattern, path)
        if result:
            return True
        return False

    @staticmethod
    async def token_decode(access_token):
        """
        :param access_token:
        :return:
        """
        try:
            access_token = access_token.replace("Bearer ", "")
            payload = jwt.decode(access_token, key=consts.JWT_SECRET, algorithms=[consts.JWT_ALGORITHM])
        except PyJWTError as e:
            print(e)
            # Raise Error
        return payload