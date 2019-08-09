import traceback
import os
from multiprocessing import current_process


def statpro_update(feature, log=None):
    """

    :type feature: str
    :type log: logging.Logger
    """
    if not "INICIO_VERSION_HOME" in os.environ:
        return

    if current_process().name != "MainProcess":
        return

    try:
        import inicioenv
        import inicio

        msg = "Sending statpro information about feature: " + feature
        if log is not None:
            log.debug(msg)

        cfg = inicio.config_dict()
        inicioenv.statpro_update([feature], cfg)

    except ImportError:
        msg = "Could not import inicioenv and inicio!"
        if log is not None:
            log.warning(msg)
        else:
            print(msg)
        return

    except Exception:
        msg = "Exception occured while statpro update: " + traceback.format_exc()
        if log is not None:
            log.warning(msg)
        else:
            print(msg)
        return


class FEATURES:
    anasymod_import         = "anasymod_import"
    anasymod_sim            = "anasymod_sim_"
    anasymod_build_vivado   = "anasymod_build_vivado"
    anasymod_emulate_vivado = "anasymod_emulate_vivado"


if __name__ == '__main__':
    statpro_update(FEATURES.anasymod_import)
