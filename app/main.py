from dataclasses import asdict
from typing import Union
from typing import Optional

import uvicorn
from fastapi import FastAPI

from app.common.config import conf
from app.database.conn import db
from app.router import index
from app.util.log import logger


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

    ## 라우터 정의
    app.include_router(index.router)
    return app


app = create_app()

if __name__ == "__main__":
    #logger.info("----------__main__ start----------");
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
