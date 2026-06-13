"""
ContextStore — Almacén de contexto en memoria para CAG.

Estructura interna:
    _store = {
        user_id: {
            key: {"value": <any>, "saved_at": <datetime>}
        }
    }

Interfaz pública:
    save(user_id, key, value)          -> bool
    list_for_user(user_id, limit=None) -> list[dict]
    clear(user_id)                     -> None
    clean_expired(max_age_minutes)     -> int
"""

import threading
from datetime import datetime, timedelta


class ContextStore:
    """
    Almacén de contexto persistente por usuario (en memoria RAM).

    Cada entrada guarda un par clave/valor con su timestamp de creación,
    lo que permite recuperar los últimos N turnos y expirar entradas viejas.
    Thread-safe mediante un Lock compartido.
    """

    def __init__(self):
        # { user_id: { key: {"value": any, "saved_at": datetime} } }
        self._store: dict = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------

    def save(self, user_id: str, key: str, value) -> bool:
        """
        Guarda (o sobreescribe) un par clave/valor para user_id.

        Comportamiento upsert: si la clave ya existe para ese usuario,
        reemplaza el valor y actualiza el timestamp.

        Returns:
            True si se guardó correctamente.
        """
        with self._lock:
            if user_id not in self._store:
                self._store[user_id] = {}
            self._store[user_id][key] = {
                "value": value,
                "saved_at": datetime.now(),
            }
        return True

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    def list_for_user(self, user_id: str, limit: int = None) -> list:
        """
        Retorna el contexto de user_id como lista de dicts {key, value}.

        Args:
            user_id: identificador del usuario.
            limit:   si se especifica, retorna solo los últimos `limit`
                     turnos ordenados por timestamp de guardado.

        Returns:
            [{"key": k, "value": v}, ...]  — vacío si no hay contexto.
        """
        with self._lock:
            user_data = self._store.get(user_id, {})
            # Ordenar por timestamp para que limit respete el orden cronológico
            ordered = sorted(user_data.items(), key=lambda kv: kv[1]["saved_at"])
            items = [{"key": k, "value": v["value"]} for k, v in ordered]

        if limit is not None:
            return items[-limit:]
        return items

    # ------------------------------------------------------------------
    # Limpieza
    # ------------------------------------------------------------------

    def clear(self, user_id: str) -> None:
        """
        Elimina todo el contexto almacenado para user_id.

        No lanza excepción si el usuario no tiene contexto.
        """
        with self._lock:
            self._store.pop(user_id, None)

    def clean_expired(self, max_age_minutes: int = 60) -> int:
        """
        Elimina entradas más viejas que max_age_minutes para todos los usuarios.

        Args:
            max_age_minutes: antigüedad máxima permitida en minutos (default 60).

        Returns:
            Número total de entradas eliminadas.
        """
        cutoff = datetime.now() - timedelta(minutes=max_age_minutes)
        removed = 0

        with self._lock:
            for user_id in list(self._store.keys()):
                user_data = self._store[user_id]
                expired = [
                    k for k, v in user_data.items()
                    if v["saved_at"] < cutoff
                ]
                for k in expired:
                    del user_data[k]
                    removed += 1
                # Eliminar usuario si se quedó sin entradas
                if not user_data:
                    del self._store[user_id]

        return removed

