#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recorta automáticamente bandas negras (letterbox) y ajusta cualquier imagen
a una proporción exacta 21:9 panorámica para las cabeceras de capítulo de SOMBRA.
Uso: python recortar_banner_21_9.py <ruta_origen> <numero_capitulo>
"""

import os
import sys
from PIL import Image, ImageChops

def trim_black_bars(im, threshold=12):
    bg = Image.new(im.mode, im.size, (0, 0, 0))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -threshold)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)
    return im

def crop_to_21_9(im):
    w, h = im.size
    target_ratio = 21.0 / 9.0
    current_ratio = w / float(h)
    if abs(current_ratio - target_ratio) < 0.01:
        return im
    if current_ratio < target_ratio:
        # Más alta que 21:9 -> recortar arriba y abajo centrando
        new_h = int(round(w / target_ratio))
        top = max(0, (h - new_h) // 2)
        return im.crop((0, top, w, top + new_h))
    else:
        # Más ancha que 21:9 -> recortar lados centrando
        new_w = int(round(h * target_ratio))
        left = max(0, (w - new_w) // 2)
        return im.crop((left, 0, left + new_w, h))

def main():
    if len(sys.argv) < 3:
        print("Uso: python recortar_banner_21_9.py <ruta_origen> <numero_capitulo>")
        sys.exit(1)

    src_path = sys.argv[1]
    chap_num = int(sys.argv[2])

    os.makedirs(os.path.join("img", "banners"), exist_ok=True)
    dest_path = os.path.join("img", "banners", f"cap_{chap_num}.jpg")

    im = Image.open(src_path).convert("RGB")
    im = trim_black_bars(im)
    im = crop_to_21_9(im)
    im.save(dest_path, "JPEG", quality=92, optimize=True)
    print(f"[OK] Banner 21:9 guardado en: {dest_path} ({im.size[0]}x{im.size[1]})")

if __name__ == "__main__":
    main()

