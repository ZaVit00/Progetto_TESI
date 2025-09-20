from costanti_comuni import TipoServizio
import logging
import os

def setup_logger(service: TipoServizio,
                 level: int = logging.INFO,
                 log_to_file: bool = False,
                 output_dir: str = "./logs") -> logging.Logger:
    """
    Crea e restituisce un logger dedicato a un servizio.
    :param service: uno dei valori di TipoServizio (Enum)
    :param level: livello di logging (default INFO)
    :param log_to_file: se True salva anche su file
    :param output_dir: cartella dei log
    """
    service_name = service.value  # recupera la stringa dall'enumerativi
    logger = logging.getLogger(service_name)
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            f"%(asctime)s [{service_name}] [%(levelname)s] %(message)s"
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
