#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de recopilación y transcripción de conversaciones para el agente Memo.
Proyecto: La Canción del Silencio (NOVELA_3)
Genera y actualiza de forma NO DESTRUCTIVA: historial/historial.md
"""

import os
import json
import re
from datetime import datetime, timezone

# Directorio raíz del proyecto (4 niveles arriba desde .agents/skills/memo/scripts)
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
HISTORIAL_DIR = os.path.join(WORKSPACE_DIR, "historial")
HISTORIAL_FILE = os.path.join(HISTORIAL_DIR, "historial.md")

BRAIN_DIRS = [
    os.path.expanduser(r"~\.gemini\antigravity\brain"),
    os.path.expanduser(r"~\.gemini\antigravity-ide\brain"),
]

EXCLUDED_CONV_IDS = {
    "3c4a63dd",
    "05acbf90",
    "a3ec8cd7",
    "a6c8d55d",
}

OTHER_PROJECT_MARKERS = [
    "ANTA_OBRA",
    "ANTA OBRA",
    "PASCUAL VEIGA",
    "LIBRO DEL EDIFICIO",
    "25_011_PROXECTO",
    "22_017_REFUNDIDO",
    "26_016_CONCURSO",
    "26_018_CASA",
    "26_033_CONCURSO",
    "TANGERINE PC",
    "ANTIGRAVITY\\CONVERT",
    "ANTIGRAVITY/CONVERT",
    "20_055_ARRANXO",
    "CARBALLO CALERO",
    "PLANTILLA.DOCX",
]


def clean_user_prompt(raw_text):
    if not raw_text:
        return ""
    match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", raw_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw_text.strip()


def extract_active_doc(raw_text):
    if not raw_text:
        return ""
    m = re.search(r"Active Document:\s*([^\r\n]+)", raw_text)
    return m.group(1) if m else ""


def is_novela3_conversation(target_log):
    """
    Determina con precisión si una conversación pertenece al proyecto NOVELA_3
    analizando rutas reales en tool_calls, Active Document y peticiones del usuario.
    Evita falsos positivos de otros proyectos (ANTA_OBRA, arquitectura, etc.).
    """
    if not os.path.exists(target_log):
        return False

    novela3_tool_hits = 0
    other_tool_hits = 0
    novela3_user_hits = 0
    other_user_hits = 0

    try:
        with open(target_log, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue

                step_type = obj.get("type")
                if step_type == "USER_INPUT":
                    raw_c = obj.get("content", "")
                    active_doc = extract_active_doc(raw_c)
                    req = clean_user_prompt(raw_c)
                    if "NOVELA_3" in active_doc:
                        novela3_tool_hits += 1
                    elif any(m in active_doc.upper() for m in OTHER_PROJECT_MARKERS):
                        other_tool_hits += 1

                    if "NOVELA_3" in req or "La Canción del Silencio" in req:
                        novela3_user_hits += 1
                    if any(m in req.upper() for m in OTHER_PROJECT_MARKERS):
                        other_user_hits += 1

                elif step_type == "PLANNER_RESPONSE" and obj.get("tool_calls"):
                    tc_str = json.dumps(obj.get("tool_calls", []), ensure_ascii=False)
                    if "NOVELA_3" in tc_str:
                        novela3_tool_hits += 1
                    if any(m in tc_str.upper() for m in OTHER_PROJECT_MARKERS):
                        other_tool_hits += 1
    except Exception:
        return False

    # Debe tener actividad real en NOVELA_3 y superar claramente a cualquier mención incidental de otros proyectos
    total_nov = novela3_tool_hits + novela3_user_hits
    if novela3_tool_hits >= 1 and novela3_tool_hits >= other_tool_hits:
        return True
    if total_nov >= 2 and total_nov > other_user_hits + other_tool_hits:
        return True
    return False


def parse_transcript_file(file_path):
    turns = []
    if not os.path.exists(file_path):
        return turns

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue

            step_type = obj.get("type")
            created_at = obj.get("created_at")

            if step_type == "USER_INPUT":
                raw_c = obj.get("content", "")
                prompt = clean_user_prompt(raw_c)
                if prompt:
                    turns.append({
                        "role": "user",
                        "time": created_at,
                        "text": prompt,
                    })
            elif step_type == "PLANNER_RESPONSE" and obj.get("status") == "DONE":
                c = obj.get("content")
                tool_calls = obj.get("tool_calls")
                if c and not tool_calls:
                    turns.append({
                        "role": "assistant",
                        "time": created_at,
                        "text": c.strip(),
                    })
    return turns


def format_iso_time(iso_str):
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return iso_str


def find_novela_conversations():
    novela_convs = {}
    for brain_dir in BRAIN_DIRS:
        if not os.path.exists(brain_dir):
            continue
        for d in os.listdir(brain_dir):
            p = os.path.join(brain_dir, d)
            if not os.path.isdir(p) or d == "tempmediaStorage":
                continue

            log_file = os.path.join(p, ".system_generated", "logs", "transcript.jsonl")
            log_full = os.path.join(p, ".system_generated", "logs", "transcript_full.jsonl")
            target_log = log_full if os.path.exists(log_full) else log_file
            check_log = log_file if os.path.exists(log_file) else log_full

            if not os.path.exists(target_log):
                continue

            if is_novela3_conversation(check_log):
                mtime = os.path.getmtime(p)
                # Si existe en ambos directorios, conservar el más reciente
                if d not in novela_convs or mtime > novela_convs[d][2]:
                    novela_convs[d] = (p, target_log, mtime)

    result = list(novela_convs.values())
    result.sort(key=lambda x: x[2])
    return result


def parse_existing_historial():
    """
    Lee las sesiones ya guardadas en historial/historial.md para preservarlas
    entre distintos equipos (OneDrive/Git), filtrando sesiones ajenas a NOVELA_3.
    """
    existing = {}
    if not os.path.exists(HISTORIAL_FILE):
        return existing

    with open(HISTORIAL_FILE, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    blocks = re.split(r"\n(?=## Sesión \d+ - )", text)
    for block in blocks[1:]:
        id_match = re.search(r"\*\*Identificador completo:\*\*\s*`([^`]+)`", block)
        time_match = re.search(r"\*\*Fecha y Hora de inicio:\*\*\s*`([^`]+)`", block)
        turns_match = re.search(r"\*\*Intercambios registrados:\*\*\s*(\d+)", block)
        if not id_match:
            continue

        conv_id = id_match.group(1).strip()
        if any(conv_id.startswith(ex) for ex in EXCLUDED_CONV_IDS):
            print(f"[LIMPIEZA] Descartando sesión excluida: {conv_id[:8]}")
            continue
        start_time = time_match.group(1).strip() if time_match else ""
        turn_count = int(turns_match.group(1)) if turns_match else 0

        # Descartar bloques contaminados de otros proyectos (ej. ANTA_OBRA / Ferrol)
        has_other = any(m in block.upper() for m in OTHER_PROJECT_MARKERS)
        has_novela = any(
            k in block
            for k in [
                "NOVELA_3",
                "La Canción del Silencio",
                "Sarah Lin",
                "Thomas Wright",
                "Em Pleh",
                "capitulo_",
                "novela/",
            ]
        )
        if has_other and not has_novela:
            print(f"[LIMPIEZA] Descartando sesión ajena al proyecto: {conv_id[:8]}")
            continue

        # Extraer el primer prompt para el índice
        first_prompt = "(Sesión preservada)"
        user_match = re.search(r"### 👤 Autor[^\n]*\n\n([^\n]+)", block)
        if user_match:
            first_prompt = user_match.group(1).strip()

        # Quitar la cabecera "## Sesión XX - ..." y el separador final "---"
        body_lines = block.strip().split("\n")[1:]
        body = "\n".join(body_lines).strip()
        if body.endswith("---"):
            body = body[:-3].strip()

        existing[conv_id] = {
            "id": conv_id,
            "start_time": start_time,
            "first_prompt": first_prompt,
            "turn_count": turn_count,
            "raw_body": body,
        }

    return existing


def format_session_body(conv_id, start_time, turns):
    lines = [
        f"**Identificador completo:** `{conv_id}`  ",
        f"**Fecha y Hora de inicio:** `{start_time}`  ",
        f"**Intercambios registrados:** {len(turns)}",
        "",
    ]

    if not turns:
        lines.append("*Sin mensajes de chat directos registrados en esta sesión.*")
        lines.append("")
        return "\n".join(lines)

    for turn in turns:
        role = turn["role"]
        t = turn.get("time", "")
        formatted_t = format_iso_time(t)
        time_badge = f" *({formatted_t})*" if formatted_t else ""

        if role == "user":
            lines.append(f"### 👤 Autor{time_badge}")
            lines.append("")
            lines.append(turn["text"])
            lines.append("")
        else:
            lines.append(f"### 🤖 Antigravity / Asistente{time_badge}")
            lines.append("")
            lines.append(turn["text"])
            lines.append("")

    return "\n".join(lines)


def generate_historial_markdown(merged_sessions):
    os.makedirs(HISTORIAL_DIR, exist_ok=True)

    lines = [
        "# 📚 Historial y Bitácora de Conversaciones",
        "## *La Canción del Silencio / Antigravity*",
        "",
        "> **Agente Responsable:** **Memo** (Cronista y Archivero Mayor)",
        f"> **Última actualización:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"> **Total de sesiones recopiladas:** {len(merged_sessions)}",
        "",
        "Este documento recopila la transcripción íntegra y ordenada de las conversaciones, instrucciones, acuerdos técnicos, debates de trama y decisiones editoriales entre el Autor y Antigravity.",
        "",
        "---",
        "",
        "## 📑 Índice Cronológico de Sesiones",
        "",
    ]

    for i, item in enumerate(merged_sessions, 1):
        conv_id = item["id"]
        first_time = item["start_time"]
        topic = item["first_prompt"][:80].replace("\n", " ")
        lines.append(f"- **[Sesión {i:02d} — {first_time}](#sesión-{i:02d}---{conv_id[:8]})**: {topic}...")

    lines.append("")
    lines.append("---")
    lines.append("")

    for i, item in enumerate(merged_sessions, 1):
        conv_id = item["id"]
        lines.append(f"## Sesión {i:02d} - {conv_id[:8]}")
        lines.append(item["raw_body"])
        lines.append("")
        lines.append("---")
        lines.append("")

    content = "\n".join(lines)
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Historial escrito con éxito en: {HISTORIAL_FILE}")
    print(f"Total sesiones consolidadas: {len(merged_sessions)}")


def main():
    print("Iniciando recopilación NO DESTRUCTIVA de conversaciones de NOVELA_3...")
    merged = parse_existing_historial()
    print(f"Sesiones válidas preservadas del historial actual: {len(merged)}")

    novela_convs = find_novela_conversations()
    print(f"Conversaciones de NOVELA_3 encontradas en este equipo: {len(novela_convs)}")

    added = 0
    updated = 0
    for d, target_log, mtime in novela_convs:
        conv_id = os.path.basename(d)
        turns = parse_transcript_file(target_log)

        start_time = ""
        first_prompt = "(Sin texto inicial)"
        for t in turns:
            if t["role"] == "user":
                first_prompt = t["text"]
                start_time = format_iso_time(t.get("time"))
                break
        if not start_time:
            start_time = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        if conv_id not in merged:
            merged[conv_id] = {
                "id": conv_id,
                "start_time": start_time,
                "first_prompt": first_prompt,
                "turn_count": len(turns),
                "raw_body": format_session_body(conv_id, start_time, turns),
            }
            added += 1
        elif len(turns) > merged[conv_id]["turn_count"]:
            merged[conv_id] = {
                "id": conv_id,
                "start_time": start_time,
                "first_prompt": first_prompt,
                "turn_count": len(turns),
                "raw_body": format_session_body(conv_id, start_time, turns),
            }
            updated += 1

    print(f"Nuevas sesiones añadidas: {added} | Sesiones actualizadas: {updated}")

    merged_list = sorted(merged.values(), key=lambda x: x.get("start_time") or "")
    generate_historial_markdown(merged_list)


if __name__ == "__main__":
    main()
