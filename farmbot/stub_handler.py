from typing import Dict
from farmbot.farmbot import Farmbot
from farmbot.farmbot_connection import ErrorResponse, OkResponse
from paho.mqtt.client import Mqtt
from typing import Dict, Any


class StubHandler:
    def on_connect(self, bot: Farmbot, client: Mqtt) -> None: pass
    def on_change(self, bot: Farmbot, state: Dict[Any, Any]) -> None: pass
    def on_log(self, _bot: Farmbot, log: Dict[Any, Any]) -> None: pass
    def on_error(self, _bot: Farmbot, _response: ErrorResponse) -> None: pass
    def on_response(self, _bot: Farmbot, _response: OkResponse) -> None: pass
