"""
Sistema de registro de eventos y manejo de excepciones - SOFIA 2026.

Registra en tiempo real incidencias, errores de hardware, desconexiones
y métricas en un archivo CSV estructurado. Sirve como evidencia formal
para los entregables de laboratorio y garantiza que ningún fallo no
capturado cierre de forma imprevista la interfaz gráfica.
"""

import csv
import datetime
import os
import sys
import traceback

DEFAULT_LOG_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "docs",
        "experimental-data",
        "registro_eventos.csv"
    )
)


class EventLogger:
    """Registrador en disco CSV con protección ante fallos de I/O."""

    def __init__(self, filepath=DEFAULT_LOG_PATH):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) == 0:
                with open(self.filepath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "Timestamp",
                        "Componente",
                        "Nivel",
                        "Evento",
                        "Detalle"
                    ])
        except Exception as error:
            print(f"[EventLogger] Error al inicializar bitácora CSV: {error}")

    def log(self, componente, nivel, evento, detalle=""):
        """Escribe una fila en la bitácora CSV."""
        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        try:
            with open(self.filepath, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    ahora,
                    str(componente).upper(),
                    str(nivel).upper(),
                    str(evento),
                    str(detalle).replace("\n", " ")
                ])
        except Exception as error:
            print(f"[EventLogger] Fallo al escribir log: {error}")


# Instancia global
logger = EventLogger()


def instalar_manejador_excepciones_global(callback_alerta=None):
    """
    Instala un hook global en sys.excepthook para evitar que cualquier
    error imprevisto en hilos secundarios o slots Qt tire la aplicación.
    """
    def _manejador(exctype, value, tb):
        tb_str = "".join(traceback.format_exception(exctype, value, tb))
        mensaje_corto = f"{exctype.__name__}: {value}"
        print(f"[CRASH_PREVENTED] {mensaje_corto}\n{tb_str}", file=sys.stderr)

        logger.log(
            componente="SISTEMA",
            nivel="CRITICAL",
            evento="EXCEPCION_NO_CAPTURADA",
            detalle=f"{mensaje_corto} | Trace: {tb_str[:200]}"
        )

        if callback_alerta is not None:
            try:
                callback_alerta(f"Error recuperado: {mensaje_corto}")
            except Exception:
                pass

    sys.excepthook = _manejador

