import paho.mqtt.client as mqtt
from typing import Any, Dict, List, Tuple, Type, TypedDict
from urllib.request import urlopen, Request
import json
import uuid


class Message(TypedDict):
    message: str


class Label(TypedDict):
    label: str


class RpcOK(TypedDict):
    kind: str
    args: Label


class Explanation(TypedDict):
    kind: str
    args: Message


class OkResponse():
    def __init__(self, id: str):
        self.id = id


class ErrorResponse():
    def __init__(self, id: str, errors: List[str]):
        self.errors = errors
        self.id = id


class FarmbotConnection():
    mqtt: mqtt.Client
    channels: Tuple[str, str, str]
    incoming_chan: str
    logs_chan: str
    status_chan: str

    def __init__(self, bot, mqtt=mqtt.Client()):
        self.bot = bot
        self.mqtt = mqtt
        u = bot.username
        self.mqtt.username_pw_set(u, bot.password)
        # bot/device_000/from_clients
        # bot/device_000/from_device
        # bot/device_000/logs
        # bot/device_000/status
        # bot/device_000/sync/#
        # bot/device_000/ping/#
        # bot/device_000/pong/#
        self.status_chan = "bot/" + u + "/status"
        self.logs_chan = "bot/" + u + "/logs"
        self.incoming_chan = "bot/" + u + "/from_device"
        self.outgoing_chan = "bot/" + u + "/from_clients"
        self.channels = (
            self.status_chan,
            self.logs_chan,
            self.incoming_chan
        )

    def start_connection(self):
        # Attach event handlers:
        self.mqtt.on_connect = self.handle_connect
        self.mqtt.on_message = self.handle_message

        # Finally, connect to the server:
        self.mqtt.connect(self.bot.hostname, 1883, 60)

        self.mqtt.loop_forever()

    def handle_connect(self, mqtt: mqtt.Client, userdata: None, flags: None, rc: None):
        for channel in self.channels:
            mqtt.subscribe(channel)
        self.bot.read_status()
        self.bot.handler.on_connect(self.bot, mqtt)

    def handle_message(self, mqtt: mqtt.Client, userdata: None, msg: mqtt):
        if msg.topic == self.status_chan:
            self.handle_status(msg)

        if msg.topic == self.logs_chan:
            self.handle_log(msg)

        if msg.topic == self.incoming_chan:
            self.unpack_response(msg.payload)

    def unpack_response(self, payload: str):
        resp = json.loads(payload)
        kind = resp["kind"]
        label = resp["args"]["label"]
        if kind == "rpc_ok":
            self.handle_resp(label)
        if kind == "rpc_error":
            self.handle_error(label, resp["body"] or [])

    def handle_resp(self, label: str):
        # {
        #   'kind': 'rpc_ok',
        #   'args': { 'label': 'fd0ee7c9-6ca8-11eb-9d9d-eba70539ce61' },
        # }
        self.bot.handler.on_response(self.bot, OkResponse(label))
        return

    def handle_status(self, msg):
        self.bot.state = json.loads(msg.payload)
        self.bot.handler.on_change(self.bot, self.bot.state)
        return

    def handle_log(self, msg):
        log = json.loads(msg.payload)
        self.bot.handler.on_log(self.bot, log)
        return

    def handle_error(self, label: str, errors: List[Explanation]):
        # {
        #   'kind': 'rpc_error',
        #   'args': { 'label': 'fd0ee7c8-6ca8-11eb-9d9d-eba70539ce61' },
        #   'body': [
        #       { 'kind': 'explanation', 'args': { 'message': '~ERROR~' } },
        #       { 'kind': 'explanation', 'args': { 'message': '~ERROR~' } },
        #     ],
        # }

        tidy_errors = []
        for error in errors:
            args = error["args"] or {"message": "No message provided"}
            message = args["message"]
            tidy_errors.append(message)
        self.bot.handler.on_error(self.bot, ErrorResponse(label, tidy_errors))
        return

    def send_rpc(self, rpc):
        label = str(uuid.uuid1())
        message = {"kind": "rpc_request", "args": {"label": label}}
        if isinstance(rpc, list):
            message["body"] = rpc
        else:
            message["body"] = [rpc]
        payload = json.dumps(message)
        self.mqtt.publish(self.outgoing_chan, payload)
        return label


