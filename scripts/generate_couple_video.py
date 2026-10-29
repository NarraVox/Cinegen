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
CineGen - Kandinsky 6.0 Lite OrbitQuant Video Generator
Local 480p (864x480) 4-second Image-to-Video generation on RTX 3050 (6GB VRAM)
"""

import os
import sys
import time
import json
from pathlib import Path
from PIL import Image
import torch

MODEL_DIR = Path(r"C:\CineGen\models\videos\Kandinsky-6-Lite-OrbitQuant-W4A4")
SOURCE_SNAPSHOT = Path.home() / ".cache" / "huggingface" / "hub" / "models--kandinskylab--Kandinsky-6.0-Lite-distill-5s-Diffusers" / "snapshots" / "efbaeb9961770cc82fece5b9cb2197049d8c983c"

INPUT_IMAGE = Path(r"C:\CineGen\comfyui\output\CineGen_Casal_Oficial_Tags_HD_00001_.png")
OUTPUT_VIDEO = Path(r"C:\CineGen\output\CineGen_Casal_Parque_480p_4s.mp4")

WIDTH = 864
HEIGHT = 480
NUM_FRAMES = 97  # 4.04 seconds @ 24 fps (4n + 1 formula)
STEPS = 10
GUIDANCE_SCALE = 1.0
SEED = 61000
ALLOCATOR_CAP_GIB = 5.2

PROMPT = (
    "The couple smiles warmly, gently looking at each other and turning towards the camera, "
    "soft evening breeze subtly moving their hair, warm illuminated amusement park bokeh lights glowing in background, "
    "smooth cinematic camera movement, realistic natural lighting. "
    "Audio: gentle ambient murmur of an evening amusement park, distant faint music and cheerful atmosphere."
)


def configure_memory_and_pipeline():
    print(f"[CineGen Video] Setting GPU memory allocator cap to {ALLOCATOR_CAP_GIB} GiB...")
    device = torch.cuda.current_device()
    total = torch.cuda.get_device_properties(device).total_memory
    fraction = (ALLOCATOR_CAP_GIB * 1024**3) / total
    if fraction < 1.0:
        torch.cuda.set_per_process_memory_fraction(fraction, device)
    torch.backends.cudnn.benchmark = False

    from diffusers import Kandinsky6TI2VAPipeline, Kandinsky6Transformer3DModel
    from transformers import Qwen2_5_VLForConditionalGeneration
    import orbitquant
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

    print("[CineGen Video] Loading quantized DiT W4A4...")
    transformer = Kandinsky6Transformer3DModel.from_pretrained(
        str(MODEL_DIR), torch_dtype=torch.bfloat16
    )

    print("[CineGen Video] Loading text encoder Qwen2.5-VL W4A6...")
    encoder = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        str(MODEL_DIR / "text_encoder"), dtype=torch.bfloat16
    )

    print("[CineGen Video] Initializing Kandinsky6TI2VAPipeline...")
    pipe = Kandinsky6TI2VAPipeline.from_pretrained(
        str(SOURCE_SNAPSHOT),
        transformer=transformer,
        text_encoder=encoder,
        torch_dtype=torch.bfloat16,
    )

    print("[CineGen Video] Applying OrbitQuant runtime optimizations (INT8 attention, fusion)...")
    install_kandinsky6_attention(pipe.transformer)
    install_kandinsky6_pointwise(pipe.transformer)
    install_kandinsky6_projection_reuse(pipe.transformer)
    install_kandinsky6_norm_fusion(pipe.transformer)
    install_kandinsky6_qk_norm(pipe.transformer)
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
        pipe.maybe_free_model_hooks()
        torch.cuda.empty_cache()
        return original_decode(*args, **kwargs)
    pipe.vae.decode = decode_after_reclaim

    # Enable sequential submodel CPU offload
    print("[CineGen Video] Enabling model CPU offload...")
    pipe.enable_model_cpu_offload()

    return pipe


def prepare_input_image(img_path: Path, width: int, height: int) -> Image.Image:
    print(f"[CineGen Video] Preparing input image: {img_path} -> {width}x{height}...")
    img = Image.open(img_path).convert("RGB")
    # Resize keeping aspect ratio, then crop center
    target_ratio = width / height
    img_ratio = img.width / img.height

    if img_ratio > target_ratio:
        # Image is wider: fit height and crop width
        new_height = height
        new_width = int(height * img_ratio)
    else:
        # Image is taller: fit width and crop height
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

    print("=" * 60)
    print("CineGen - Kandinsky 6.0 Lite OrbitQuant Video Engine")
    print(f"Target Resolution: {WIDTH}x{HEIGHT} (480p)")
    print(f"Target Frames:     {NUM_FRAMES} (4.04s @ 24 FPS)")
    print(f"Inference Steps:   {STEPS}")
    print(f"Input Image:       {INPUT_IMAGE.name}")
    print("=" * 60)

    pipe = configure_memory_and_pipeline()
    ref_image = prepare_input_image(INPUT_IMAGE, WIDTH, HEIGHT)

    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    start_time = time.perf_counter()

    print("\n[CineGen Video] >>> Starting Video Generation (Image-to-Video)...")
    generator = torch.Generator(device="cuda").manual_seed(SEED)

    with torch.inference_mode():
        output = pipe(
            prompt=PROMPT,
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
    elapsed = time.perf_counter() - start_time
    peak_vram = torch.cuda.max_memory_allocated() / (1024**3)

    print(f"\n[CineGen Video] Generation completed in {elapsed:.2f}s!")
    print(f"[CineGen Video] Peak VRAM allocated: {peak_vram:.2f} GiB")

    print(f"[CineGen Video] Exporting MP4 with audio to {OUTPUT_VIDEO}...")
    from diffusers.utils import encode_video
    encode_video(
        output.frames[0],
        fps=24,
        output_path=str(OUTPUT_VIDEO),
        audio=output.audio[0][None] if hasattr(output, "audio") and output.audio is not None else None,
        audio_sample_rate=getattr(pipe, "audio_sample_rate", 24000),
    )

    print(f"\n[CineGen Video] SUCCESS! Video saved at: {OUTPUT_VIDEO}")
    print(f"File size: {OUTPUT_VIDEO.stat().st_size / (1024*1024):.2f} MB")


if __name__ == "__main__":
    main()
