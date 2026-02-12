import signal
import sys
import logging
from src.tui.app import YTMusicApp

from src.config import get_data_dir

# Configurar logging para depuración
logging.basicConfig(
    filename=get_data_dir() / 'debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def signal_handler(sig, frame):
    """Manejador para cerrar la app inmediatamente con Ctrl+C."""
    # Intentamos una salida limpia si la app está definida
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    app = YTMusicApp()
    try:
        app.run()
    except SystemExit:
        # Aseguramos que los procesos secundarios mueran
        pass
