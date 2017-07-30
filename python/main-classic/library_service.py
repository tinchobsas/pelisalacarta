# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta 4
# Copyright 2015 tvalacarta@gmail.com
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#
# Distributed under the terms of GNU General Public License v3 (GPLv3)
# http://www.gnu.org/licenses/gpl-3.0.html
# ------------------------------------------------------------
# This file is part of pelisalacarta 4.
#
# pelisalacarta 4 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pelisalacarta 4 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pelisalacarta 4.  If not, see <http://www.gnu.org/licenses/>.
# ------------------------------------------------------------
# Service for updating new episodes on library series
# ------------------------------------------------------------

import imp
import math

from core import config
from core import jsontools
from core import logger
from core.item import Item
from platformcode import library
from platformcode import platformtools


def main():
    logger.info("pelisalacarta.library_service Actualizando series...")

    directorio = library.join_path(config.get_library_path(), "SERIES")
    logger.info("directorio="+directorio)

    if not library.path_exists(directorio):
        library.make_dir(directorio)

    library.check_tvshow_xml()

    try:

        if config.get_setting("updatelibrary") == "true":

            data, dict_data = lib_data()

            heading = 'Actualizando biblioteca....'
            p_dialog = platformtools.dialog_progress_bg('pelisalacarta', heading)
            p_dialog.update(0, '')
            i = 0
            # fix float porque la division se hace mal en python 2.x
            t = float(100) / len(dict_data.keys())

            for tvshow_id in dict_data.keys():
                logger.info("pelisalacarta.library_service serie="+dict_data[tvshow_id]["name"])

                for channel in dict_data[tvshow_id]["channels"].keys():
                    carpeta = "{0} [{1}]".format(library.title_to_filename(
                        dict_data[tvshow_id]["channels"][channel]["tvshow"].lower()), channel)
                    # carpeta = dict_serie[tvshow_id]["channels"][channel]["path"]
                    ruta = library.join_path(config.get_library_path(), "SERIES", carpeta)
                    logger.info("pelisalacarta.library_service ruta =#"+ruta+"#")

                    i += 1
                    if library.path_exists(ruta):
                        logger.info("pelisalacarta.library_service Actualizando "+carpeta)
                        logger.info("pelisalacarta.library_service url " +
                                    dict_data[tvshow_id]["channels"][channel]["url"])

                        p_dialog.update(int(math.ceil(i * t)), heading, dict_data[tvshow_id]["name"])

                        item = Item(url=dict_data[tvshow_id]["channels"][channel]["url"],
                                    show=dict_data[tvshow_id]["channels"][channel]["tvshow"], channel=channel)

                        try:
                            pathchannels = library.join_path(config.get_runtime_path(), 'channels', channel + '.py')
                            logger.info("pelisalacarta.library_service Cargando canal  " + pathchannels + " " + channel)
                            obj = imp.load_source(channel, pathchannels)
                            itemlist = obj.episodios(item)

                            try:
                                library.save_library_tvshow(item, itemlist)
                            except Exception as ex:
                                logger.info("pelisalacarta.library_service Error al guardar los capitulos de la serie")
                                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                                message = template.format(type(ex).__name__, ex.args)
                                logger.info(message)

                        except Exception as ex:
                            logger.error("Error al obtener los episodios de: {0}".
                                         format(dict_data[tvshow_id]["channels"][channel]["tvshow"]))
                            template = "An exception of type {0} occured. Arguments:\n{1!r}"
                            message = template.format(type(ex).__name__, ex.args)
                            logger.info(message)
                    else:
                        logger.info("pelisalacarta.library_service No actualiza {0} (no existe el directorio)".
                                    format(dict_data[tvshow_id]["name"]))

                        p_dialog.update(int(math.ceil(i * t)), 'Error al obtener ruta...', dict_data[tvshow_id]["name"])

            p_dialog.close()
            library.update()
        else:
            logger.info("No actualiza la biblioteca, está desactivado en la configuración de pelisalacarta")

    except Exception as ex:
        import traceback
        logger.info(traceback.format_exc())

        if p_dialog:
            p_dialog.close()


def lib_data():
    """
    Recoge la info de la libreria. Es un trozo de main que se ha extraido
    para poder usarse tambien en la funcion que utiliza el canal ayuda.py
    """
    nombre_fichero_config_canal = library.join_path(config.get_data_path(), library.TVSHOW_FILE)
    data = library.read_file(nombre_fichero_config_canal)
    dict_data = jsontools.load_json(data)
    return (data, dict_data)


def update_from_conf():
    """
    Se trata de una funcion que tiene como objetivo evitar el loop infinito
    al hacer la llamada desde ayuda.py
    """
    if platformtools.dialog_yesno("pelisalacarta",
                                  "Seguro que desea actualizar los enlaces y la biblioteca?") == 1:
        main()
        platformtools.dialog_ok("pelisalacarta", "Proceso completado")
        # TODO: Mejorarlo

    else:
        platformtools.dialog_notification("Plugin", "Proceso abortado")


if __name__ == "__main__":
    main()
