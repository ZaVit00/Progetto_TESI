def formatta_dimensione(byte_size: int) -> str:
    """Ritorna una stringa leggibile in KB o MB a seconda della dimensione."""
    if byte_size < 1024 * 1024:  # meno di 1 MB
        return f"{byte_size / 1024:.2f} KB"
    else:
        return f"{byte_size / (1024 * 1024):.2f} MB"

def formatta_tempo(sec: float) -> str:
    if sec < 1:
        return f"{sec * 1000:.4f} ms"
    else:
        return f"{sec:.4f} s"
