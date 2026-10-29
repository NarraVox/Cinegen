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
CineGen - Motor Oficial de Video: Kandinsky 6.0 Lite INT8 (3s / 5 Passos / VAE Tile 256)
Configuracao Oficial Consolidada:
  - Duracao: 3.04s (73 quadros a 24fps)
  - Passos DiT: 5 passos (Target oficial PiFlow Distilled)
  - Resolucao: 864x480 (480p real)
  - VAE: Hunyuan Video VAE oficial com Tile 256 e Overlap 32 (Zero estouro de VRAM / Zero memoria compartilhada)
  - Audio: BigVGAN 44.1kHz focado em Som Ambiente Natural (Sem trilha musical embutida)
"""

import json
import time
import argparse
import urllib.request
import urllib.error

COMFY_URL = "http://127.0.0.1:8188"
PROMPT_ENDPOINT = f"{COMFY_URL}/prompt"
HISTORY_ENDPOINT = f"{COMFY_URL}/history"

DEFAULT_VIDEO_PROMPT = (
    "The happy couple smiles warmly, looking at each other and towards the camera, "
    "evening breeze gently moving their hair, warm illuminated amusement park bokeh lights glowing in background, "
    "smooth cinematic camera movement, realistic natural lighting."
)

# Som ambiente puro e natural (diegético), sem trilha musical forçada
DEFAULT_AUDIO_PROMPT = (
    "Realistic natural ambient sound, soft gentle evening breeze rustling, "
    "subtle distant crowd murmur, peaceful outdoor park atmosphere, clean high fidelity foley, no music."
)

DEFAULT_NEGATIVE_PROMPT = "Static, cartoon, worst quality, low quality, deformed, blurry, loud noise, electronic music, distortion"

def build_workflow(
    image_name="casal_parque.png",
    video_prompt=DEFAULT_VIDEO_PROMPT,
    audio_prompt=DEFAULT_AUDIO_PROMPT,
    seed=64000,
    steps=5,
    length=73,
    prefix="CineGen_Take_3s_Oficial"
):
    return {
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
                "video_caption": video_prompt,
                "audio_caption": audio_prompt
            }
        },
        "6": {
            "class_type": "Kandinsky6TextEncode",
            "inputs": {
                "clip": ["2", 0],
                "video_caption": DEFAULT_NEGATIVE_PROMPT,
                "audio_caption": ""
            }
        },
        "7": {
            "class_type": "Kandinsky6EmptyLatent",
            "inputs": {
                "width": 864,
                "height": 480,
                "length": length,
                "fps": 24.0,
                "batch_size": 1
            }
        },
        "8": {
            "class_type": "LoadImage",
            "inputs": {
                "image": image_name
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
                "seed": seed,
                "steps": steps,
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
                "tile_size": 256,
                "overlap": 32,
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
                "filename_prefix": prefix,
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

def main():
    parser = argparse.ArgumentParser(description="CineGen - Gerador Oficial de Video 3s")
    parser.add_argument("--image", default="casal_parque.png", help="Nome da imagem em comfyui/input/")
    parser.add_argument("--video_prompt", default=DEFAULT_VIDEO_PROMPT, help="Prompt visual do video")
    parser.add_argument("--audio_prompt", default=DEFAULT_AUDIO_PROMPT, help="Prompt de som ambiente natural")
    parser.add_argument("--seed", type=int, default=64000, help="Seed para reproducibilidade")
    parser.add_argument("--prefix", default="CineGen_Take_3s_Oficial", help="Prefixo do arquivo mp4")
    args = parser.parse_args()

    wf = build_workflow(
        image_name=args.image,
        video_prompt=args.video_prompt,
        audio_prompt=args.audio_prompt,
        seed=args.seed,
        prefix=args.prefix
    )

    print("Enviando workflow consolidado do CineGen...")
    res = queue_prompt(wf)
    print("Sucesso! ID da Tarefa:", res.get("prompt_id"))

if __name__ == "__main__":
    main()
