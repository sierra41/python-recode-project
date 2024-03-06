# consts.py
## 환경에도 변하지 않는 상수

#WEBSITE_ADDR = "youtube.com"
JWT_SECRET = "ABCD1234!" # 나중에는 aws secret manager에서 동적으로 관리할 것
JWT_ALGORITHM = "HS256"

# "/" : main. healthcheck용, "/openapi.json": /docs /redoc 에서 api만들 때 사용하는 파일
EXCEPT_PATH_LIST = ["/", "/openapi.json"]
# /docs /redoc : 스웨거 등 문서 /auth : 로그인, 회원가입 등 인증
EXCEPT_PATH_REGEX = "^(/docs|/redoc|/auth)"