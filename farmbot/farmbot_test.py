from unittest import mock
import farmbot as fb

fake_bytes = b"{\"token\": {\"unencoded\": {\"aud\": \"unknown\", \"sub\": 1, \"iat\": 1609876696, \"jti\": \"46694c2f-2a03-4e3f-84bd-7ec22fb58c1f\", \"iss\": \"//10.11.1.235:3000\", \"exp\": 1613332696, \"mqtt\": \"10.11.1.235\", \"bot\": \"device_2\", \"vhost\": \"/\", \"mqtt_ws\": \"ws://10.11.1.235:3002/ws\"}, \"encoded\": \"eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJ1bmtub3duIiwic3ViIjoxLCJpYXQiOjE2MDk4NzY2OTYsImp0aSI6IjQ2Njk0YzJmLTJhMDMtNGUzZi04NGJkLTdlYzIyZmI1OGMxZiIsImlzcyI6Ii8vMTAuMTEuMS4yMzU6MzAwMCIsImV4cCI6MTYxMzMzMjY5NiwibXF0dCI6IjEwLjExLjEuMjM1IiwiYm90IjoiZGV2aWNlXzIiLCJ2aG9zdCI6Ii8iLCJtcXR0X3dzIjoid3M6Ly8xMC4xMS4xLjIzNTozMDAyL3dzIn0.mdiWPVn0Vp3tYbZfP9P2CRpKd3txjXkfUjvkgALeXAC7OJGSBu_0uIU3ZRakhfu6QaEKX0pP-jKlxvxgNDbYNgwUoqEC8RLrbnGoCx_SmhSf_43TRW2UoKOSo8BFp2D7_0L_zkocW_6VCzwLKo90m09N2VSA4S3wSItRphimEuvK224VSnr5oqyqQ5NfVgkA_usLVpExX6t7-5rF6Lm_VpIm6y-7Z4k6GvaJLH8WIDBsLQrM7STeFNwZGxWuUeblHjY4eyv2DkX7m1s9EN-fCUQzgBzvFUcjemk8rhAfz2A02SqShD2YHa2qidPnjpiJpwXWK9vXYdO2KQsjrsdBrA\"}, \"user\": {\"id\": 1, \"device_id\": 2, \"name\": \"Test\", \"email\": \"test@test.com\", \"created_at\": \"2020-12-14T20: 22: 49.821Z\", \"updated_at\": \"2021-01-05T19: 50: 12.653Z\", \"agreed_to_terms_at\": \"2020-12-14T20: 22: 49.854Z\", \"inactivity_warning_sent_at\": null}}"


class FakeReturn:
    def read(_) -> bytes:
        return fake_bytes


class FakeFarmbot():
    def __init__(self) -> None:
        self.password = "drowssap"
        self.username = "emanresu"
        self.hostname = "tob.mraf.ym"
        self.handle_connect = mock.MagicMock()
        self.handle_message = mock.MagicMock()
        self.read_status = mock.MagicMock()
        self.handler = fb.StubHandler()


class FakeMQTT():
    def __init__(self) -> None:
        self.connect = mock.MagicMock()
        self.loop_forever = mock.MagicMock()
        self.username_pw_set = mock.MagicMock()
        self.subscribe = mock.MagicMock()


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
        my_farmbot.handler.on_connect = mock.MagicMock()
        client = FakeMQTT()
        connection = fb.FarmbotConnection(my_farmbot, client)
        connection.handle_connect(mqtt=client,
                                  userdata=None,
                                  flags=None,
                                  rc=None)
        for channel in connection.channels:
            client.subscribe.assert_has_calls([mock.call(channel)])
        my_farmbot.handler.on_connect.assert_called_with(my_farmbot, client)
        my_farmbot.read_status.assert_called()
