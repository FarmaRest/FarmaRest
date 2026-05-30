import logging
import threading
import time
from datetime import datetime, timezone

logger = logging.getLogger("farma.cron")


def _inactivar_usuarios():
    from app.core.database import SessionLocal
    from app.services.usuarios import InactivacionService

    db = SessionLocal()
    try:
        service = InactivacionService(db)
        logger.info("[CRON] Inactivación de usuarios iniciada.")
        total = service.ejecutar()
        logger.info(f"[CRON] Usuarios inactivados: {total}")
        logger.info("[CRON] Inactivación de usuarios finalizada correctamente.")
    except Exception as e:
        logger.error(f"[CRON] Error durante la inactivación: {e}")
    finally:
        db.close()


def _loop_diario():
    while True:
        ahora = datetime.now(timezone.utc)
        # Ejecutar a las 3:00 AM UTC cada día
        segundos_hasta_3am = (3 - ahora.hour) * 3600 - ahora.minute * 60 - ahora.second
        if segundos_hasta_3am <= 0:
            segundos_hasta_3am += 86400
        time.sleep(segundos_hasta_3am)
        _inactivar_usuarios()


def iniciar_cron():
    hilo = threading.Thread(target=_loop_diario, daemon=True, name="cron-inactivacion")
    hilo.start()
    logger.info("[CRON] Tarea de inactivación programada iniciada (diaria a las 3:00 AM UTC).")