class Farmbot():
    username: str
    password: str
    hostname: str
    device_id: int
    connection: FarmbotConnection

    @classmethod
    def login(cls,
              email: str,
              password: str,
              server: str = "https://my.farm.bot"):
        """
        We reccomend that users store tokens rather than passwords.
        """
        token = FarmbotToken.download_token(email=email,
                                            password=password,
                                            server=server)
        return Farmbot(token)

    def __init__(self, raw_token: bytes):
        token = FarmbotToken(raw_token)
        self.username = token.bot
        self.password = token.jwt
        self.hostname = token.mqtt
        self.device_id = token.sub
        self.handler = StubHandler()

        self.connection = FarmbotConnection(self)
        self.state = empty_state()

    def connect(self, handler):
        self.handler = handler
        self.connection.start_connection()

    def position(self):
        position = self.state["location_data"]["position"]
        x = position["x"] or -0.0
        y = position["y"] or -0.0
        z = position["z"] or -0.0
        return (x, y, z)

    def _do_cs(self, kind, args, body=[]):
        return self.connection.send_rpc({
            "kind": kind,
            "args": args,
            "body": body
        })

    def move_absolute(self, x: float, y: float, z: float, speed: float = 100.0) -> str:
        return self._do_cs("move_absolute", {
            "location": {"kind": "coordinate", "args": {"x": x, "y": y, "z": z, }},
            "speed": speed,
            "offset": {"kind": "coordinate", "args": zero_xyz}
        })

    def send_message(self, msg: str) -> str:
        return self._do_cs("send_message", {"message": msg, "message_type": "info", })

    def emergency_lock(self): raise "NOT IMPLEMENTED"
    def emergency_unlock(self): raise "NOT IMPLEMENTED"
    def find_home(self): raise "NOT IMPLEMENTED"
    def find_length(self): raise "NOT IMPLEMENTED"
    def flash_farmduino(self): raise "NOT IMPLEMENTED"
    def go_to_home(self): raise "NOT IMPLEMENTED"
    def lua(self): raise "NOT IMPLEMENTED"
    def move_relative(self): raise "NOT IMPLEMENTED"
    def ping(self): raise "NOT IMPLEMENTED"
    def power_off(self): raise "NOT IMPLEMENTED"
    def read_pin(self): raise "NOT IMPLEMENTED"
    def read_status(self): return self._do_cs("read_status", {})
    def reboot_farmduino(self): raise "NOT IMPLEMENTED"
    def reboot(self): raise "NOT IMPLEMENTED"
    def reset_farmbot_os(self): raise "NOT IMPLEMENTED"
    def reset_farmduino(self): raise "NOT IMPLEMENTED"
    def set_servo_angle(self): raise "NOT IMPLEMENTED"
    def set_zero(self): raise "NOT IMPLEMENTED"
    def sync(self): raise "NOT IMPLEMENTED"
    def take_photo(self): raise "NOT IMPLEMENTED"
    def toggle_pin(self): raise "NOT IMPLEMENTED"
    def update_farmbot_os(self): raise "NOT IMPLEMENTED"
    def write_pin(self): raise "NOT IMPLEMENTED"


class StubHandler:
    def on_connect(self, bot: Farmbot, client: mqtt.Client) -> None: pass
    def on_change(self, bot: Farmbot, state: Dict[Any, Any]) -> None: pass
    def on_log(self, _bot: Farmbot, log: Dict[Any, Any]) -> None: pass
    def on_error(self, _bot: Farmbot, _response: ErrorResponse) -> None: pass
    def on_response(self, _bot: Farmbot, _response: OkResponse) -> None: pass


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

    @ staticmethod
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


empty_xyz = {"x": None, "y": None, "z": None}
zero_xyz = {"x": 0, "y": 0, "z": 0}


def empty_state():
    return {
        "configuration": {},
        "informational_settings": {},
        "jobs": {},
        "location_data": {
            "axis_states": empty_xyz,
            "load": empty_xyz,
            "position": empty_xyz,
            "raw_encoders": empty_xyz,
            "scaled_encoders": empty_xyz,
        },
        "mcu_params": {},
        "pins": {},
        "user_env": {}
    }
