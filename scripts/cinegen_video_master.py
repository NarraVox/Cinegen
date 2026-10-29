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

"""
CineGen - Master Pipeline de Vídeo e Upscale Full HD 1080p
Versão Consolidada Oficial:
  1. Geração de Vídeo: Kandinsky 6.0 Lite INT8 (PiFlow 5 steps, Hunyuan VAE Tile 256, 480p, 24fps)
  2. Upscale Ultrarrápido: 2x-NomosUni SPAN (Full HD 1920x1080 em ~10 segundos, áudio sincronizado)
"""

import os
import sys
import time
import json
import argparse
import urllib.request
import subprocess

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

COMFY_URL = "http://127.0.0.1:8188"
PROMPT_ENDPOINT = f"{COMFY_URL}/prompt"
HISTORY_ENDPOINT = f"{COMFY_URL}/history"

DEFAULT_MODEL_SPAN = r"C:\CineGen\comfyui\models\upscale_models\2xNomosUni_span_multijpg.safetensors"

def queue_kandinsky_generation(
    image_name: str,
    video_prompt: str,
    audio_prompt: str,
    prefix: str,
    seed: int = 64000
) -> str:
    from run_comfy_kandinsky_3s import build_workflow
    wf = build_workflow(
        image_name=image_name,
        video_prompt=video_prompt,
        audio_prompt=audio_prompt,
        seed=seed,
        prefix=prefix
    )
    payload = json.dumps({"prompt": wf}).encode("utf-8")
    req = urllib.request.Request(PROMPT_ENDPOINT, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        prompt_id = res.get("prompt_id")
        print(f"🚀 Tarefa enviada ao ComfyUI! Prompt ID: {prompt_id}", flush=True)
        return prompt_id

def wait_for_completion(prompt_id: str, timeout_sec: int = 900) -> str:
    print(f"⏳ Aguardando renderização do vídeo base ({prompt_id})...", flush=True)
    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            req = urllib.request.Request(f"{HISTORY_ENDPOINT}/{prompt_id}")
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                if prompt_id in data:
                    item = data[prompt_id]
                    status = item.get("status", {})
                    if status.get("completed", False):
                        outputs = item.get("outputs", {})
                        # Node 19 is SaveVideo
                        for nid, node_out in outputs.items():
                            if "images" in node_out:
                                for img in node_out["images"]:
                                    fname = img.get("filename")
                                    if fname and fname.endswith(".mp4"):
                                        full_path = os.path.join(r"C:\CineGen\comfyui\output", fname)
                                        print(f"✅ Vídeo gerado em {time.time()-start:.1f}s: {full_path}", flush=True)
                                        return full_path
        except Exception:
            pass
        time.sleep(5)
    raise TimeoutError("Tempo limite excedido aguardando o ComfyUI.")

def run_upscale(input_path: str, output_path: str = None) -> str:
    from upscale_video_pipeline import upscale_video_to_1080p
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_1080p{ext}"
    
    t0 = time.time()
    upscale_video_to_1080p(input_path, output_path, model_path=DEFAULT_MODEL_SPAN)
    print(f"⚡ Upscale finalizado em {time.time()-t0:.1f}s! Arquivo: {output_path}", flush=True)
    return output_path

def main():
    parser = argparse.ArgumentParser(description="CineGen - Master Pipeline de Vídeo & Upscale 1080p")
    parser.add_argument("--mode", choices=["all", "generate", "upscale"], default="upscale", help="Modo de execução")
    parser.add_argument("--image", default="amiga_loira_solo.png", help="Imagem de referência em comfyui/input/")
    parser.add_argument("--video_prompt", default="The character smiles warmly, evening breeze moving hair, cinematic lighting", help="Prompt do vídeo")
    parser.add_argument("--audio_prompt", default="Natural soft evening breeze, peaceful ambient sound, clean foley, no music", help="Prompt de som")
    parser.add_argument("--prefix", default="CineGen_Scene", help="Prefixo do arquivo")
    parser.add_argument("--video_input", help="Arquivo mp4 de entrada para modo upscale")
    parser.add_argument("--video_output", help="Arquivo mp4 de saída para modo upscale")
    parser.add_argument("--seed", type=int, default=64000)

    args = parser.parse_args()

    if args.mode == "upscale":
        target_in = args.video_input or r"C:\CineGen\comfyui\output\CineGen_Amiga_Solo_Loiro_3s_00001_.mp4"
        run_upscale(target_in, args.video_output)
    elif args.mode == "generate":
        pid = queue_kandinsky_generation(args.image, args.video_prompt, args.audio_prompt, args.prefix, args.seed)
        wait_for_completion(pid)
    elif args.mode == "all":
        pid = queue_kandinsky_generation(args.image, args.video_prompt, args.audio_prompt, args.prefix, args.seed)
        raw_video = wait_for_completion(pid)
        run_upscale(raw_video, args.video_output)

if __name__ == "__main__":
    main()
