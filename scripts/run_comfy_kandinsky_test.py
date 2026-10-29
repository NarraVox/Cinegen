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
CineGen - Run Kandinsky 6.0 Lite Distill INT8 Video Generation via ComfyUI
Executes 4-second (97 frames @ 24fps) 480p Image-to-Video+Audio using:
  - DiT: Kandinsky-6.0-Lite-Distilled-5s-int8-convrot.safetensors (3.25 GB)
  - Text: Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf + clip_l.safetensors
  - VAE: hunyuan_video_vae_bf16.safetensors (Tiled decode)
  - Audio: v1-44.pth + bigvgan_vocoder
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path

COMFY_URL = "http://127.0.0.1:8188"
PROMPT_ENDPOINT = f"{COMFY_URL}/prompt"
HISTORY_ENDPOINT = f"{COMFY_URL}/history"

PROMPT_TEXT = (
    "The happy couple smiles warmly, looking at each other and towards the camera, "
    "evening breeze gently moving their hair, warm illuminated amusement park bokeh lights glowing in background, "
    "smooth cinematic camera movement, realistic natural lighting."
)

AUDIO_PROMPT = "Gentle ambient murmur of an evening amusement park, distant faint music, joyful atmosphere."

NEGATIVE_PROMPT = "Static, cartoon, worst quality, low quality, deformed, blurry"

WORKFLOW = {
    "1": {
        "class_type": "UNETLoader",
        "inputs": {
            "unet_name": "Kandinsky-6.0-Lite-Distilled-5s-int8-convrot.safetensors",
            "weight_dtype": "default"
        }
    },
    "2": {
        "class_type": "DualCLIPLoaderGGUF",
        "inputs": {
            "clip_name1": "Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf",
            "clip_name2": "clip_l.safetensors",
            "type": "kandinsky5"
        }
    },
    "3": {
        "class_type": "VAELoader",
        "inputs": {
            "vae_name": "hunyuan_video_vae_bf16.safetensors"
        }
    },
    "4": {
        "class_type": "Kandinsky6AudioVAELoader",
        "inputs": {
            "tod_vae": "v1-44.pth",
            "bigvgan_dir": "bigvgan_vocoder",
            "mode": "44k",
            "scaling_factor": 0.417,
            "model_variant": "pretrain / distill"
        }
    },
    "5": {
        "class_type": "Kandinsky6TextEncode",
        "inputs": {
            "clip": ["2", 0],
            "video_caption": PROMPT_TEXT,
            "audio_caption": AUDIO_PROMPT
        }
    },
    "6": {
        "class_type": "Kandinsky6TextEncode",
        "inputs": {
            "clip": ["2", 0],
            "video_caption": NEGATIVE_PROMPT,
            "audio_caption": ""
        }
    },
    "7": {
        "class_type": "Kandinsky6EmptyLatent",
        "inputs": {
            "width": 864,
            "height": 480,
            "length": 97,
            "fps": 24.0,
            "batch_size": 1
        }
    },
    "8": {
        "class_type": "LoadImage",
        "inputs": {
            "image": "casal_parque.png"
        }
    },
    "9": {
        "class_type": "ImageScale",
        "inputs": {
            "image": ["8", 0],
            "upscale_method": "bilinear",
            "width": 864,
            "height": 480,
            "crop": "center"
        }
    },
    "10": {
        "class_type": "VAEEncode",
        "inputs": {
            "pixels": ["9", 0],
            "vae": ["3", 0]
        }
    },
    "11": {
        "class_type": "Kandinsky6ImageToVideoAudio",
        "inputs": {
            "positive": ["5", 0],
            "negative": ["6", 0],
            "empty_latent": ["7", 0],
            "reference_latent": ["10", 0]
        }
    },
    "12": {
        "class_type": "Kandinsky6Sampler",
        "inputs": {
            "model": ["1", 0],
            "seed": 61000,
            "steps": 10,
            "cfg": 1.0,
            "sampler_name": "euler",
            "scheduler": "simple",
            "positive": ["11", 0],
            "negative": ["11", 1],
            "latent_image": ["11", 2],
            "denoise": 1.0
        }
    },
    "13": {
        "class_type": "Kandinsky6RemoveReferenceLatent",
        "inputs": {
            "joint_latent": ["12", 0]
        }
    },
    "14": {
        "class_type": "VAEDecodeTiled",
        "inputs": {
            "samples": ["13", 0],
            "vae": ["3", 0],
            "tile_size": 512,
            "overlap": 64,
            "temporal_size": 64,
            "temporal_overlap": 8
        }
    },
    "15": {
        "class_type": "Kandinsky6AudioVAEDecode",
        "inputs": {
            "audio_vae": ["4", 0],
            "joint_latent": ["13", 0]
        }
    },
    "18": {
        "class_type": "CreateVideo",
        "inputs": {
            "images": ["14", 0],
            "fps": ["7", 1],
            "audio": ["15", 0]
        }
    },
    "19": {
        "class_type": "SaveVideo",
        "inputs": {
            "video": ["18", 0],
            "filename_prefix": "CineGen_Casal_Parque_480p_INT8",
            "format": "mp4",
            "format.codec": "h264",
            "format.codec.encoding": "auto"
        }
    }
}

def queue_prompt(prompt_workflow):
    payload = json.dumps({"prompt": prompt_workflow}).encode("utf-8")
    req = urllib.request.Request(
        PROMPT_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def get_history(prompt_id):
    url = f"{HISTORY_ENDPOINT}/{prompt_id}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError:
        return None

def main():
    print("=" * 65)
    print(" CineGen - Teste de Velocidade Kandinsky 6.0 INT8 (ComfyUI)")
    print("=" * 65)
    print("[1/3] Enviando workflow para a fila do ComfyUI...")
    
    try:
        res = queue_prompt(WORKFLOW)
        prompt_id = res.get("prompt_id")
        print(f"[OK] Tarefa enfileirada com ID: {prompt_id}")
    except Exception as e:
        print(f"[ERRO] Falha ao enviar workflow: {e}")
        return

    print("\n[2/3] Monitorando execucao em tempo real...")
    start_time = time.time()
    
    while True:
        history = get_history(prompt_id)
        if history and prompt_id in history:
            task_info = history[prompt_id]
            status = task_info.get("status", {})
            completed = status.get("completed", False)
            outputs = task_info.get("outputs", {})
            
            elapsed = time.time() - start_time
            if completed:
                print(f"\n[3/3] SUCESSO! Video gerado em {elapsed:.1f} segundos ({elapsed/60:.2f} minutos)!")
                print(f"Outputs gerados: {json.dumps(outputs, indent=2)}")
                break
            elif status.get("status_str") == "error":
                print(f"\n[ERRO] A geracao falhou com erro:")
                messages = status.get("messages", [])
                for msg in messages:
                    print(msg)
                break
        
        time.sleep(2)

if __name__ == "__main__":
    main()
