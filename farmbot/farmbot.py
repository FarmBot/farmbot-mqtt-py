import paho.mqtt.client as mqtt
from urllib.request import urlopen, Request
import json
import uuid


class OkResponse():
    def __init__(self, id):
        self.id = id


class ErrorResponse():
    def __init__(self, id, errors):
        self.errors = errors
        self.id = id


class FarmbotConnection():
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

    def handle_connect(self, mqtt, userdata, flags, rc):
        for channel in self.channels:
            mqtt.subscribe(channel)
        self.bot.read_status()
        self.bot._handler.on_connect(self.bot, mqtt)

    def handle_message(self, mqtt, userdata, msg):
        if msg.topic == self.status_chan:
            self.handle_status(msg)

        if msg.topic == self.logs_chan:
            self.handle_log(msg)

        if msg.topic == self.incoming_chan:
            self.unpack_response(msg.payload)

    def unpack_response(self, payload):
        resp = json.loads(payload)
        kind = resp["kind"]
        label = resp["args"]["label"]
        if kind == "rpc_ok":
            self.handle_resp(label)
        if kind == "rpc_error":
            self.handle_error(label, resp["body"] or [])

    def handle_resp(self, label):
        # {
        #   'kind': 'rpc_ok',
        #   'args': { 'label': 'fd0ee7c9-6ca8-11eb-9d9d-eba70539ce61' },
        # }
        self.bot._handler.on_response(self.bot, OkResponse(label))
        return

    def handle_status(self, msg):
        self.bot.state = json.loads(msg.payload)
        self.bot._handler.on_change(self.bot, self.bot.state)
        return

    def handle_log(self, msg):
        log = json.loads(msg.payload)
        self.bot._handler.on_log(self.bot, log)
        return

    def handle_error(self, label, errors):
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
        self.bot._handler.on_error(self.bot, ErrorResponse(label, tidy_errors))
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


class StubHandler:
    def on_connect(self, bot, client): pass
    def on_change(self, bot, state): pass
    def on_log(self, _bot, log): pass
    def on_error(self, _bot, _response): pass
    def on_response(self, _bot, _response): pass


