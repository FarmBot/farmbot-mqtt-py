from unittest import mock
import farmbot as fb
import json

fake_bytes = b"{\"token\": {\"unencoded\": {\"aud\": \"unknown\", \"sub\": 1, \"iat\": 1609876696, \"jti\": \"46694c2f-2a03-4e3f-84bd-7ec22fb58c1f\", \"iss\": \"//10.11.1.235:3000\", \"exp\": 1613332696, \"mqtt\": \"10.11.1.235\", \"bot\": \"device_2\", \"vhost\": \"/\", \"mqtt_ws\": \"ws://10.11.1.235:3002/ws\"}, \"encoded\": \"eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJ1bmtub3duIiwic3ViIjoxLCJpYXQiOjE2MDk4NzY2OTYsImp0aSI6IjQ2Njk0YzJmLTJhMDMtNGUzZi04NGJkLTdlYzIyZmI1OGMxZiIsImlzcyI6Ii8vMTAuMTEuMS4yMzU6MzAwMCIsImV4cCI6MTYxMzMzMjY5NiwibXF0dCI6IjEwLjExLjEuMjM1IiwiYm90IjoiZGV2aWNlXzIiLCJ2aG9zdCI6Ii8iLCJtcXR0X3dzIjoid3M6Ly8xMC4xMS4xLjIzNTozMDAyL3dzIn0.mdiWPVn0Vp3tYbZfP9P2CRpKd3txjXkfUjvkgALeXAC7OJGSBu_0uIU3ZRakhfu6QaEKX0pP-jKlxvxgNDbYNgwUoqEC8RLrbnGoCx_SmhSf_43TRW2UoKOSo8BFp2D7_0L_zkocW_6VCzwLKo90m09N2VSA4S3wSItRphimEuvK224VSnr5oqyqQ5NfVgkA_usLVpExX6t7-5rF6Lm_VpIm6y-7Z4k6GvaJLH8WIDBsLQrM7STeFNwZGxWuUeblHjY4eyv2DkX7m1s9EN-fCUQzgBzvFUcjemk8rhAfz2A02SqShD2YHa2qidPnjpiJpwXWK9vXYdO2KQsjrsdBrA\"}, \"user\": {\"id\": 1, \"device_id\": 2, \"name\": \"Test\", \"email\": \"test@test.com\", \"created_at\": \"2020-12-14T20: 22: 49.821Z\", \"updated_at\": \"2021-01-05T19: 50: 12.653Z\", \"agreed_to_terms_at\": \"2020-12-14T20: 22: 49.854Z\", \"inactivity_warning_sent_at\": null}}"
fake_token = json.dumps({
    "token": {
        "unencoded": {
            "bot": "456",
            "exp": 1000,
            "iat": 900,
            "iss": "?",
            "jti": "Long string",
            "mqtt": "mqtt://my.farm.bot:1883",
            "mqtt_ws": "wss://my.farm.bot:1883",
            "sub": "device_456",
            "vhost": "dfsdfxcsd",
        },
        "encoded": "TOPSECRETTOKEN"
    }
})


class FakeReturn:
    def read(_) -> bytes:
        return fake_bytes


class FakeFarmbot(fb.Farmbot):
    def __init__(self) -> None:
        self.password = "drowssap"
        self.username = "emanresu"
        self.hostname = "tob.mraf.ym"
        self.state = None
        self.handle_connect = mock.MagicMock()
        self.handle_message = mock.MagicMock()
        self._handler = fb.StubHandler()
        self.read_status = mock.MagicMock()


class FakeMQTT():
    def __init__(self) -> None:
        self.connect = mock.MagicMock()
        self.loop_forever = mock.MagicMock()
        self.username_pw_set = mock.MagicMock()
        self.subscribe = mock.MagicMock()


class FakeMqttMessage():
    def __init__(self, topic: str, payload: str) -> None:
        self.topic = topic
        self.payload = payload


class TestFarmbotToken():
    @mock.patch("farmbot.urlopen", autospec=True, return_value=FakeReturn())
    def test_download_token(_, mock_download_token):
        email = "test@test.com"
        password = "password123"
        server = "http://localhost:3000"
        tkn = fb.FarmbotToken.download_token(email=email,
                                             password=password,
                                             server=server)
        assert isinstance(tkn, bytes)
        assert tkn == fake_bytes

    def test_init(_):
        token = fb.FarmbotToken(fake_bytes)
        assert(token.bot == "device_2")
        assert(token.exp == 1613332696)
        assert(token.iat == 1609876696)
        assert(token.iss == "//10.11.1.235:3000")
        assert(token.jti == "46694c2f-2a03-4e3f-84bd-7ec22fb58c1f")
        assert(token.mqtt_ws == "ws://10.11.1.235:3002/ws")
        assert(token.mqtt == "10.11.1.235")
        assert(token.sub == 1)
        assert(token.vhost == "/")
        assert(len(token.jwt) == 671)


