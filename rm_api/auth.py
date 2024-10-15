from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from rm_api import API

TOKEN_URL = "{0}token/json/2/device/new"
TOKEN_REFRESH_URL = "{0}token/json/2/user/new"


def get_token(api: 'API'):
    code = input("Enter your connect code: ")
    response = api.session.post(
        TOKEN_URL.format(api.uri),
        json={
            "code": code,
            "deviceDesc": "desktop-windows",
            "deviceID": uuid4().hex,
            "secret": ""
        },
        headers={
            "Authorization": f"Bearer "
        }
    )
    if response.status_code != 200:
        print(f'Got status code {response.status_code}')
        return get_token(api)

    with open("token", "w") as f:
        f.write(response.text)

    return response.text


def refresh_token(api: 'API', token: str):
    response = api.session.post(
        TOKEN_REFRESH_URL.format(api.uri),
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code != 200:
        return refresh_token(api, get_token(api))

    return response.text