class FarmbotToken():
    @staticmethod
    def download_token(email,
                       password,
                       server="https://my.farm.bot"):
        """
        Returns a byte stream representation of the
        """
        req = Request(server + "/api/tokens")
        req.add_header("Content-Type", "application/json")
        data = {"user": {"email": email, "password": password}}
        string = json.dumps(data)
        as_bytes = str.encode(string)
        response = urlopen(req, as_bytes)

        return response.read()

    def __init__(self, raw_token):
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
    """
    This is what the bot's state tree looks like.
    This helper method creates an empty object that is mostly
    unpopulated.
    """
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
    @classmethod
    def login(cls,
              email,
              password,
              server="https://my.farm.bot"):
        """
        We reccomend that users store tokens rather than passwords.
        """
        token = FarmbotToken.download_token(email=email,
                                            password=password,
                                            server=server)
        return Farmbot(token)

    def __init__(self, raw_token):
        token = FarmbotToken(raw_token)
        self.username = token.bot
        self.password = token.jwt
        self.hostname = token.mqtt
        self.device_id = token.sub
        self._handler = StubHandler()

        self._connection = FarmbotConnection(self)
        self.state = empty_state()

    def connect(self, handler):
        """
        Attempt to connect to the MQTT broker.
        """
        self._handler = handler
        self._connection.start_connection()

    def position(self):
        """
        Convinence method to return the bot's current location
        as an (x, y, z) tuple.
        """
        position = self.state["location_data"]["position"]
        x = position["x"] or -0.0
        y = position["y"] or -0.0
        z = position["z"] or -0.0
        return (x, y, z)

    def _do_cs(self, kind, args, body=[]):
        """
        This is a private helper that wraps CeleryScript in
        an `rpc` node and sends it to the device over MQTT.
        """
        return self._connection.send_rpc({
            "kind": kind,
            "args": args,
            "body": body
        })

    def move_absolute(self, x, y, z, speed=100.0):
        """
        Move to an absolute XYZ coordinate at a speed percentage (default speed: 100%).
        """
        return self._do_cs("move_absolute", {
            "location": {"kind": "coordinate", "args": {"x": x, "y": y, "z": z, }},
            "speed": speed,
            "offset": {"kind": "coordinate", "args": zero_xyz}
        })

    def send_message(self, msg, type="info"):
        """
        Send a log message.
        """
        return self._do_cs("send_message",
                           {"message": msg, "message_type": type, })

    def emergency_lock(self):
        """
        Perform an emergency stop, thereby preventing any
        motor movement until `emergency_unlock()` is called.
        """
        return self._do_cs("emergency_lock", {})

    def emergency_unlock(self):
        """
        Unlock the Farmduino, allowing movement of previously
        locked motors.
        """
        return self._do_cs("emergency_unlock", {})

    def find_home(self):
        """
        Find the home (0) position for all axes.
        """
        return self._do_cs("find_home", {"speed": 100, "axis": "all"})

    def find_length(self, axis="all"):
        """
        Move to the end of each axis until a stall is detected,
        then set that distance as the maximum length.
        """
        return self._do_cs("calibrate", {"axis": axis})

    def flash_farmduino(self, package="farmduino"):
        """
        Flash microcontroller firmware. `package` is one of
        the following values: "arduino", "express_k10",
        "farmduino_k14", "farmduino"
        """
        return self._do_cs("flash_firmware", {"package": package})

    def go_to_home(self, axis="all", speed=100):
        """
        Move to the home position for a given axis at a
        particular speed.
        """
        return self._do_cs("home", {"speed": speed, "axis": axis})

    def move_relative(self, x, y, z, speed=100):
        """
        Move to a relative XYZ offset from the device's current
        position at a speed percentage (default speed: 100%).
        """
        return self._do_cs("move_relative",
                           {"x": x, "y": y, "z": z, "speed": speed})

    def power_off(self):
        """
        Deactivate FarmBot OS completely (shutdown). Useful
        before unplugging the power.
        """
        return self._do_cs("power_off", {})

    def read_status(self):
        """
        Read the status of the bot. Should not be needed unless you are first
        logging in to the device, since the device pushes new states out on
        every update.
        """
        self._do_cs("read_status", {})

    def reboot(self):
        """
        Restart FarmBot OS.
        """
        return self._do_cs("reboot", {"package": "farmbot_os"})

    def reboot_farmduino(self):
        """
        Reinitialize the FarmBot microcontroller firmware.
        """
        return self._do_cs("reboot", {"package": "arduino_firmware"})

    def factory_reset(self):
        """
        THIS WILL RESET THE SD CARD, deleting all non-factory data!
        * Be careful!! *
        """
        return self._do_cs("factory_reset", {"package": "farmbot_os"})

    def sync(self):
        """
        Download/apply all of the latest FarmBot API JSON resources (plants,
        account info, etc.) to the device.
        """
        return self._do_cs("sync", {})

    def take_photo(self):
        """
        Snap a photo and send to the API for post processing.
        """
        return self._do_cs("take_photo", {})

    def toggle_pin(self, pin_number):
        """
        Reverse the value of a digital pin.
        """
        return self._do_cs("toggle_pin", {"pin_number": pin_number})

    def update_farmbot_os(self):
        return self._do_cs("check_updates", {"package": "farmbot_os"})

    def read_pin(self, pin_number, pin_mode="digital"):
        """
        Read a pin
        """
        modes = {"digital": 0, "analog": 1}
        args = {
            "label": "pin" + str(pin_number),
            "pin_mode": modes[pin_mode] or (modes["digital"]),
            "pin_number": pin_number
        }
        return self._do_cs("read_pin", args)

    def write_pin(self, pin_number, pin_value, pin_mode="digital"):
        """
        Write to a pin
        """
        modes = {"digital": 0, "analog": 1}
        args = {
            "pin_mode": modes[pin_mode] or (modes["digital"]),
            "pin_number": pin_number,
            "pin_value": pin_value
        }
        return self._do_cs("write_pin", args)

    def set_servo_angle(self, pin_number, angle):
        """
        Set pins 4 or 5 to a value between 0 and 180.
        """
        return self._do_cs("set_servo_angle",
                           {"pin_number": pin_number, "pin_value": angle})
