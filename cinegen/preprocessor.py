# Copyright (c) 2026 Paulo Henrik Carvalho Araújo
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from pathlib import Path
from PIL import Image, ImageOps

COMFY_INPUT_DIR = Path(r"C:\CineGen\comfyui\input")

def preprocess_reference(
    image_path: str | Path,
    output_name: str | None = None,
    target_size: tuple[int, int] = (576, 1024),
    clean_mobile_ui: bool = True
) -> str:
    """
    Normaliza a imagem de referência para o padrão oficial CineGen:
    1. Corrige rotação EXIF de fotos de smartphone.
    2. Remove barras de status / stories se clean_mobile_ui for True.
    3. Ajusta o enquadramento de busto/rosto para proporção 9:16 (576x1024).
    4. Salva diretamente em C:\\CineGen\\comfyui\\input\\ e retorna o nome do arquivo.
    """
    path = Path(image_path)
    if not path.is_absolute():
        path = Path(r"C:\CineGen") / path

    if not path.exists():
        raise FileNotFoundError(f"Imagem não encontrada: {path}")

    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    w, h = img.size

    # Se for print de celular (muito comprido, ex: proporção próxima de 9:20), limpa UI superior/inferior
    if clean_mobile_ui and (h / w) > 2.0:
        crop_h = int(h * 0.72)
        crop_w = int(crop_h * (target_size[0] / target_size[1]))
        if crop_w > w:
            crop_w = w
            crop_h = int(crop_w * (target_size[1] / target_size[0]))
        crop_x = int((w - crop_w) / 2)
        crop_y = int(h * 0.13) # Pula a barra superior do story
        img = img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
    elif (w / h) != (target_size[0] / target_size[1]):
        # Se for foto horizontal larga (ex: 1344x768), mantém aspecto ou ajusta
        # Se for imagem de casal, não distorce
        target_aspect = target_size[0] / target_size[1]
        current_aspect = w / h
        if current_aspect > target_aspect:
            # Mais larga que o target -> corta bordas laterais centralizando
            new_w = int(h * target_aspect)
            offset = int((w - new_w) / 2)
            img = img.crop((offset, 0, offset + new_w, h))
        else:
            # Mais alta que o target
            new_h = int(w / target_aspect)
            offset = int((h - new_h) / 2)
            img = img.crop((0, offset, w, offset + new_h))

    resized = img.resize(target_size, Image.Resampling.LANCZOS)
    COMFY_INPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not output_name:
        stem = path.stem.replace(" ", "_")
        output_name = f"cinegen_ref_{stem}.png"

    dest_path = COMFY_INPUT_DIR / output_name
    resized.save(dest_path)
    return output_name
