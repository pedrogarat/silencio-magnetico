# -*- coding: utf-8 -*-
"""
Script autónomo para Windows: Generación automática de banners 21:9 para SOMBRA.
Busca el primer capítulo pendiente (entre 1 y 25), lanza agy.exe de forma silenciosa,
recorta a 21:9, actualiza datos web y bitácora, y sube a GitHub.
"""
import os
import sys
import re
import subprocess
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
BANNERS_DIR = WORKSPACE / "img" / "banners"
PROMPTS_FILE = WORKSPACE / "novela" / "prompts_banners_21_9.md"
AGY_EXE = Path(r"C:\Users\Usuario\.gemini\bin\agy.exe")

def encontrar_siguiente_capitulo():
    BANNERS_DIR.mkdir(parents=True, exist_ok=True)
    for cap in range(1, 26):
        banner_jpg = BANNERS_DIR / f"cap_{cap}.jpg"
        banner_png = BANNERS_DIR / f"cap_{cap}.png"
        if not banner_jpg.exists() and not banner_png.exists():
            return cap
    return None

def extraer_prompt(cap_num):
    if not PROMPTS_FILE.exists():
        print(f"[ERROR] No se encuentra {PROMPTS_FILE}")
        return None
    content = PROMPTS_FILE.read_text(encoding="utf-8")
    
    # Buscar sección del capítulo: ### Capítulo N: o ## Capítulo N:
    patron = rf"###?\s*Cap[íi]tulo\s+{cap_num}\b.*?(?=###?\s*Cap[íi]tulo|\Z)"
    match = re.search(patron, content, re.DOTALL | re.IGNORECASE)
    if not match:
        print(f"[ERROR] No se encontró el prompt para el capítulo {cap_num} en {PROMPTS_FILE}")
        return None
    
    seccion = match.group(0)
    # Extraer bloque de código con el prompt
    code_match = re.search(r"```(?:\w+)?\s*\n(.*?)\n```", seccion, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    return seccion.strip()

def desinstalar_tarea_programada():
    """Elimina la tarea del Programador de Tareas de Windows cuando ya no quedan capitulos."""
    try:
        subprocess.run(
            ["schtasks", "/delete", "/tn", "SOMBRA_Generador_Banners_21_9", "/f"],
            capture_output=True,
            text=True
        )
        print("[OK] Tarea programada 'SOMBRA_Generador_Banners_21_9' desinstalada de Windows automáticamente.")
    except Exception as e:
        print(f"[Aviso] No se pudo desinstalar la tarea programada: {e}")

def mostrar_notificacion_windows(titulo, mensaje, ruta_imagen=None):
    """Muestra una notificación nativa Toast en Windows con imagen y clic para abrirla en grande."""
    xml_img = ""
    launch_attr = ""
    if ruta_imagen and Path(ruta_imagen).exists():
        uri_img = Path(ruta_imagen).resolve().as_uri()
        xml_img = f'<image placement="hero" src="{uri_img}"/>'
        launch_attr = f'launch="{uri_img}" activationType="protocol"'
    
    ps_cmd = f"""
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] > $null
    $template = @"
    <toast {launch_attr}>
        <visual>
            <binding template="ToastGeneric">
                <text>{titulo}</text>
                <text>{mensaje}</text>
                {xml_img}
            </binding>
        </visual>
    </toast>
"@
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($template)
    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("SOMBRA Novela").Show($toast)
    """
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
    except Exception as e:
        print(f"[Aviso] No se pudo enviar notificación nativa: {e}")

def main():
    print("=" * 60)
    print("  SOMBRA: Generador Autónomo de Banners 21:9 (Windows)")
    print("=" * 60)
    
    cap = encontrar_siguiente_capitulo()
    if cap is None:
        print("[OK] ¡Todos los capítulos (1 al 25) ya tienen su banner 21:9 generado!")
        desinstalar_tarea_programada()
        mostrar_notificacion_windows(
            "SOMBRA Novela - Colección Completa",
            "¡Todos los banners 21:9 (Capítulos 1 al 25) han sido generados y publicados! La tarea automática se ha autoeliminado."
        )
        sys.exit(0)
        
    print(f"[*] Siguiente capítulo a procesar: Capítulo {cap}")
    prompt_texto = extraer_prompt(cap)
    if not prompt_texto:
        sys.exit(1)
        
    print(f"[*] Prompt cargado ({len(prompt_texto)} caracteres).")
    
    # Instrucción para que el subproceso de agy invoque el generador de imágenes y guarde la ruta
    instruccion_agente = (
        f"Por favor ejecuta esta tarea automática de banner para el Capítulo {cap} de la novela SOMBRA:\n"
        f"IMPORTANTE PARA LA COHERENCIA VISUAL:\n"
        f"Antes de generar la imagen, consulta las fotos de referencia canónicas en img/personajes/ (thomas.jpg, sarah.jpg, jean_luc.jpg, ramos.jpg, pleh.jpg) "
        f"para asegurar que los rasgos fisonómicos, etnia, edad, peinado y complexión de cada personaje coincidan fielmente con el retrato canónico de su archivo.\n"
        f"1. Invoca al subagente 'image-generator' con Role 'Banner Image Generator Cap {cap}' usando exactamente este prompt:\n"
        f"'''\n{prompt_texto}\n'''\n"
        f"2. Con la ruta absoluta de la imagen JPG generada por el subagente, ejecuta el recorte exacto a 21:9 corriendo el comando:\n"
        f"python recortar_banner_21_9.py \"<ruta_imagen_generada>\" {cap}\n"
        f"3. Verifica que exista el archivo img/banners/cap_{cap}.jpg.\n"
        f"4. Ejecuta: node build-novel-data.js\n"
        f"5. Ejecuta: python .agents/skills/memo/scripts/recopilar_historial.py\n"
        f"6. Sincroniza con GitHub ejecutando: python sync_multiversion_to_github.py\n"
        f"7. Responde únicamente: [BANNER_CAP_{cap}_COMPLETADO]"
    )
    
    print(f"[*] Lanzando agy.exe para el Capítulo {cap} en segundo plano...")
    cmd = [
        str(AGY_EXE),
        "--project", str(WORKSPACE),
        "--print", instruccion_agente
    ]
    
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        print("[STDOUT]:")
        print(proc.stdout)
        if proc.stderr:
            print("[STDERR]:")
            print(proc.stderr)
            
        banner_dest = BANNERS_DIR / f"cap_{cap}.jpg"
        if banner_dest.exists():
            print(f"\n[ÉXITO] ¡Banner de Capítulo {cap} creado correctamente en {banner_dest}!")
            mostrar_notificacion_windows(
                "SOMBRA Novela",
                f"Imagen Generada SOMBRA capítulo {cap} (Haz clic para verla en grande)",
                ruta_imagen=banner_dest
            )
        else:
            print(f"\n[AVISO] Finalizado el proceso, pero no se detectó {banner_dest}")
    except Exception as e:
        print(f"[ERROR al ejecutar agy]: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

