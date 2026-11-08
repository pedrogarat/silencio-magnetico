#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de sincronización segura con GitHub para superar el bloqueo de OneDrive.
Clona el repositorio en una carpeta temporal fuera de OneDrive,
sincroniza los archivos del workspace, hace commit y push a origin/main.
"""

import os
import shutil
import subprocess
import tempfile
import sys

WORKSPACE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMP_SYNC_DIR = os.path.join(tempfile.gettempdir(), "novela_gh_sync")
REPO_URL = "https://github.com/pedrogarat/sombra.git"

# Carpetas o patrones a excluir del copiado
EXCLUDE_DIRS = {".git", "__pycache__"}
EXCLUDE_EXTS = {".pyc"}

def run_cmd(cmd, cwd=None):
    print(f"[RUN] {cmd} (cwd: {cwd or '.'})")
    res = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print("[STDERR]", res.stderr)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed with code {res.returncode}: {cmd}")
    return res.stdout

def handle_remove_readonly(func, path, exc):
    import stat
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

def main():
    print("=" * 70)
    print("SINCRONIZACIÓN DE NOVELA MULTIVERSIÓN HACIA GITHUB")
    print(f"Origen: {WORKSPACE_DIR}")
    print(f"Destino temporal: {TEMP_SYNC_DIR}")
    print("=" * 70)

    # 1. Limpiar directorio temporal previo si existe
    if os.path.exists(TEMP_SYNC_DIR):
        print(f"Limpiando directorio temporal previo: {TEMP_SYNC_DIR}...")
        shutil.rmtree(TEMP_SYNC_DIR, onerror=handle_remove_readonly)
        if os.path.exists(TEMP_SYNC_DIR):
            import subprocess
            subprocess.run(f'cmd /c rmdir /s /q "{TEMP_SYNC_DIR}"', shell=True)

    # 2. Clonar el repositorio oficial desde GitHub
    print("\nClonando repositorio desde GitHub...")
    run_cmd(f'git clone --depth 1 {REPO_URL} "{TEMP_SYNC_DIR}"')

    # 3. Copiar todos los archivos actualizados desde WORKSPACE_DIR al repo temporal
    print("\nSincronizando archivos del espacio de trabajo al repositorio temporal...")
    for root, dirs, files in os.walk(WORKSPACE_DIR):
        # Excluir directorios ignorados
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        rel_dir = os.path.relpath(root, WORKSPACE_DIR)
        dest_dir = os.path.join(TEMP_SYNC_DIR, rel_dir) if rel_dir != "." else TEMP_SYNC_DIR

        os.makedirs(dest_dir, exist_ok=True)

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in EXCLUDE_EXTS:
                continue

            src_file = os.path.join(root, f)
            dest_file = os.path.join(dest_dir, f)

            shutil.copy2(src_file, dest_file)

    print("Copia completada con éxito.")

    # 4. Estado de Git en el repo temporal
    print("\nComprobando cambios en el repositorio temporal...")
    run_cmd("git status", cwd=TEMP_SYNC_DIR)

    # 5. Añadir cambios, hacer commit y push
    print("\nAñadiendo archivos al índice de Git...")
    run_cmd("git add -A", cwd=TEMP_SYNC_DIR)

    commit_msg = "docs: actualizar enlace web a https://pedrogarat.github.io/sombra/"
    print(f"\nCreando commit: '{commit_msg}'...")
    try:
        run_cmd(f'git commit -m "{commit_msg}"', cwd=TEMP_SYNC_DIR)
    except RuntimeError as e:
        if "nothing to commit" in str(e).lower():
            print("No hay cambios pendientes de commit.")
            return
        raise

    print("\nEnviando cambios a GitHub (origin/main)...")
    run_cmd("git push origin main", cwd=TEMP_SYNC_DIR)

    print("\n¡Despliegue y subida completados exitosamente!")

    # 6. Limpieza final
    print(f"Limpiando {TEMP_SYNC_DIR}...")
    shutil.rmtree(TEMP_SYNC_DIR, onerror=handle_remove_readonly)
    if os.path.exists(TEMP_SYNC_DIR):
        subprocess.run(f'cmd /c rmdir /s /q "{TEMP_SYNC_DIR}"', shell=True)

if __name__ == "__main__":
    main()
