from farmbot.stub_handler import StubHandler
from farmbot_connection import FarmbotConnection
from farmbot_token import FarmbotToken

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

    def move_absolute(self, x: float, y: float, z: float, speed: float = 100.0) -> str:
        return self.connection.send_rpc({
            "kind": "move_absolute",
            "args": {
                "location": {
                    "kind": "coordinate",
                    "args": {
                        "x": x,
                        "y": y,
                        "z": z,
                    }
                },
                "speed": speed,
                "offset": {
                    "kind": "coordinate",
                    "args": zero_xyz
                }
            }
        })

    def send_message(self, msg: str) -> str:
        # assertion busy debug error fun info success warn
        return self.connection.send_rpc({
            "kind": "send_message",
            "args": {
                "message": msg,
                "message_type": "info",
            }
        })

    def noop(self, _other):
        pass
