from costanti_comuni import TipoServizio
import logging
import os

import logging
import os
from costanti_comuni import TipoServizio


def setup_logger(
        service: TipoServizio,
        module: str = __name__,
        level: int = logging.INFO,
        log_to_file: bool = False,
        output_dir: str = "./logs"
) -> logging.Logger:
    """
    Crea e restituisce un logger dedicato a un servizio e a un modulo.

    :param service: uno dei valori di TipoServizio (Enum)
    :param module: nome del modulo Python (tipicamente __name__)
    :param level: livello di logging (default INFO)
    :param log_to_file: se True salva anche su file
    :param output_dir: cartella dei log
    """
    service_name = service.value
    logger_name = f"{service_name}.{module}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
        )

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler opzionale
        if log_to_file:
            os.makedirs(output_dir, exist_ok=True)
            log_path = os.path.join(output_dir, f"{service_name.lower()}.log")
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger
