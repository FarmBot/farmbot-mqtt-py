import json
from urllib.request import urlopen, Request


class FarmbotToken():
    bot: str
    iss: str
    jti: str
    mqtt_ws: str
    mqtt: str
    vhost: str
    # "subject". This is your bot"s device ID as an integer
    sub: int
    # "expiration" UNIX timestamp
    exp: int
    # "Issued at" UNIX Timestamp
    iat: int

    @staticmethod
    def download_token(email: str,
                       password: str,
                       server: str = "https://my.farm.bot") -> bytes:
        req = Request(server + "/api/tokens")
        req.add_header("Content-Type", "application/json")
        data = {"user": {"email": email, "password": password}}
        string = json.dumps(data)
        as_bytes = str.encode(string)
        response = urlopen(req, as_bytes)

        return response.read()

    def __init__(self, raw_token: bytes):
        token_data = json.loads(raw_token)
        self.raw_token = raw_token
        token = token_data["token"]["unencoded"]
        self.jwt = token_data["token"]["encoded"]

        self.bot = token["bot"]
        self.exp = token["exp"]
        self.iat = token["iat"]
        self.iss = token["iss"]
        self.jti = token["jti"]
        self.mqtt = token["mqtt"]
        self.mqtt_ws = token["mqtt_ws"]
        self.sub = token["sub"]
        self.vhost = token["vhost"]
