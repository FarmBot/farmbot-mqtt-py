:warning: | Vous lisez la traduction française de la documentation, elle peut ne pas être totalement à jour. En cas de doute, consultez la [version anglaise](README.md).
:---: | :---

Ce _package_ est prêt à être utilisé, mais n'a pas été testé de manière approfondie dans le monde réel.

Les signalements de bugs sont bienvenus.

# Dépendances (_Requirements_)

Ce _package_ a été testé avec Python 3.8 et `paho-mqtt` 1.5.

Il se peut qu'il fonctionne avec des versions antérieures de Python, mais le support n'est assuré qu'avec Python 3.8.
Merci de ne pas signaler de bugs liés à des versions antérieures.

# Installation

Farmbot publie la version la plus récente de ce _package_ sur [PyPi](https://pypi.org/project/farmbot/). Vous pouvez l'installer avec la commande suivante :

```
pip install farmbot
```

# Tests unitaires

```
pip install -e .[dev]
pytest --cov=farmbot --cov-report html
```

# Utilisation

```python
from farmbot import Farmbot, FarmbotToken


# Avant tout, nous devons obtenir un jeton d'accès (access token) auprès de l'API.
# Pour éviter de copier/coller des mots de passe, il est préférable de créer
# un jeton d'accès et de le stocker de manière sécurisée.
raw_token = FarmbotToken.download_token("test@example.com",
                                        "password",
                                        "https://my.farm.bot")

# Ce jeton est ensuite passé au constructeur Farmbot :
fb = Farmbot(raw_token)

# Si vous réalisez des tests, du développement local,
# il est possible de sauter l'étape de création de jeton et de s'authentifier avec un email
# et un mot de passe. Ce n'est cependant pas recommandé pour les robots en production :
# fb = Farmbot.login(email="em@i.l",
#                    password="pass",
#                    server="https://my.farm.bot")

# L'étape suivante est d'appeler fb.connect(), mais nous ne sommes pas encore prêts
# à le faire. Avant de pouvoir appeler fb.connect(), nous devons créer
# un objet "handler" (gestionnaire d'évènements).
# Le contrôle du FarmBot est basé sur des évènements et l'objet handler sert à intégrer
# tous ces évènements dans une application sur mesure.
#
# Au minimum, le handler doit implémenter les méthodes suivantes :
#     on_connect(self, bot: Farmbot, client: Mqtt) -> None
#     on_change(self, bot: Farmbot, state: Dict[Any, Any]) -> None
#     on_log(self, _bot: Farmbot, log: Dict[Any, Any]) -> None
#     on_error(self, _bot: Farmbot, _response: ErrorResponse) -> None
#     on_response(self, _bot: Farmbot, _response: OkResponse) -> None
#
# FarmbotPy appellera la méthode appropriée à chaque fois qu'un évènement est déclenché.
# Par exemple, la méthode `on_log` sera appelée avec le dernier message
# à chaque fois qu'un nouveau log est créé.

class MyHandler:
    # L'évènement `on_connect` est appelé à chaque fois que le robot
    # se connecte au serveur MQTT. C'est à cet endroit que vous pouvez placer
    # la logique d'initialisation.
    #
    # Le callback (fonction de rappel) reçoit deux arguments : l'instance Farmbot,
    # et un objet client MQTT (voir la documentation de Paho MQTT pour en savoir plus)
    def on_connect(self, bot, mqtt_client):
        # Une fois connecté au robot, nous pouvons envoyer des commandes RPC.
        # Chaque commande RPC retourne un identifiant de requête unique et aléatoire.
        # Nous pouvons ensuite utiliser cet identifiant pour être informé
        # du succès ou de l'échec de nos requêtes (via les callbacks `on_response` / `on_error`):

        request_id1 = bot.move_absolute(x=10, y=20, z=30)
        # => "c580-6c-11-94-130002"
        print("Identifiant de requête MOVE_ABS: " + request_id1)

        request_id2 = bot.send_message("Hello, world!")
        # => "2000-31-49-11-c6085c"
        print("Idnetifiant de requête SEND_MESSAGE: " + request_id2)

    def on_change(self, bot, state):
        # `on_change` est l'évènement le plus fréquemment déclenché.
        # Il est appelé à chaque fois que l'état interne du robot change.
        # Exemple : lors de la mise à jour de la position X/Y/Z
        # lorsque le robot se déplace dans le jardin.
        # L'état interne est contenu dans un seul object JSON
        # qui est diffusé (broadcast) en permanence via le protocole MQTT.
        # C'est un très gros objet, qui n'est affiché ici qu'à titre d'exemple.
        print("Un nouvel état du robot est disponible :")
        print(state)
        # Comme l'arbre d'état est très volumineux, nous proposons des fonctions helpers
        # pour faciliter l'accès à certaines données, tel que `bot.position()` qui retourne
        # un tuple (x, y, z) de la dernière position connue du robot :
        print("Position actuelle : (%.2f, %.2f, %.2f)" % bot.position())
        pos = state["location_data"]["position"]
        xyz = (pos["x"], pos["y"], pos["z"])
        print("Même information : " + str(xyz))

    # L'évènement `on_log` est déclenché à chaque fois qu'un nouveau log est créé.
    # Le callback reçoit deux arguments : une instance Farmbot, et un objet log au format JSON.
    # L'information la plus utile est l'attribut `message`, bien que d'autres attributs soient également disponibles.
    def on_log(self, bot, log):
        print("New message from FarmBot: " + log['message'])

    # Quand une requête est couronnée de succès, le callback `on_response` se déclenche.
    # Ce callback reçoit deux arguments : un objet Farmbot, et un objet `response`.
    # La partie la plus importante de `response` est `response.id`. Cet `id` correspond
    # à l'identifiant de requête d'origine, ce qui est utile pour recouper les opérations en attente.
    def on_response(self, bot, response):
        print("Identifiant de la requête réussie : " + response.id)

    # Si une requête RPC échoue (exemple : moteurs bloqués, timeout du firmware, etc.),
    # le callback `on_error` est appelé.
    # Le callback reçoit deux arguments : un objet Farmbot, et un objet ErrorResponse.
    def on_error(self, bot, response):
        # Vous rappelez-vous de l'identifiant unique qui était retourné
        # quand nous appelions `move_absolute` un peu plus haut ?
        # Nous pouvons le retrouver en affichant `response.id`:
        print("Identifiant de la requête en échec :" + response.id)
        # Nous pouvons également récupérer une liste de messages d'erreur
        # en affichant `response.errors`
        print("Cause(s) de l'échec : " + response.errors)


# Maintenant que nous avons une classe gestionnaire d'évènements à disposition,
# créons une instance de ce handler et connectons-la au Farmbot :
handler = MyHandler()

# Une fois que `connect` est appelé, l'exécution de tout autre code est suspendue
# jusqu'à qu'un évènement se produise (logs, erreurs, mise à jour du statut, etc.).
# Si vous avez besoin d'exécuter autre chose pendant que `connect()` est actif,
# envisagez l'utilisation de threads (https://docs.python.org/fr/3/library/threading.html)
# ou de processus (https://docs.python.org/fr/3/library/multiprocessing.html).
fb.connect(handler)
print("Cette ligne ne s'exécutera pas. `connect()` est une commande bloquante.")
```

# Remote Procedure Calls (RPC) supportés

Vous trouverez ci-dessous la liste des commandes actuellement supportées.

Merci de créer une _issue_ si vous souhaitez demander une nouvelle commande.

 * bot.position() -> (x, y, z)
 * bot.emergency_lock()
 * bot.emergency_unlock()
 * bot.factory_reset()
 * bot.find_home()
 * bot.find_length(axis="all")
 * bot.flash_farmduino(package="farmduino") (ou "arduino", "express_k10", "farmduino_k14")
 * bot.go_to_home(axis="all", speed=100)
 * bot.move_absolute(x, y, z, speed=100.0)
 * bot.move_relative(x, y, z, speed=100)
 * bot.power_off()
 * bot.read_pin(pin_number, pin_mode="digital") (N.B. : les résultats apparaissent dans l'arbre d'état)
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

# Non supporté pour le moment

 * Capacité à exécuter une _séquence_ Farmbot existante
 * Gestion des ressources via une API REST

# _Build_ et publication du _package_

Nous suivons un workflow standard Pip / PyPI. Voyez [cet excellent tutoriel](https://www.youtube.com/watch?v=GIF3LaRqgXo&t=1527s) pour plus de détails.
