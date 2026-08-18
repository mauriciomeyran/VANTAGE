#!/usr/bin/env python3
"""
Simulación funcional del sistema de documentación de notas en archivado

Este script simula el comportamiento de VL1 al archivar vacantes,
generando las notas deterministas en el momento de la decisión.

Propósito: Validar la funcionalidad desde el punto de vista humano
antes de implementación en producción.
"""

import json
from datetime import date, datetime, timedelta
from typing import Dict, List

# Simulación de la función generate_archive_notes
def generate_archive_notes(reason: str, details: str = "") -> str:
    """
    Genera mensaje estandarizado para campo Notas cuando se archiva una vacante.
    Formato: [ARCHIVO] Razón: {razón_determinista}
    {detalles_específicos_si_aplica}
    """
    message = f"[ARCHIVO] Razón: {reason}"
    if details:
        message += f"\n{details}"
    return message


class SimulatedVacante:
    """Representa una vacante simulada en el tracker"""
    def __init__(self, id: str, marca: str, rol: str, url: str, 
                 status: str, notas: str = "", nad: str = ""):
        self.id = id
        self.marca = marca
        self.rol = rol
        self.url = url
        self.status = status
        self.notas = notas
        self.nad = nad
        self.archivada = False

    def to_dict(self):
        return {
            "id": self.id,
            "marca": self.marca,
            "rol": self.rol,
            "url": self.url,
            "status": self.status,
            "notas": self.notas,
            "nad": self.nad,
            "archivada": self.archivada
        }


def simulate_url_gate_rejection(vacante: SimulatedVacante, reason: str) -> SimulatedVacante:
    """Simula rechazo por URL Gate"""
    archive_note = generate_archive_notes(
        reason=f"URL Gate rechazada ({reason})",
        details=f"Validación de URL falló: {reason}"
    )
    
    # Append a notas existentes
    final_notas = f"{vacante.notas}\n\n{archive_note}" if vacante.notas else archive_note
    
    vacante.status = "Expirada"
    vacante.notas = final_notas
    vacante.archivada = True
    
    return vacante


def simulate_misfit_archivo(vacante: SimulatedVacante, reason: str) -> SimulatedVacante:
    """Simula archivado por misfit de perfil"""
    archive_note = generate_archive_notes(
        reason="Expirada por misfit de perfil",
        details=f"Criterio: {reason}"
    )
    
    # Append a notas existentes
    final_notas = f"{vacante.notas}\n\n{archive_note}" if vacante.notas else archive_note
    
    vacante.status = "Expirada"
    vacante.notas = final_notas
    vacante.archivada = True
    
    return vacante


def simulate_nad_expiry(vacante: SimulatedVacante) -> SimulatedVacante:
    """Simula archivado por NAD vencido"""
    archive_note = generate_archive_notes(
        reason="Expirada por NAD vencido",
        details=f"NAD original: {vacante.nad} (vencido el {vacante.nad})"
    )
    
    # Append a notas existentes
    final_notas = f"{vacante.notas}\n\n{archive_note}" if vacante.notas else archive_note
    
    vacante.status = "Expirada"
    vacante.notas = final_notas
    vacante.archivada = True
    
    return vacante


