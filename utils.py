import jwt
from datetime import datetime, timedelta, timezone
from bcrypt import hashpw, gensalt, checkpw
from fastapi import Request


def read_public_key():
    with open("routers/public_key.txt") as file:
        return file.read()


def read_private_key():
    with open("routers/private_key.txt") as file:
        return file.read()


private_key = read_private_key()
public_key = read_public_key()


def request_decode_jwt(request: Request) -> dict:
    '''
    ручное декодирование jwt из request
    '''
    auth_header = request.headers.get("Authorization")
    payload = None
    if not auth_header or not auth_header.startswith("Bearer"):
        return None
    try:
        token = auth_header.split(" ")[1]
        payload = jwt_decode(token)
        if isinstance(payload, dict):
            return payload
    except: 
        payload = None
        return payload


def jwt_encode(user_id: int, role: str):
    '''
    создание jwt с полезной информаией о айди и роли
    '''
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        "role": role,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def jwt_decode(token: str):
    '''
    декод jwt для авторизации
    '''
    try:
        decoded = jwt.decode(token, public_key, algorithms=["RS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def set_password(password: str) -> str:
    '''
    установка пароля
    '''
    password = password.encode("utf-8")
    salt = gensalt()
    hashed = hashpw(password, salt)
    return hashed.decode("utf-8")


def check_password(hash_password: str, plain_password: str) -> bool:
    '''
    проверка пароля
    '''
    return checkpw(plain_password.encode("utf-8"), hash_password.encode("utf-8"))
