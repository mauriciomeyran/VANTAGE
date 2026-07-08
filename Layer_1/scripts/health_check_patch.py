"""
PATCH — agregar check_layer3_heartbeat() a health_check.py

Instrucciones:
1. Abrir Layer_1/scripts/health_check.py
2. Agregar la función check_layer3_heartbeat() antes del bloque "── Runner ──"
3. Agregar ("layer3", check_layer3_heartbeat) a la lista checks en main()

--- FUNCIÓN A INSERTAR (antes de "def main():") ---

L3_HEARTBEAT_PATH     = Path.home() / ".vantage" / "l3_heartbeat.json"
L3_STALE_THRESHOLD_H  = 48   # alertar si L3 no corrió en más de 48h


def check_layer3_heartbeat():
    \"\"\"Verifica que Layer 3 (mail pipeline) haya corrido recientemente.\"\"\"
    if not L3_HEARTBEAT_PATH.exists():
        warn("layer3 — heartbeat no encontrado (¿L3 nunca ha corrido?)")
        return True   # no es fallo crítico si nunca se ha configurado

    try:
        data = json.loads(L3_HEARTBEAT_PATH.read_text())
        last_run_str = data.get("last_run", "")
        if not last_run_str:
            warn("layer3 — heartbeat sin campo last_run")
            return True

        last_run = datetime.fromisoformat(last_run_str.replace("Z", "+00:00"))
        now      = datetime.now(tz=timezone.utc)
        age_h    = (now - last_run).total_seconds() / 3600

        created = data.get("total_created", "?")
        failed  = data.get("total_failed", "?")

        if age_h > L3_STALE_THRESHOLD_H:
            warn(
                f"layer3 — última ejecución hace {age_h:.0f}h "
                f"(umbral: {L3_STALE_THRESHOLD_H}h) | created={created} failed={failed}"
            )
        else:
            ok(
                f"layer3 — última ejecución hace {age_h:.1f}h "
                f"| created={created} failed={failed}"
            )
    except Exception as e:
        warn(f"layer3 — error leyendo heartbeat: {e}")

    return True   # L3 es pasivo; no bloquea arranque de L1

--- LÍNEA A AGREGAR EN main() (lista checks, después de "index_age") ---

        ("layer3", check_layer3_heartbeat),
"""

# Este archivo es solo documentación del patch.
# No ejecutar directamente.
print(__doc__)
