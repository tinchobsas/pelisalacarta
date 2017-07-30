# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta
# HTTPServer
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------
import os
from core import logger
from core import config
from threading import Thread
import WebSocketServer
from platformcode import platformtools
import random
import traceback


class HandleWebSocket(WebSocketServer.WebSocket):
    ID = "%032x" % (random.getrandbits(128))
    controller = None

    def handleMessage(self):
        try:
            if self.data:
                import json
                json_message = json.loads(str(self.data))

            if "request" in json_message:
                t = Thread(target=self.controller.run, args=[json_message["request"].encode("utf8")], name=self.ID)
                t.setDaemon(True)
                t.start()

            elif "data" in json_message:
                if type(json_message["data"]["result"]) == unicode:
                    json_message["data"]["result"] = json_message["data"]["result"].encode("utf8")

                self.controller.set_data(json_message["data"])

        except:
            logger.error(traceback.format_exc())
            show_error_message(traceback.format_exc())

    def handleConnected(self):
        try:
            from platformcode.controllers.html import html
            self.controller = html(self)
            platformtools.controllers[self.ID] = self.controller
            self.server.fnc_info()
        except:
            logger.error(traceback.format_exc())

    def handleClose(self):
        self.controller = None
        del platformtools.controllers[self.ID]
        self.server.fnc_info()


port = int(config.get_setting("websocket.port"))
server = WebSocketServer.SimpleWebSocketServer("", port, HandleWebSocket)


def start(fnc_info):
    server.fnc_info = fnc_info
    Thread(target=server.serveforever).start()


def stop():
    server.close()


def show_error_message(err_info):
    from core import scrapertools
    patron = 'File "' + os.path.join(config.get_runtime_path(), "channels", "").replace("\\", "\\\\") + '([^.]+)\.py"'
    canal = scrapertools.find_single_match(err_info, patron)
    if canal:
        platformtools.dialog_ok(
                "Se ha producido un error en el canal " + canal,
                "Esto puede ser devido a varias razones: \n \
                - \El servidor no está disponible, o no esta respondiendo.\n \
                - Cambios en el diseño de la web.\n \
                - Etc...\n \
                Comprueba el log para ver mas detalles del error.")
    else:
        platformtools.dialog_ok(
                "Se ha producido un error en pelisalacarta",
                "Comprueba el log para ver mas detalles del error.")
