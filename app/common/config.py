from dataclasses import dataclass, asdict
from os import environ, path

base_dir = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))


# config.py
## 환경별 변수


# dictionary 형식으로 가지고 오고 싶을 경우에 dataclass 사용
@dataclass
class Config:
  """
  기본 Configuration
  """
  BASE_DIR = base_dir

  DB_POOL_RECYCLE: int = 900
  DB_ECHO: bool = True


@dataclass
class LocalConfig(Config):
  PROJ_RELOAD: bool = True


@dataclass
class ProdConfig(Config):
  PROJ_RELOAD: bool = False

# def abc(DB_ECHO=None, DB_POOL_RECYCLE=None, **kwargs):
#     print(DB_ECHO, DB_POOL_RECYCLE)
# arg = asdict(LocalConfig())
# abc(**arg) - 각각 값으로 가져옴

def conf():
  """
  환경 불러오기
  :return:
  """
  config = dict(prod=ProdConfig(), local=LocalConfig())
  return config.get(environ.get("API_ENV", "local"))
# API_ENV가 없으면 local 사용하라는 의미
## 파이썬에서는 switch case 가 없어서 이렇게 사용