class TestEmptyState():
    def test_empty_state(self):
        empty_xyz = {"x": None, "y": None, "z": None}
        state = fb.empty_state()
        assert(state["configuration"] == {})
        assert(state["informational_settings"] == {})
        assert(state["jobs"] == {})
        assert(state["location_data"]["axis_states"] == empty_xyz)
        assert(state["location_data"]["load"] == empty_xyz)
        assert(state["location_data"]["position"] == empty_xyz)
        assert(state["location_data"]["raw_encoders"] == empty_xyz)
        assert(state["location_data"]["scaled_encoders"] == empty_xyz)
        assert(state["mcu_params"] == {})
        assert(state["pins"] == {})
        assert(state["user_env"] == {})


class TestErrorResponse():
    def test_error_response(self):
        id = "my_id"
        errors = ["error1", "error2"]
        fake = fb.ErrorResponse(id, errors)
        assert(fake.id == id)
        assert(fake.errors == errors)


class TestOkResponse():
    def test_error_response(self):
        id = "my_id"
        fake = fb.OkResponse(id)
        assert(fake.id == id)


class TestFarmbotConnection():
    def test_init(self):
        my_farmbot = FakeFarmbot()
        connection = fb.FarmbotConnection(my_farmbot)
        assert(connection.bot == my_farmbot)
        assert(connection.mqtt)
        assert(connection.incoming_chan == "bot/emanresu/from_device")
        assert(connection.logs_chan == "bot/emanresu/logs")
        assert(connection.outgoing_chan == "bot/emanresu/from_clients")
        assert(connection.status_chan == "bot/emanresu/status")
        expected = ('bot/emanresu/status',
                    'bot/emanresu/logs',
                    'bot/emanresu/from_device')
        assert(connection.channels == expected)

    def test_start_connection(self):
        my_farmbot = FakeFarmbot()
        client = FakeMQTT()
        connection = fb.FarmbotConnection(my_farmbot, client)
        connection.start_connection()
        client.connect.assert_called_with('tob.mraf.ym', 1883, 60)
        client.loop_forever.assert_called()
        client.username_pw_set.assert_called_with('emanresu', 'drowssap')
        assert(client.on_connect)
        assert(client.on_message)

    def test_handle_connect(self):
        # https://docs.python.org/3/library/unittest.mock.html
        my_farmbot = FakeFarmbot()
        my_farmbot._handler.on_connect = mock.MagicMock()
        client = FakeMQTT()
        connection = fb.FarmbotConnection(my_farmbot, client)
        connection.handle_connect(mqtt=client,
                                  userdata=None,
                                  flags=None,
                                  rc=None)
        for channel in connection.channels:
            client.subscribe.assert_has_calls([mock.call(channel)])
        my_farmbot._handler.on_connect.assert_called_with(my_farmbot, client)
        my_farmbot.read_status.assert_called()

    def test_handle_message(self):
        my_farmbot = FakeFarmbot()
        conn = fb.FarmbotConnection(my_farmbot, FakeMQTT())

        # == STATUS Message
        conn.handle_status = mock.MagicMock()
        status_msg = FakeMqttMessage(conn.status_chan, '{}')
        conn.handle_message(conn.mqtt, None, status_msg)
        conn.handle_status.assert_called_with(status_msg)

        # == LOG Message
        conn.handle_log = mock.MagicMock()
        log_msg = FakeMqttMessage(conn.logs_chan, '{}')
        conn.handle_message(conn.mqtt, None, log_msg)
        conn.handle_log.assert_called_with(log_msg)

        # == RPC Message
        conn.unpack_response = mock.MagicMock()
        rpc_json = '{}'
        rpc_msg = FakeMqttMessage(conn.incoming_chan, rpc_json)
        conn.handle_message(conn.mqtt, None, rpc_msg)
        conn.unpack_response.assert_called_with(rpc_json)

    def test_unpack_response(self):
        conn = fb.FarmbotConnection(FakeFarmbot(), FakeMQTT())
        # == OK Response
        conn.handle_resp = mock.MagicMock()
        rpc_ok = json.dumps({"kind": "rpc_ok", "args": {"label": "123"}})
        conn.unpack_response(rpc_ok)
        conn.handle_resp.assert_called_with("123")

        # == ERROR Response
        conn.handle_error = mock.MagicMock()
        errors = [
            {'kind': 'explanation', 'args': {'message': 'ERROR 1'}},
            {'kind': 'explanation', 'args': {'message': 'ERROR 2'}},
        ]
        rpc_err = json.dumps({
            "kind": "rpc_error",
            "args": {"label": "456"},
            "body": errors
        })

        conn.unpack_response(rpc_err)
        conn.handle_error.assert_called_with("456", errors)

    def test_handle_resp(self):
        conn = fb.FarmbotConnection(FakeFarmbot(), FakeMQTT())
        my_mock = mock.MagicMock()
        conn.bot._handler.on_response = my_mock
        conn.handle_resp("any_label")
        args = my_mock.call_args[0]
        bot = args[0]
        response = args[1]
        assert bot == conn.bot
        assert response.id == "any_label"

    def test_handle_status(self):
        conn = fb.FarmbotConnection(FakeFarmbot(), FakeMQTT())
        status_msg = FakeMqttMessage(conn.status_chan, '{}')
        conn.bot._handler.on_change = mock.MagicMock()
        conn.handle_status(status_msg)
        conn.bot._handler.on_change.assert_called_with(conn.bot, {})

    def test_handle_log(self):
        conn = fb.FarmbotConnection(FakeFarmbot(), FakeMQTT())
        status_msg = FakeMqttMessage(conn.logs_chan, '{}')
        conn.bot._handler.on_log = mock.MagicMock()
        conn.handle_log(status_msg)
        conn.bot._handler.on_log.assert_called_with(conn.bot, {})

    def test_handle_error(self):
        errors = [
            {'kind': 'explanation', 'args': {'message': 'ERROR 1'}},
            {'kind': 'explanation', 'args': {'message': 'ERROR 2'}},
        ]
        label = 'fd0ee7c8-6ca8-11eb-9d9d-eba70539ce61'

        conn = fb.FarmbotConnection(FakeFarmbot(), FakeMQTT())
        status_msg = FakeMqttMessage(conn.incoming_chan, '{}')
        conn.bot._handler.on_error = mm = mock.MagicMock()
        conn.handle_error(label, errors)
        args = mm.call_args[0]
        actual_bot = args[0]
        actual_response = args[1]
        assert actual_bot == conn.bot
        assert actual_response.id == label
        assert actual_response.errors == ['ERROR 1', 'ERROR 2']

    @mock.patch("farmbot.uuid.uuid1", autospec=True, return_value="FAKE_UUID")
    def test_send_rpc(self, _):
        mqtt = FakeMQTT()
        mqtt.publish = mock.MagicMock()
        conn = fb.FarmbotConnection(FakeFarmbot(), mqtt)
        # === NON-ARRAY
        result = conn.send_rpc({})
        assert result == "FAKE_UUID"
        expected_chan = 'bot/emanresu/from_clients'
        expected_json = '{"kind": "rpc_request", "args": {"label": "FAKE_UUID"}, "body": [{}]}'
        mqtt.publish.assert_called_with(expected_chan, expected_json)
        # === ARRAY
        result2 = conn.send_rpc([{}])
        assert result2 == "FAKE_UUID"
        expected_chan2 = 'bot/emanresu/from_clients'
        expected_json2 = '{"kind": "rpc_request", "args": {"label": "FAKE_UUID"}, "body": [{}]}'
        mqtt.publish.assert_called_with(expected_chan2, expected_json2)

    fake_token = json.dumps({
        "token": {
            "unencoded": {
                "bot": "456",
                "exp": 1000,
                "iat": 900,
                "iss": "?",
                "jti": "Long string",
                "mqtt": "mqtt://my.farm.bot:1883",
                "mqtt_ws": "wss://my.farm.bot:1883",
                "sub": "device_456",
                "vhost": "dfsdfxcsd",
            },
            "encoded": "TOPSECRETTOKEN"
        }
    })

    @mock.patch("farmbot.FarmbotToken.download_token", autospec=True, return_value=fake_token)
    def test_login(self, dl_token):
        bot = fb.Farmbot.login("email", "pass")
        dl_token.assert_called_with(email='email',
                                    password='pass',
                                    server='https://my.farm.bot')
        assert bot.username == "456"
        assert bot.password == "TOPSECRETTOKEN"
        assert bot.hostname == "mqtt://my.farm.bot:1883"
        assert bot.device_id == "device_456"
        assert isinstance(bot._handler, fb.StubHandler)

        assert isinstance(bot._connection, fb.FarmbotConnection)
        assert bot.state == fb.empty_state()

    def test_position(self):
        bot = fb.Farmbot(fake_token)
        assert bot.position() == (-0.0, -0.0, -0.0)

    def test__do_cs(self):
        fake_rpc = {"kind": "nothing", "args": {}, "body": []}
        bot = fb.Farmbot(fake_token)
        bot._connection.send_rpc = mock.MagicMock()
        bot._do_cs("nothing", {})
        bot._connection.send_rpc.assert_called_with(fake_rpc)

    def test_connect(self):
        bot = fb.Farmbot(fake_token)
        fake_handler = 'In real life, this would be a class'
        bot._connection.start_connection = mock.MagicMock()
        bot.connect(fake_handler)
        assert bot._handler == fake_handler
        bot._connection.start_connection.assert_called()

    def expected_rpc(self, bot, kind, args, body=None):
        if not body:
            bot._do_cs.assert_called_with(kind, args)
        else:
            bot._do_cs.assert_called_with(kind, args, body)

    def test_various_rpcs(self):
        bot = fb.Farmbot(fake_token)
        bot._do_cs = mock.MagicMock()

        bot.send_message("Hello, world!")
        self.expected_rpc(bot,
                          'send_message',
                          {'message': 'Hello, world!', 'message_type': 'info'})

        bot.emergency_lock()
        self.expected_rpc(bot, "emergency_lock", {})

        bot.emergency_unlock()
        self.expected_rpc(bot, "emergency_unlock", {})

        bot.find_home()
        self.expected_rpc(bot, "find_home", {"speed": 100, "axis": "all"})

        bot.find_length()
        self.expected_rpc(bot, "calibrate", {"axis": "all"})

        bot.flash_farmduino("express_k10")
        self.expected_rpc(bot, "flash_firmware", {"package": "express_k10"})

        bot.go_to_home()
        self.expected_rpc(bot, "home", {"speed": 100, "axis": "all"})

        bot.move_absolute(x=1.2, y=3.4, z=5.6)
        self.expected_rpc(bot,
                          'move_absolute',
                          {
                              'location': {
                                  'kind': 'coordinate',
                                  'args': {'x': 1.2, 'y': 3.4, 'z': 5.6}
                              },
                              'speed': 100.0,
                              'offset': {
                                  'kind': 'coordinate',
                                  'args': {'x': 0, 'y': 0, 'z': 0}
                              }
                          })

        bot.move_relative(x=1.2, y=3.4, z=5.6)
        self.expected_rpc(bot,
                          "move_relative",
                          {"x": 1.2, "y": 3.4, "z": 5.6, "speed": 100})

        bot.power_off()
        self.expected_rpc(bot, "power_off", {})

        bot.read_status()
        self.expected_rpc(bot, "read_status", {})

        bot.reboot()
        self.expected_rpc(bot, "reboot", {"package": "farmbot_os"})

        bot.reboot_farmduino()
        self.expected_rpc(bot,
                          "reboot",
                          {"package": "arduino_firmware"})

        bot.factory_reset()
        self.expected_rpc(bot, "factory_reset", {"package": "farmbot_os"})

        bot.sync()
        self.expected_rpc(bot, "sync", {})

        bot.take_photo()
        self.expected_rpc(bot, "take_photo", {})

        bot.toggle_pin(12)
        self.expected_rpc(bot, "toggle_pin", {"pin_number": 12})

        bot.update_farmbot_os()
        self.expected_rpc(bot, "check_updates", {"package": "farmbot_os"})

        bot.read_pin(21)
        self.expected_rpc(bot,
                          "read_pin",
                          {'label': 'pin21', 'pin_mode': 0, 'pin_number': 21})

        bot.write_pin(45, 67)
        self.expected_rpc(bot,
                          "write_pin",
                          {'pin_mode': 0, 'pin_number': 45, 'pin_value': 67})

        bot.set_servo_angle(5, 90)
        self.expected_rpc(bot,
                          "set_servo_angle",
                          {'pin_number': 5, 'pin_value': 90})
