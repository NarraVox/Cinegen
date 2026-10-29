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
CineGen - Kandinsky 6.0 Lite OrbitQuant Staged Video Pipeline
Local 480p (864x480) 4-second Image-to-Video generation on RTX 3050 (6GB VRAM)
Stages:
  1. Text Encoding (Qwen2.5-VL hybrid GPU/CPU -> unloaded)
  2. Video Diffusion (DiT W4A4 on GPU -> unloaded)
  3. Latent Decoding (VAE tiled + Audio Vocoder on GPU)
"""

import os
import gc
import sys
import time
from pathlib import Path
from PIL import Image
import torch

MODEL_DIR = Path(r"C:\CineGen\models\videos\Kandinsky-6-Lite-OrbitQuant-W4A4")
SOURCE_SNAPSHOT = Path.home() / ".cache" / "huggingface" / "hub" / "models--kandinskylab--Kandinsky-6.0-Lite-distill-5s-Diffusers" / "snapshots" / "efbaeb9961770cc82fece5b9cb2197049d8c983c"

INPUT_IMAGE = Path(r"C:\CineGen\comfyui\output\CineGen_Casal_Oficial_Tags_HD_00001_.png")
OUTPUT_VIDEO = Path(r"C:\CineGen\output\CineGen_Casal_Parque_480p_4s.mp4")

WIDTH = 864
HEIGHT = 480
NUM_FRAMES = 97  # 4.04s @ 24 fps
STEPS = 10
GUIDANCE_SCALE = 1.0
SEED = 61000

PROMPT = (
    "The happy couple smiles warmly, looking at each other and towards the camera, "
    "evening breeze gently moving their hair, warm illuminated amusement park bokeh lights glowing in background, "
    "smooth cinematic camera movement, realistic natural lighting. "
    "Audio: gentle ambient murmur of an evening amusement park, distant faint music, joyful atmosphere."
)


def prepare_input_image(img_path: Path, width: int, height: int) -> Image.Image:
    print(f"[CineGen Video] Preprocessing reference image {img_path.name} -> {width}x{height}...")
    img = Image.open(img_path).convert("RGB")
    target_ratio = width / height
    img_ratio = img.width / img.height

    if img_ratio > target_ratio:
        new_height = height
        new_width = int(height * img_ratio)
    else:
        new_width = width
        new_height = int(width / img_ratio)

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    left = (new_width - width) // 2
    top = (new_height - height) // 2
    img = img.crop((left, top, left + width, top + height))
    return img


def main():
    if not INPUT_IMAGE.exists():
        print(f"ERROR: Input image {INPUT_IMAGE} not found!")
        sys.exit(1)

    OUTPUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("CineGen - Kandinsky 6.0 Lite Staged Video Pipeline (RTX 3050 6GB)")
    print(f"Target Resolution: {WIDTH}x{HEIGHT} (480p)")
    print(f"Target Frames:     {NUM_FRAMES} (4.04s @ 24 FPS)")
    print(f"Inference Steps:   {STEPS}")
    print(f"Reference Image:   {INPUT_IMAGE.name}")
    print("=" * 65)

    import orbitquant
    from diffusers import Kandinsky6TI2VAPipeline, Kandinsky6Transformer3DModel
    from transformers import Qwen2_5_VLForConditionalGeneration
    from orbitquant.runtime.kandinsky6 import (
        install_kandinsky6_attention,
        install_kandinsky6_norm_fusion,
        install_kandinsky6_pointwise,
        install_kandinsky6_projection_reuse,
        install_kandinsky6_qk_norm,
    )
    from orbitquant.runtime.kandinsky6_video import (
        install_kandinsky6_video_io,
        install_kandinsky6_video_norm,
    )

    # -------------------------------------------------------------
    # STAGE 1: Prompt Encoding with Qwen2.5-VL (Hybrid GPU/CPU)
    # -------------------------------------------------------------
    print("\n[STAGE 1/3] Prompt Encoding with Qwen2.5-VL...")
    t0 = time.time()
    
    # Load Qwen with 4.0 GiB GPU cap and rest CPU
    text_encoder = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        str(MODEL_DIR / "text_encoder"),
        dtype=torch.bfloat16,
        device_map="auto",
        max_memory={0: "4.0GiB", "cpu": "12GiB"},
    )

    # Load temporary pipeline just to run encode_prompt
    pipe_encoder = Kandinsky6TI2VAPipeline.from_pretrained(
        str(SOURCE_SNAPSHOT),
        transformer=None,
        text_encoder=text_encoder,
        torch_dtype=torch.bfloat16,
    )
    if pipe_encoder.text_encoder_2 is not None:
        pipe_encoder.text_encoder_2.to("cuda")

    with torch.inference_mode():
        (
            prompt_embeds,
            pooled_prompt_embeds,
            prompt_attention_mask,
            negative_prompt_embeds,
            negative_pooled_prompt_embeds,
            negative_prompt_attention_mask,
        ) = pipe_encoder.encode_prompt(
            prompt=PROMPT,
            do_classifier_free_guidance=False,
            device="cuda",
        )

    # Keep embeddings on CPU until DiT needs them
    prompt_embeds = prompt_embeds.cpu()
    if pooled_prompt_embeds is not None:
        pooled_prompt_embeds = pooled_prompt_embeds.cpu()

    # Free Stage 1 completely from VRAM!
    del text_encoder
    del pipe_encoder
    gc.collect()
    torch.cuda.empty_cache()
    print(f"[STAGE 1/3] Completed in {time.time() - t0:.2f}s! VRAM allocated: {torch.cuda.memory_allocated() / 1024**2:.1f} MB (Freed!)")

    # -------------------------------------------------------------
    # STAGE 2: Video Diffusion with DiT W4A4 on GPU
    # -------------------------------------------------------------
    print("\n[STAGE 2/3] Initializing Kandinsky 6.0 Video Pipeline on GPU...")
    t1 = time.time()

    print("[STAGE 2/3] Loading quantized DiT W4A4 (3.54 GB)...")
    transformer = Kandinsky6Transformer3DModel.from_pretrained(
        str(MODEL_DIR), torch_dtype=torch.bfloat16
    )

    # Apply OrbitQuant attention & fusion
    install_kandinsky6_attention(transformer)
    install_kandinsky6_pointwise(transformer)
    install_kandinsky6_projection_reuse(transformer)
    install_kandinsky6_norm_fusion(transformer)
    install_kandinsky6_qk_norm(transformer)

    pipe = Kandinsky6TI2VAPipeline.from_pretrained(
        str(SOURCE_SNAPSHOT),
        transformer=transformer,
        text_encoder=None,
        torch_dtype=torch.bfloat16,
    )

    install_kandinsky6_video_io(pipe)
    install_kandinsky6_video_norm(pipe)

    # Low-memory spatial tiling for VAE
    pipe.vae.enable_tiling(
        tile_sample_min_height=272,
        tile_sample_min_width=320,
        tile_sample_stride_height=240,
        tile_sample_stride_width=288,
    )

    # Reclaim transformer memory before VAE decode
    original_decode = pipe.vae.decode
    def decode_after_reclaim(*args, **kwargs):
        print("\n[STAGE 3/3] Denoising finished. Offloading DiT to CPU before VAE decoding...")
        pipe.transformer.to("cpu")
        gc.collect()
        torch.cuda.empty_cache()
        print(f"[STAGE 3/3] VRAM before VAE decode: {torch.cuda.memory_allocated() / 1024**2:.1f} MB")
        return original_decode(*args, **kwargs)
    pipe.vae.decode = decode_after_reclaim

    # Enable sequential model CPU offload
    pipe.enable_model_cpu_offload()

    ref_image = prepare_input_image(INPUT_IMAGE, WIDTH, HEIGHT)

    print("\n[STAGE 2/3] >>> Running 10 PiFlow Denoising Steps at 480p on GPU...")
    generator = torch.Generator(device="cuda").manual_seed(SEED)

    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    gen_start = time.perf_counter()

    with torch.inference_mode():
        output = pipe(
            prompt_embeds=prompt_embeds.to("cuda"),
            pooled_prompt_embeds=pooled_prompt_embeds.to("cuda") if pooled_prompt_embeds is not None else None,
            image=ref_image,
            height=HEIGHT,
            width=WIDTH,
            num_frames=NUM_FRAMES,
            frame_rate=24.0,
            num_inference_steps=STEPS,
            guidance_scale=GUIDANCE_SCALE,
            generator=generator,
        )

    torch.cuda.synchronize()
    total_time = time.perf_counter() - gen_start
    peak_vram = torch.cuda.max_memory_allocated() / (1024**3)

    print(f"\n[STAGE 3/3] Video Generation & Decoding completed in {total_time:.2f}s!")
    print(f"[STAGE 3/3] Peak VRAM allocated: {peak_vram:.2f} GiB")

    print(f"\n[CineGen Video] Exporting MP4 with audio to {OUTPUT_VIDEO}...")
    from diffusers.utils import encode_video
    encode_video(
        output.frames[0],
        fps=24,
        output_path=str(OUTPUT_VIDEO),
        audio=output.audio[0][None] if hasattr(output, "audio") and output.audio is not None else None,
        audio_sample_rate=getattr(pipe, "audio_sample_rate", 24000),
    )

    print(f"\n=============================================================")
    print(f"SUCCESS! Video created: {OUTPUT_VIDEO}")
    print(f"File size: {OUTPUT_VIDEO.stat().st_size / (1024*1024):.2f} MB")
    print(f"=============================================================")


if __name__ == "__main__":
    main()
