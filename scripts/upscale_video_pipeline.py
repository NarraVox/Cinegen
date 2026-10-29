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
import sys
import time
import subprocess
import torch
import cv2
import numpy as np
import spandrel
import torch.nn.functional as F

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def upscale_video_to_1080p(
    input_path: str,
    output_path: str,
    model_path: str = r"C:\CineGen\comfyui\models\upscale_models\2xNomosUni_span_multijpg.safetensors",
    target_width: int = 1920,
    target_height: int = 1080
):
    print("🎬 Iniciando Upscale 2x-NomosUni SPAN para Full HD 1080p...", flush=True)
    print(f"📁 Entrada: {input_path}", flush=True)
    print(f"📁 Saída: {output_path}", flush=True)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Modelo não encontrado: {model_path}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"⚡ Dispositivo: {device} ({torch.cuda.get_device_name(0) if device == 'cuda' else 'CPU'})", flush=True)

    # Carrega modelo SPAN
    print("📦 Carregando modelo 2x-NomosUni SPAN...", flush=True)
    descriptor = spandrel.ModelLoader().load_from_file(model_path)
    model = descriptor.model.to(device).half().eval()
    print(f"✅ Modelo carregado com sucesso! Arquitetura: SPAN (Escala: {descriptor.scale}x)", flush=True)

    # Abre vídeo original
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError("Falha ao abrir vídeo de entrada com OpenCV.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"🎞️ Vídeo original: {orig_w}x{orig_h} | {fps:.2f} fps | {total_frames} frames", flush=True)

    temp_dir = os.path.dirname(output_path)
    temp_audio = os.path.join(temp_dir, "temp_audio_span.aac")
    has_audio = False
    try:
        audio_cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vn", "-acodec", "copy", temp_audio
        ]
        res = subprocess.run(audio_cmd, capture_output=True)
        if res.returncode == 0 and os.path.exists(temp_audio) and os.path.getsize(temp_audio) > 0:
            has_audio = True
            print("🎵 Áudio extraído com sucesso para preservação!", flush=True)
    except Exception as e:
        print(f"⚠️ Aviso ao extrair áudio: {e}", flush=True)

    # Testa se NVENC está disponível
    temp_video = os.path.join(temp_dir, "temp_upscaled_span.mp4")
    encoder = "libx264"
    preset_args = ["-preset", "veryfast", "-crf", "18"]
    try:
        test_nvenc = subprocess.run(["ffmpeg", "-f", "lavfi", "-i", "nullsrc=s=64x64:d=0.1", "-c:v", "h264_nvenc", "-f", "null", "-"], capture_output=True)
        if test_nvenc.returncode == 0:
            encoder = "h264_nvenc"
            preset_args = ["-preset", "p4", "-cq", "19"]
            print("🚀 Aceleração de Hardware NVIDIA NVENC ativada!", flush=True)
    except Exception:
        pass

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{target_width}x{target_height}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", encoder,
        "-pix_fmt", "yuv420p"
    ] + preset_args + [temp_video]

    pipe = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    start_time = time.time()
    processed = 0

    print(f"⚡ Processando {total_frames} quadros em super-resolução SPAN...", flush=True)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Frame BGR -> RGB Tensor FP16 na GPU
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_t = torch.from_numpy(frame_rgb).permute(2, 0, 1).unsqueeze(0).to(device)
            img_t = img_t.half() / 255.0

            with torch.inference_mode():
                # Upscale 2x nativo via SPAN
                out_t = model(img_t)
                # Interpolação GPU direta para Full HD (1920x1080)
                out_1080 = F.interpolate(out_t, size=(target_height, target_width), mode='bicubic', align_corners=False)

            # Converte de volta na GPU antes de transferir para a CPU
            out_bytes = (out_1080.squeeze(0).clamp(0, 1).permute(1, 2, 0) * 255.0).byte().cpu().numpy()
            out_bgr = cv2.cvtColor(out_bytes, cv2.COLOR_RGB2BGR)

            pipe.stdin.write(out_bgr.tobytes())

            processed += 1
            if processed % 15 == 0 or processed == total_frames:
                elapsed = time.time() - start_time
                fps_proc = processed / elapsed
                eta = (total_frames - processed) / fps_proc if fps_proc > 0 else 0
                print(f"⏳ SPAN: {processed}/{total_frames} frames ({processed/total_frames*100:.1f}%) | {fps_proc:.2f} fps | Restante: {eta:.0f}s", flush=True)

    finally:
        cap.release()
        pipe.stdin.close()
        pipe.wait()

    total_time = time.time() - start_time
    print(f"✨ Upscale SPAN concluído em {total_time:.1f} segundos ({total_time/60:.2f} minutos)!", flush=True)

    # Multiplexa áudio
    if has_audio and os.path.exists(temp_audio):
        merge_cmd = [
            "ffmpeg", "-y",
            "-i", temp_video,
            "-i", temp_audio,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]
        subprocess.run(merge_cmd, check=True, capture_output=True)
        if os.path.exists(temp_audio): os.remove(temp_audio)
        if os.path.exists(temp_video): os.remove(temp_video)
    else:
        if os.path.exists(output_path): os.remove(output_path)
        os.rename(temp_video, output_path)

    out_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"🎉 Vídeo 1080p SPAN finalizado com sucesso!", flush=True)
    print(f"💾 Arquivo final: {output_path} ({out_size:.2f} MB)", flush=True)

if __name__ == "__main__":
    input_file = r"C:\CineGen\comfyui\output\CineGen_Amiga_Solo_Loiro_3s_00001_.mp4"
    output_file = r"C:\CineGen\comfyui\output\CineGen_Amiga_Solo_Loiro_3s_SPAN_1080p.mp4"
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
        
    upscale_video_to_1080p(input_file, output_file)
