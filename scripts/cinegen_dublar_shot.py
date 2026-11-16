# Copyright (c) 2026 Paulo Henrik Carvalho Araújo
# CineGen - Módulo Autônomo de Dublagem PT-BR por Cena
# Executado como subprocesso isolado para garantir 100% de liberação de VRAM após o término.

import os
import sys
import argparse
import subprocess
from pathlib import Path
import soundfile as sf
import numpy as np

BASE_DIR = Path(r"C:\IA_dublagem")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from nexus.core.tts import gerar_audio_qwen3, unload_qwen3_model

def mux_shot_audio(video_in: str, audio_wav: str, start_offset: float, video_out: str):
    data, sr = sf.read(audio_wav)
    lead_silence = np.zeros(int(start_offset * sr), dtype=data.dtype)
    combined = np.concatenate([lead_silence, data])
    
    res = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_in],
        capture_output=True, text=True, check=True
    )
    v_dur = float(res.stdout.strip())
    needed_samples = int(v_dur * sr)
    if len(combined) < needed_samples:
        pad = np.zeros(needed_samples - len(combined), dtype=combined.dtype)
        combined = np.concatenate([combined, pad])
    else:
        combined = combined[:needed_samples]
        
    temp_padded = Path(video_out).parent / f"temp_padded_{Path(video_out).stem}.wav"
    sf.write(str(temp_padded), combined, sr)
    
    cmd = [
        'ffmpeg', '-y',
        '-i', video_in,
        '-i', str(temp_padded),
        '-c:v', 'copy',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-ar', '48000',
        '-ac', '2',
        '-shortest',
        video_out
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if temp_padded.exists():
        temp_padded.unlink()

def main():
    parser = argparse.ArgumentParser(description="CineGen Dublagem Subprocess")
    parser.add_argument("--video_in", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--ref_audio", required=True)
    parser.add_argument("--speaker_id", default=None, help="ID único do locutor (ex: ator_01, narrador)")
    parser.add_argument("--emotion", default="NORMAL")
    parser.add_argument("--temp", type=float, default=0.60)
    parser.add_argument("--start_offset", type=float, default=0.25)
    parser.add_argument("--video_out", required=True)
    args = parser.parse_args()

    spk_id = args.speaker_id or Path(args.ref_audio).stem
    print(f"[CineGen TTS] Dublando cena para locutor '{spk_id}': {args.text} (Emoção: {args.emotion}, Temp: {args.temp})", flush=True)

    # Obter duração do vídeo de entrada
    res = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', args.video_in],
        capture_output=True, text=True, check=True
    )
    v_dur = float(res.stdout.strip())
    budget = max(0.5, v_dur - args.start_offset)

    temp_wav = Path(args.video_out).parent / f"temp_raw_{Path(args.video_out).stem}.wav"

    # Geração com Qwen3-TTS
    gerar_audio_qwen3(
        text=args.text,
        ref_audio_path=args.ref_audio,
        output_path=str(temp_wav),
        emotion=args.emotion,
        max_duration=budget,
        speaker_id=spk_id
    )

    # Descarrega modelo na memória local da lib
    unload_qwen3_model()

    # Mux com o vídeo em 48kHz stereo
    mux_shot_audio(args.video_in, str(temp_wav), args.start_offset, args.video_out)

    if temp_wav.exists():
        temp_wav.unlink()

    print(f"[CineGen TTS] Dublagem concluída com sucesso: {args.video_out}", flush=True)

if __name__ == "__main__":
    main()
