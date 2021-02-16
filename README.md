# !NOT READY FOR GENERAL USE!

Eventually, this will become the official RPC wrapper for Farmbot. It is still under active development.
Many things mentioned below have not yet been implemented. Many will change without notice. Real-world testing is minimal.

# Installation

This module has not yet been published. In order to test the code, you must clone the repository and use the code directly:

```
git clone git@github.com:FarmBot-Labs/farmbot-py.git
cd farmbot-py
```

After cloning the repo, you must [manually install Paho MQTT](https://pypi.org/project/paho-mqtt/).

# Unit Testing

```
pytest --cov=farmbot --cov-report html
```

# Usage

```python
from farmbot import Farmbot, FarmbotToken

# Before we begin, we must download an access token from the
# API. To avoid copy/pasting passwords, it is best to create
# an access token and then store that token securely:
raw_token = FarmbotToken.download_token("test@example.com",
                                        "password",
                                        "https://my.farm.bot")

# This token is then passed to the Farmbot constructor:
fb = Farmbot(raw_token)

# If you are just doing testing, such as local development,
# it is possible to skip token creation and login with email
# and password. This is not recommended for production devices:
# fb = Farmbot.login(email="em@i.l",
#                    password="pass",
#                    server="https://my.farm.bot")

# The next step is to call fb.connect(), but we are not ready
# to do that yet. Before we can call connect(), we must
# create a "handler" object. FarmBot control is event-based
# and the handler object is responsible for integrating all
# of those events into a custom application.
#
# At a minimum, the handler must respond to the following
# methods:
#     on_connect(self, bot: Farmbot, client: Mqtt) -> None
#     on_change(self, bot: Farmbot, state: Dict[Any, Any]) -> None
#     on_log(self, _bot: Farmbot, log: Dict[Any, Any]) -> None
#     on_error(self, _bot: Farmbot, _response: ErrorResponse) -> None
#     on_response(self, _bot: Farmbot, _response: OkResponse) -> None
#
# FarmBotPy will call the appropriate method whenever an event
# is triggered. For example, the method `on_log` will be
# called with the last log message every time a new log
# message is created.


class MyHandler:
    # The `on_connect` event is called whenever the device
    # connects to the MQTT server. You can place initialization
    # logic here.
    #
    # The callback is passed a FarmBot instance, plus an MQTT
    # client object (see Paho MQTT docs to learn more).
    def on_connect(self, bot, mqtt_client):
        # Once the bot is connected, we can send RPC commands.
        # Every RPC command returns a unique, random request
        # ID. Later on, we can use this ID to track our commands
        # as they succeed/fail (via `on_response` / `on_error`
        # callbacks):

        request_id1 = bot.move_absolute(x=10, y=20, z=30)
        # => "c580-6c-11-94-130002"
        print("MOVE_ABS REQUEST ID: " + request_id1)

        request_id2 = bot.send_message("Hello, world!")
        # => "2000-31-49-11-c6085c"
        print("SEND_MESSAGE REQUEST ID: " + request_id2)

    def on_change(self, bot, state):
        # The `on_change` event is most frequently triggered
        # event. It is called any time the device's internal
        # state changes. Example: Updating X/Y/Z position as
        # the device moves across the garden.
        # The bot maintains all this state in a single JSON
        # object that is broadcast over MQTT constantly.
        # It is a very large object, so we are printing it
        # only as an example.
        print("NEW BOT STATE TREE AVAILABLE:")
        print(state)
        # Since the state tree is very large, we offer
        # convenience helpers such as `bot.position()`,
        # which returns an (x, y, z) tuple of the device's
        # last known position:
        print("Current position: (%.2f, %.2f, %.2f)" % bot.position())
        # A less convenient method would be to access the state
        # tree directly:
        pos = state["location_data"]["position"]
        xyz = (pos["x"], pos["y"], pos["z"])
        print("Same information as before: " + xyz)

    # The `on_log` event fires every time a new log is created.
    # The callback receives a FarmBot instance, plus a JSON
    # log object. The most useful piece of information is the
    # `message` attribute, though other attributes do exist.
    def on_log(self, bot, log):
        print("New message from FarmBot: " + log['message'])

    # When a response succeeds, the `on_response` callback
    # fires. This callback is passed a FarmBot object, as well
    # as a `response` object. The most important part of the
    # `response` is `response.id`. This `id` will match the
    # original request ID, which is useful for cross-checking
    # pending operations.
    def on_response(self, bot, response):
        print("ID of successful request: " + response.id)

    # If an RPC request fails (example: stalled motors, firmware
    # timeout, etc..), the `on_error` callback is called.
    # The callback receives a FarmBot object, plus an
    # ErrorResponse object.
    def on_error(self, bot, response):
        # Remember the unique ID that was returned when we
        # called `move_absolute()` earlier? We can cross-check
        # the ID by calling `response.id`:
        print("ID of failed request: " + response.id)
        # We can also retrieve a list of error message(s) by
        # calling response.errors:
        print("Reason(s) for failure: " + response.errors)


# Now that we have a handler class to use, let's create an
# instance of that handler and `connect()` it to the FarmBot:
handler = MyHandler()

# Keep in mind that `connect()` will block the current thread.
# If you require parallel operations, consider using a background
# thread or a worker process.
fb.connect(handler)
print("This line will not execute. `connect()` is a blocking call.")
```

# Supported Remote Procedure Calls

The currently supported list of commands is below.

Please create an issue if you would to request a new command.

 * bot.position() -> (x, y, z)
 * bot.emergency_lock()
 * bot.emergency_unlock()
 * bot.factory_reset()
 * bot.find_home()
 * bot.find_length(axis="all")
 * bot.flash_farmduino(package="farmduino") (or "arduino", "express_k10", "farmduino_k14")
 * bot.go_to_home(axis="all", speed=100)
 * bot.move_absolute(x, y, z, speed=100.0)
 * bot.move_relative(x, y, z, speed=100)
 * bot.power_off()
 * bot.read_pin(pin_number, pin_mode="digital") (NOTE: Results appear in state tree)
 * bot.read_status()
 * bot.reboot()
 * bot.reboot_farmduino()
 * bot.send_message(msg, type="info")
 * bot.set_servo_angle(pin_number, angle)
 * bot.sync()
 * bot.take_photo()
 * bot.toggle_pin(pin_number)
 * bot.update_farmbot_os()
 * bot.write_pin(pin_number, pin_value, pin_mode="digital" )

# Done

 - [X] Initialize via API token
 - [X] bot.connect
 - [X] bot._connection
 - [X] bot.move_absolute
 - [X] bot.send_message
 - [X] emit on_change
 - [X] emit on_log
 - [X] emit on_connect
 - [X] emit on_error
 - [X] emit on_response
 - [X] bot.location
 - [X] bot.send_raw
 - [X] bot.read_status
 - [X] Perform `getStatus()` before firing `connect()` event.
 - [X] bot.emergency_lock
 - [X] bot.emergency_unlock
 - [X] bot.take_photo
 - [X] bot.find_home
 - [X] bot.find_length
 - [X] bot.flash_farmduino
 - [X] bot.power_off
 - [X] bot.sync
 - [X] bot.toggle_pin
 - [X] bot.update_farmbot_os
 - [X] bot.reboot_farmduino
 - [X] bot.move_relative
 - [X] bot.go_to_home

# TODO

 - [ ] 100% test coverage
 - [ ] 100% documentation
 - [ ] Publish to PyPi
 - [ ] Get a CI System
 - [ ] Update MQTT client string
 - [ ] bot.write_pin
 - [ ] bot.reboot
 - [ ] bot.reset_farmbot_os
 - [ ] bot.reset_farmduino
 - [ ] bot.set_servo_angle
 - [ ] bot.run_sequence (References sequences)
