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

def build_flux_workflow(
    prompt_text: str,
    reference_images: list[str],
    output_prefix: str = "CineGen_Output",
    seed: int = 941,
    steps: int = 8,
    width: int = 1280,
    height: int = 720,
    cfg: float = 1.0,
    sampler_name: str = "euler",
    scheduler: str = "simple"
) -> dict:
    """
    Constrói a árvore de nós ComfyUI para FLUX.3 Klein com GGUF e encadeamento de referências.
    """
    wf = {
        "1": {
            "class_type": "UnetLoaderGGUF",
            "inputs": {
                "unet_name": "flux-3-image-klein-Q4_K_M.gguf"
            }
        },
        "2": {
            "class_type": "CLIPLoaderGGUF",
            "inputs": {
                "clip_name": "Qwen3-VL-4B-Instruct-Q4_K_M.gguf",
                "type": "flux3"
            }
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "ae.safetensors"
            }
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["2", 0],
                "text": prompt_text
            }
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["2", 0],
                "text": ""
            }
        }
    }

    last_cond = ["4", 0]
    node_id = 6

    # Encadeamento dinâmico de ReferenceLatent para cada imagem de referência
    for idx, img_name in enumerate(reference_images):
        load_id = str(node_id)
        encode_id = str(node_id + 1)
        ref_id = str(node_id + 2)
        node_id += 3

        wf[load_id] = {
            "class_type": "LoadImage",
            "inputs": {
                "image": img_name
            }
        }
        wf[encode_id] = {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": [load_id, 0],
                "vae": ["3", 0]
            }
        }
        wf[ref_id] = {
            "class_type": "ReferenceLatent",
            "inputs": {
                "conditioning": last_cond,
                "latent": [encode_id, 0]
            }
        }
        last_cond = [ref_id, 0]

    empty_id = str(node_id)
    ksampler_id = str(node_id + 1)
    decode_id = str(node_id + 2)
    save_id = str(node_id + 3)

    wf[empty_id] = {
        "class_type": "EmptySD3LatentImage",
        "inputs": {
            "width": width,
            "height": height,
            "batch_size": 1
        }
    }
    wf[ksampler_id] = {
        "class_type": "KSampler",
        "inputs": {
            "model": ["1", 0],
            "positive": last_cond,
            "negative": ["5", 0],
            "latent_image": [empty_id, 0],
            "seed": seed,
            "steps": steps,
            "cfg": cfg,
            "sampler_name": sampler_name,
            "scheduler": scheduler,
            "denoise": 1.0
        }
    }
    wf[decode_id] = {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": [ksampler_id, 0],
            "vae": ["3", 0]
        }
    }
    wf[save_id] = {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": output_prefix,
            "images": [decode_id, 0]
        }
    }

    return wf