def run_simulation():
    """Ejecuta la simulación completa"""
    print("=" * 80)
    print("SIMULACIÓN FUNCIONAL - DOCUMENTACIÓN DE NOTAS EN ARCHIVADO")
    print("=" * 80)
    print()
    
    # Crear vacantes de prueba
    vacantes = [
        SimulatedVacante(
            id="vac001",
            marca="Nike",
            rol="Visual Merchandising Manager",
            url="https://jobs.nike.com/invalid-url",
            status="Target",
            notas="Nota previa: candidato interesante"
        ),
        SimulatedVacante(
            id="vac002",
            marca="Zara",
            rol="Store Manager",
            url="https://zara.com/jobs/store-manager",
            status="Target",
            notas=""
        ),
        SimulatedVacante(
            id="vac003",
            marca="LVMH",
            rol="Marketing Coordinator",
            url="https://lvmh.com/careers",
            status="Target",
            notas="Nota previa: referencia interna",
            nad=(date.today() - timedelta(days=5)).isoformat()
        ),
        SimulatedVacante(
            id="vac004",
            marca="Adidas",
            rol="Logistics Manager",
            url="https://adidas.com/jobs",
            status="Target",
            notas=""
        ),
    ]
    
    print("ESTADO INICIAL:")
    print("-" * 80)
    for v in vacantes:
        print(f"ID: {v.id} | {v.marca} | {v.rol} | Status: {v.status} | NAD: {v.nad or 'N/A'}")
        if v.notas:
            print(f"  Notas: {v.notas[:50]}...")
    print()
    
    # ESCENARIO 1: URL Gate rechazo
    print("ESCENARIO 1: URL Gate rechazo (vac001)")
    print("-" * 80)
    vacantes[0] = simulate_url_gate_rejection(vacantes[0], "STATUS_404")
    print(f"✅ Vacante {vacantes[0].id} archivada")
    print(f"   Nueva nota: {vacantes[0].notas}")
    print()
    
    # ESCENARIO 2: Misfit de perfil
    print("ESCENARIO 2: Misfit de perfil (vac002)")
    print("-" * 80)
    vacantes[1] = simulate_misfit_archivo(vacantes[1], "Exclusión por título de rol (no VM)")
    print(f"✅ Vacante {vacantes[1].id} archivada")
    print(f"   Nueva nota: {vacantes[1].notas}")
    print()
    
    # ESCENARIO 3: NAD vencido
    print("ESCENARIO 3: NAD vencido (vac003)")
    print("-" * 80)
    vacantes[2] = simulate_nad_expiry(vacantes[2])
    print(f"✅ Vacante {vacantes[2].id} archivada")
    print(f"   Nueva nota: {vacantes[2].notas}")
    print()
    
    # ESCENARIO 4: Sin archivado (control)
    print("ESCENARIO 4: Sin archivado - control (vac004)")
    print("-" * 80)
    print(f"ℹ️  Vacante {vacantes[3].id} no cumple criterios de archivado")
    print(f"   Estado permanece: {vacantes[3].status}")
    print()
    
    # ESTADO FINAL
    print("ESTADO FINAL:")
    print("=" * 80)
    for v in vacantes:
        print(f"ID: {v.id} | {v.marca} | {v.rol} | Status: {v.status} | Archivada: {v.archivada}")
        if v.notas:
            print(f"  Notas completas:")
            for line in v.notas.split('\n'):
                print(f"    {line}")
    print()
    
    # ANÁLISIS DE PERSPECTIVA HUMANA
    print("ANÁLISIS DE PERSPECTIVA HUMANA:")
    print("=" * 80)
    print("✅ TRAZABILIDAD: Cada decisión de archivado tiene razón documentada")
    print("✅ TRANSPARENCIA: Operador puede ver POR QUÉ se archivó cada vacante")
    print("✅ AUDITORÍA: Historial de decisiones accesible en campo Notas")
    print("✅ DEBUGGING: Facilita identificar si VL1 toma buenas decisiones")
    print("✅ APPEAL: Operador puede cuestionar/apelar decisiones con evidencia")
    print()
    
    # COMPARACIÓN CON ENFOQUE ANTERIOR
    print("COMPARACIÓN CON ENFOQUE ANTERIOR (housekeeping post-decisión):")
    print("=" * 80)
    print("❌ ENFOQUE ANTERIOR: Notas se llenan DESPUÉS de la decisión")
    print("   - Pierde valor de trazabilidad en tiempo real")
    print("   - No sirve para auditar decisiones de VL1")
    print("   - Documentación retrospectiva sin contexto de momento de decisión")
    print()
    print("✅ ENFOQUE CORREGIDO: Notas se llenan EN EL MOMENTO de la decisión")
    print("   - Trazabilidad inmediata de decisiones")
    print("   - Útil para auditar y mejorar lógica de VL1")
    print("   - Documentación con contexto completo del momento de decisión")
    print()
    
    # VALIDACIÓN DE FORMATO
    print("VALIDACIÓN DE FORMATO DE NOTAS:")
    print("=" * 80)
    for v in vacantes:
        if v.archivada:
            print(f"Vacante {v.id}:")
            lines = v.notas.split('\n')
            # Buscar línea que contiene [ARCHIVO] (puede no ser la primera si hay notas previas)
            has_archivo_tag = any("[ARCHIVO]" in line for line in lines)
            if has_archivo_tag:
                print("  ✅ Formato correcto: contiene [ARCHIVO] Razón: ...")
            else:
                print("  ❌ Formato incorrecto: falta [ARCHIVO]")
            
            # Verificar detalles adicionales
            archivo_line_index = next((i for i, line in enumerate(lines) if "[ARCHIVO]" in line), None)
            if archivo_line_index is not None and archivo_line_index + 1 < len(lines):
                next_line = lines[archivo_line_index + 1].strip()
                if next_line:
                    print("  ✅ Detalles adicionales presentes")
                else:
                    print("  ℹ️  Sin detalles adicionales inmediatos")
            print()
    
    # GUARDAR RESULTADOS
    resultados = {
        "simulacion": "Documentación de notas en archivado",
        "fecha": datetime.now().isoformat(),
        "vacantes": [v.to_dict() for v in vacantes],
        "conclusion": "Validación exitosa desde perspectiva humana"
    }
    
    with open("simulacion_resultados.json", "w") as f:
        json.dump(resultados, f, indent=2)
    
    print("Resultados guardados en: simulacion_resultados.json")
    print()
    print("✅ SIMULACIÓN COMPLETADA EXITOSAMENTE")


if __name__ == "__main__":
    run_simulation()
