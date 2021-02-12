from typing import Tuple, List, Type, TypedDict
import json
import paho.mqtt.client as mqtt
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
        self.bot.handler.on_connect(self.bot, mqtt)

    def handle_message(self, mqtt: mqtt.Client, userdata: None, msg: mqtt):
        if msg.topic == self.status_chan:
            self.handle_status(msg)

        if msg.topic == self.logs_chan:
            self.handle_log(msg)

        if msg.topic == self.incoming_chan:
            resp = json.loads(msg.payload)
            kind = resp["kind"]
            label = (resp["args"] or {})["label"] or "unknown"
            if kind == "rpc_ok":
                self.handle_resp(label)
            if kind == "rpc_error":
                self.handle_error(label, resp["body"] or [])

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

    def handle_status(self, msg):
        self.bot.state = json.loads(msg.payload)
        self.bot.handler.on_change(self.bot, self.bot.state)
        return

    def handle_log(self, msg):
        log = json.loads(msg.payload)
        self.bot.handler.on_log(self.bot, log)
        return

    def handle_resp(self, label: str):
        # { 'kind': 'rpc_ok', 'args': { 'label': 'fd0ee7c9-6ca8-11eb-9d9d-eba70539ce61' }, }
        response = OkResponse(label)
        self.bot.handler.on_response(self.bot, response)
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
        resp = ErrorResponse(label, tidy_errors)
        self.bot.handler.on_error(self.bot, resp)
        return
