from enum import Enum

from pydantic.main import BaseModel
from pydantic.networks import EmailStr

# pydantic 모델들 작성
# 입력된 request body나 그 외 데이터들의 유효성을 검사해주는 기능
# Json을 모델로 바꾸고 모델을 Json으로 바꿔서 빠르게 유효성을 검사.
## BaseModel로 대체하여
# pydantic 을 적용하여 fastapi가 다른 웹 프레임워크에 비해 빠르게 실행 가능.

class UserRegister(BaseModel):
    #pip install 'pydantic[email]'
    email: str = None
    pw: str = None
    # 파이썬(인터프리터 언어)은 타입을 지정해둔다고 빨라지지 않음.
    # 가독성을 위한 작업

class SnsType(str, Enum):
    email: str = "email"
    facebook: str = "facebook"
    google: str = "google"
    kakao: str = "kakao"
    # 여기서 정해진 Enum 외의 값이 들어오면 422 error
    # request model


class Token(BaseModel):
    Authorization: str = None
    # response model

class UserToken(BaseModel):
    # token을 객체화하여 사용하기 위해 생성
    id: int
    pw: str = None
    email: str = None
    name: str = None
    phone_number: str = None
    profile_img: str = None
    sns_type: str = None
    class Config:
        orm_mode = True