from datetime import datetime, timedelta

import bcrypt
import jwt
from sqlalchemy.orm import Session # 타이핑을 위해 가져옴
from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse # json 형태로 response 해주는 역할

from app.common.consts import JWT_SECRET, JWT_ALGORITHM
# 처음 값을 JWT_SECRET으로 인코딩을 하고 같은 값이 들어오면 디코딩을 하여 확인하는 용도. 손상된
from app.database.conn import db
from app.database.schema import Users
from app.models import SnsType, Token, UserToken, UserRegister  # 객체화 하기 위한

"""
1. 구글 로그인을 위한 구글 앱 준비 (구글 개발자 도구)
2. FB 로그인을 위한 FB 앱 준비 (FB 개발자 도구)
3. 카카오 로그인을 위한 카카오 앱준비( 카카오 개발자 도구)
4. 이메일, 비밀번호로 가입 (v)
5. 가입된 이메일, 비밀번호로 로그인, (v)
6. JWT 발급 (v)
7. 이메일 인증 실패시 이메일 변경
8. 이메일 인증 메일 발송
9. 각 SNS 에서 Unlink
10. 회원 탈퇴
11. 탈퇴 회원 정보 저장 기간 동안 보유(법적 최대 한도차 내에서, 가입 때 약관 동의 받아야 함, 재가입 방지 용도로 사용하면 가능)
"""

router = APIRouter()


# @router - 엔드포인트
# @router 와 연결되어 있는 def 는 async 적용. @router 아닌 def 는 async 사용하지 않아도 괜찮음.
@router.post("/register/{sns_type}", status_code=200, response_model=Token)
async def register(sns_type: SnsType, reg_info: UserRegister, session: Session = Depends(db.session)):
    """
    회원가입 API
    :param sns_type:
    :param reg_info:
    :param session:
    :return:
    """
    if sns_type == SnsType.email:
        # 1. 중복이메일 확인
        is_exist = await is_email_exist(reg_info.email)
        # reg_info: UserRegister -> UserRegister 객체로 받아짐.
        if not reg_info.email or not reg_info.pw: # UserRegister에서 email, pw 값이 없는 경우
            return JSONResponse(status_code=400, content=dict(msg="Email and PW must be provided"))
            # 이렇게 명시적으로 JSONResponse 에러를 보내는 방식말고 raise 로 에러 처리하는 방식을 주로 사용함.
            # raise 를 이용하여 에러를 보내고, 해당 에러를 미들웨어가 잡아서 자동으로 미리 지정한 코드로 처리하는 형태.
        if is_exist:
            return JSONResponse(status_code=400, content=dict(msg="EMAIL_EXISTS"))
        # 2. 비밀번호 해시 후 유저 정보 저장
        hash_pw = bcrypt.hashpw(reg_info.pw.encode("utf-8"), bcrypt.gensalt())
        # 회원가입을 할때 bcrypt 라이브러리를 사용하여, 패스워드를 해시
        # bcrypt : 해시함수. 해시는 바이트 코드만 가능. gensalt() - 이용하여 해시 암호화의 정도가 달라짐.
        # bcrypt.hashpw() - 해시된 pw를 반환함
        # 2-2 유저 저장
        new_user = Users.create(session, auto_commit=True, pw=hash_pw, email=reg_info.email)
        # 이전 강의에서는 Users().create() 방식으로 유저를 생성했으나 지금은 클래스메소드로 변경하여 Users.create()로 사용가능.
        # 3. 저장된 유저 정보를 기반으로 jwt 발급
        token = dict(
            Authorization=f"Bearer {create_access_token(data=UserToken.from_orm(new_user).dict(exclude={'pw', 'marketing_agree'}), )}")
                                                         # UserToken - json으로 변경. # (exclude={'pw', 'marketing_agree'}) - pw와 marketing_agree는 제외하겠다는 의미
           # Authorization=f"Bearer 대신 access_token=f"Bearer 로 사용해도 되지만 Authorization을 쓰는 게 나중에 플러터에서 사용하기 편하다.
        return token
    return JSONResponse(status_code=400, content=dict(msg="NOT_SUPPORTED"))
    # return   "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NSwiZW1haWwiOiJmc2Rmd0BnbWFpbC5jb20iLCJuYW1lIjpudWxsLCJwaG9uZV9udW1iZXIiOm51bGwsInByb2ZpbGVfaW1nIjpudWxsLCJzbnNfdHlwZSI6bnVsbH0.9gDyoKPs5ma4QLF-7Lwv9cJdhAOovImDHfv3zBzKvLA"
        # 4강 기준 만료가 안되는 토큰
@router.post("/login/{sns_type}", status_code=200)
async def login(sns_type: SnsType, user_info: UserRegister):
    if sns_type == SnsType.email:
        # 1. 이메일 유무 확인
        is_exist = await is_email_exist(user_info.email)
        if not user_info.email or not user_info.pw:
            return JSONResponse(status_code=400, content=dict(msg="Email and PW must be provided'"))
        if not is_exist:
            return JSONResponse(status_code=400, content=dict(msg="NO_MATCH_USER"))
        user = Users.get(email=user_info.email)
        # 2. 비밀번호 해시 후 db 저장된 비밀번호와 비교
        is_verified = bcrypt.checkpw(user_info.pw.encode("utf-8"), user.pw.encode("utf-8"))
        #  bcrypt 라이브러리를 사용 비밀번호를 다시 해시 하여, 패스워드
        if not is_verified:
            return JSONResponse(status_code=400, content=dict(msg="NO_MATCH_USER")) # 이메일 유무와 패스워드 정확도의 에러코드는 동일하게 하는 것이 보안에 좋음.
        # 3. 완료 후 저장된 유저 정보를 기반으로 jwt 발급
        token = dict(Authorization=f"Bearer {create_access_token(data=UserToken.from_orm(user).dict(exclude={'pw', 'marketing_agree'}),)}")
        return token
    return JSONResponse(status_code=400, content=dict(msg="NOT_SUPPORTED"))

async def is_email_exist(email: str):
    get_email = Users.get(email=email)
    if get_email:
        return True
        #return get_email 로그인한 이메일값의 사용이 필요하면 이런식으로도 사용 가능
    return False



def create_access_token(*, data: dict = None, expires_delta: int = None):
    to_encode = data.copy()
    if expires_delta:
        to_encode.update({"exp": datetime.utcnow() + timedelta(hours=expires_delta)})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


