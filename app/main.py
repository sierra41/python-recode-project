from dataclasses import asdict
from typing import Optional

import uvicorn
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.common.consts import EXCEPT_PATH_LIST, EXCEPT_PATH_REGEX
from app.database.conn import db
from app.common.config import conf
from app.middlewares.token_validator import AccessControl
from app.middlewares.trusted_hosts import TrustedHostMiddleware
from app.routes import index, auth



# main.py
## main.py 파일에 생성한 app 객체 : FastAPI의 핵심 객체
## app 객체를 통해 FastAPI의 설정
## 프로젝트의 전체적인 환경을 설정
# 참조 :https://wikidocs.net/175950

# -------------------------------------
# app = FastAPI()
# @app.get("/")
# def read_root():
#     return {"Hello": "World"}
# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}
# -------------------------------------
# 고도화

def create_app():
    """
    앱 함수 실행
    :return:
    """
    c = conf()
    app = FastAPI()
    conf_dict = asdict(c)
    db.init_app(app, **conf_dict)
    ## 데이터베이스 이니셜라이즈

    ## 레디스 이니셜라이즈

    ## 미들웨어 정의
    # 가장 밑에 있는 미들웨어부터 실행
    # 따라서 AccessControl 미들웨어가 CORSMiddleware 미들웨어 밑에 위치한다면,
    # CORSMiddleware 미들웨어가 동작하기 전에 AccessControl 미들웨어부터 실행하므로 백엔드의 도메인과 프론트엔드의 도메인이 다른 경우 항상 에러가 발생.
    #  ->> 처음 요청 전에 옵션이라는 메소드를 날리는데 프리플라이트는 엑세스토큰을 가지고 있지 않다. 따라서 옵션에서 응답을 받을 수 없기 때문에 에러 발생
    # 프리팔라이트 요청 : 브라우저에서 실제 요청 이전에 서버의 허용 여부를 확인하기 위해 PTIONS 메서드로 서버에 보내는 것. 서버에서는 헤더에 혀용여부를 포함하여 응답.
    app.add_middleware(
        AccessControl, except_path_list=EXCEPT_PATH_LIST, except_path_regex=EXCEPT_PATH_REGEX)
    app.add_middleware(
        CORSMiddleware,
        # 특정 도메인에서 특정 호스트로만 접속 가능하도록 정의하는 미들웨어.
        # 해당 미들웨어가 없으면 백엔드의 도메인과 프론트엔드의 도메인이 같아야만 응답을 주고 받을 수 있다.
        allow_origins=conf().ALLOW_SITE,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=conf().TRUSTED_HOSTS, except_path=["/health"])

    ## 라우터 정의
    app.include_router(index.router)
    app.include_router(auth.router, tags=["Authentication"], prefix="/auth")
    return app


app = create_app()

if __name__ == "__main__":
    #logger.info("----------__main__ start----------");
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
