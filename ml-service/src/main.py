import os
import base64
import hashlib
import secrets
from urllib.parse import urlencode
from fastapi import FastAPI, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
import requests
from pydantic import BaseModel

app = FastAPI()

# Конфигурация приложения VK


class VKConfig:
    CLIENT_ID = "52894113"  # Ваш client_id
    CLIENT_SECRET = ""  # Если есть (обычно для веб-приложений не нужен)
    OAUTH_URL = "https://id.vk.com/authorize"
    TOKEN_URL = "https://id.vk.com/oauth2/auth"
    # Должен совпадать с настройками в VK
    REDIRECT_URI = "http://localhost/callback"
    SCOPE = "friends,photos,offline"  # Запрашиваемые права доступа
    API_VERSION = "5.131"

# Хранилище для временных данных (в production используйте базу данных или Redis)


class Storage:
    code_verifiers = {}
    states = {}

# Генерация code_verifier и code_challenge для PKCE


def generate_pkce():
    # Генерируем строку длиной до 128 символов
    code_verifier = secrets.token_urlsafe(64)[:128]
    code_challenge = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(
        code_challenge).decode().replace("=", "")
    return code_verifier, code_challenge

# Маршрут для инициации авторизации


@app.get("/auth/vk")
async def auth_vk():
    # Генерируем PKCE параметры
    code_verifier, code_challenge = generate_pkce()

    # Генерируем случайный state для защиты от CSRF
    state = secrets.token_urlsafe(16)

    # Сохраняем code_verifier и state для проверки в callback
    Storage.code_verifiers[state] = code_verifier
    Storage.states[state] = state

    # Параметры запроса авторизации
    params = {
        "response_type": "code",
        "client_id": VKConfig.CLIENT_ID,
        "redirect_uri": VKConfig.REDIRECT_URI,
        "scope": VKConfig.SCOPE,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "v": VKConfig.API_VERSION,
    }

    # Формируем URL для перенаправления на VK ID
    auth_url = f"{VKConfig.OAUTH_URL}?{urlencode(params)}"
    return RedirectResponse(auth_url)

# Маршрут обратного вызова (callback) от VK


@app.get("/callback")
async def callback(
    request: Request,
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None),
):
    # Проверяем наличие ошибки
    if error:
        return JSONResponse(
            content={
                "error": error,
                "description": error_description,
            },
            status_code=400,
        )

    # Проверяем наличие кода и state
    if not code or not state:
        return JSONResponse(
            content={"error": "Missing code or state"},
            status_code=400,
        )

    # Проверяем state на соответствие
    if state not in Storage.states or state not in Storage.code_verifiers:
        return JSONResponse(
            content={"error": "Invalid state"},
            status_code=400,
        )

    # Получаем сохраненный code_verifier
    code_verifier = Storage.code_verifiers[state]

    # Формируем данные для запроса токена
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": VKConfig.CLIENT_ID,
        "redirect_uri": VKConfig.REDIRECT_URI,
        "code_verifier": code_verifier,
    }

    # Отправляем запрос на получение токена
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(
        VKConfig.TOKEN_URL, data=token_data, headers=headers)

    # Обрабатываем ответ
    if response.status_code == 200:
        token_data = response.json()

        # Очищаем временные данные
        Storage.code_verifiers.pop(state, None)
        Storage.states.pop(state, None)

        # Здесь вы можете сохранить токен в базу данных или сессию
        return JSONResponse(content=token_data)
    else:
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
        )

# Маршрут для обновления токена


@app.post("/refresh_token")
async def refresh_token(refresh_token: str):
    # Формируем данные для запроса обновления токена
    token_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": VKConfig.CLIENT_ID,
    }

    # Отправляем запрос на обновление токена
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(
        VKConfig.TOKEN_URL, data=token_data, headers=headers)

    # Обрабатываем ответ
    if response.status_code == 200:
        return JSONResponse(content=response.json())
    else:
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
        )

# Маршрут для получения информации о пользователе


@app.get("/user_info")
async def get_user_info(access_token: str):
    # Формируем данные для запроса информации о пользователе
    user_data = {
        "access_token": access_token,
        "client_id": VKConfig.CLIENT_ID,
        "v": VKConfig.API_VERSION,
        "q": "Кемерово"
    }

    # Отправляем запрос к API VK
    response = requests.get(
        "https://api.vk.com/method/groups.search",
        data=user_data,
    )

    # Обрабатываем ответ
    if response.status_code == 200:
        return JSONResponse(content=response.json())
    else:
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
        )
