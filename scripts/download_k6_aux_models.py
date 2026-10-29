"""
CineGen - Download Kandinsky 6 Auxiliary Shared Models
Downloads the lightweight components:
  1. clip_l.safetensors (246 MB)
  2. hunyuan_video_vae_bf16.safetensors (493 MB)
  3. v1-44.pth (1.22 GB)
  4. bigvgan_vocoder (bigvgan_generator.pt + config.json) (489 MB)
"""

import os
import shutil
from pathlib import Path
from huggingface_hub import hf_hub_download

TARGETS = [
    {
        "name": "clip_l.safetensors",
        "repo": "Comfy-Org/HunyuanVideo_repackaged",
        "subfolder": "split_files/text_encoders/clip_l.safetensors",
        "dest": Path(r"C:\CineGen\comfyui\models\text_encoders\clip_l.safetensors"),
    },
    {
        "name": "hunyuan_video_vae_bf16.safetensors",
        "repo": "Comfy-Org/HunyuanVideo_repackaged",
        "subfolder": "split_files/vae/hunyuan_video_vae_bf16.safetensors",
        "dest": Path(r"C:\CineGen\comfyui\models\vae\hunyuan_video_vae_bf16.safetensors"),
    },
    {
        "name": "v1-44.pth",
        "repo": "hkchengrex/MMAudio",
        "subfolder": "ext_weights/v1-44.pth",
        "dest": Path(r"C:\CineGen\comfyui\models\audio_vae\v1-44.pth"),
    },
    {
        "name": "bigvgan_generator.pt",
        "repo": "nvidia/bigvgan_v2_44khz_128band_512x",
        "subfolder": "bigvgan_generator.pt",
        "dest": Path(r"C:\CineGen\comfyui\models\audio_vae\bigvgan_vocoder\bigvgan_generator.pt"),
    },
    {
        "name": "config.json",
        "repo": "nvidia/bigvgan_v2_44khz_128band_512x",
        "subfolder": "config.json",
        "dest": Path(r"C:\CineGen\comfyui\models\audio_vae\bigvgan_vocoder\config.json"),
    },
]

def main():
    print("[CineGen] Iniciando download dos componentes auxiliares do Kandinsky 6...")
    for idx, target in enumerate(TARGETS, 1):
        dest = target["dest"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.stat().st_size > 0:
            print(f"[{idx}/{len(TARGETS)}] {target['name']} ja existe ({dest.stat().st_size / 1e6:.1f} MB), pulando.")
            continue
        
        print(f"\n[{idx}/{len(TARGETS)}] Baixando {target['name']} de {target['repo']}...")
        tmp_path = hf_hub_download(
            repo_id=target["repo"],
            filename=target["subfolder"],
        )
        shutil.copy2(tmp_path, dest)
        print(f"[{idx}/{len(TARGETS)}] Concluido -> {dest} ({dest.stat().st_size / 1e6:.1f} MB)")

    print("\n[CineGen] Todos os componentes auxiliares foram baixados com sucesso!")

if __name__ == "__main__":
    main()
