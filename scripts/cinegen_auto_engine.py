# Copyright (c) 2026 Paulo Henrik Carvalho Araújo
# CineGen - Motor Autônomo de Produção (Auto-Pipeline Watcher)
# Monitora a fila C:\CineGen\queue\inbox, executa todo o fluxo de imagem, vídeo,
# upscale, dublagem e sincronização MEGA com liberação estrita de VRAM entre etapas.

import os
import sys
import time
import json
import shutil
import argparse
import traceback
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Diretórios Mestres
BASE_DIR = Path(r"C:\CineGen")
QUEUE_DIR = BASE_DIR / "queue"
INBOX_DIR = QUEUE_DIR / "inbox"
PROCESSING_DIR = QUEUE_DIR / "processing"
COMPLETED_DIR = QUEUE_DIR / "completed"
FAILED_DIR = QUEUE_DIR / "failed"

COMFY_DIR = BASE_DIR / "comfyui"
COMFY_INPUT = COMFY_DIR / "input"
COMFY_OUTPUT = COMFY_DIR / "output"
COMFY_URL = "http://127.0.0.1:8188"
PROMPT_ENDPOINT = f"{COMFY_URL}/prompt"
HISTORY_ENDPOINT = f"{COMFY_URL}/history"
FREE_ENDPOINT = f"{COMFY_URL}/free"

MEGA_DIR = Path.home() / "Documents" / "MEGA"
VOICES_DIR = BASE_DIR / "reference" / "voices"

def ensure_dirs():
    for d in [INBOX_DIR, PROCESSING_DIR, COMPLETED_DIR, FAILED_DIR, COMFY_INPUT, COMFY_OUTPUT]:
        d.mkdir(parents=True, exist_ok=True)

def free_comfyui_vram():
    """Chama o endpoint /free do ComfyUI para descarregar todos os modelos da VRAM."""
    try:
        payload = json.dumps({"unload_models": True, "free_memory": True}).encode("utf-8")
        req = urllib.request.Request(FREE_ENDPOINT, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print("⚡ [VRAM GUARD] Modelos descarregados do ComfyUI! VRAM 100% liberada.", flush=True)
                return True
    except Exception as e:
        print(f"⚠️ [VRAM GUARD] Aviso ao liberar VRAM: {e}", flush=True)
    return False

def ensure_comfyui_running():
    try:
        with urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=3) as r:
            if r.status == 200:
                return True
    except Exception:
        pass

    print("🚀 [CineGen] ComfyUI offline. Iniciando servidor headless...", flush=True)
    comfy_bat = BASE_DIR / "scripts" / "start_comfy_headless.bat"
    subprocess.Popen([str(comfy_bat)], shell=True, cwd=str(COMFY_DIR))

    t0 = time.time()
    while time.time() - t0 < 60:
        time.sleep(3)
        try:
            with urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=3) as r:
                if r.status == 200:
                    print(f"✅ [CineGen] ComfyUI pronto em {time.time()-t0:.1f}s!", flush=True)
                    return True
        except Exception:
            pass
    raise TimeoutError("Falha ao iniciar ComfyUI em 60 segundos.")

def wait_for_prompt_completion(prompt_id: str, timeout_sec: int = 900):
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
                        for nid, node_out in outputs.items():
                            if "images" in node_out:
                                for img in node_out["images"]:
                                    fname = img.get("filename")
                                    if fname:
                                        full_path = COMFY_OUTPUT / fname
                                        return full_path
        except Exception:
            pass
        time.sleep(3)
    raise TimeoutError(f"Tempo limite excedido para a tarefa ComfyUI {prompt_id}")

def generate_image_flux(prompt_text: str, negative_text: str = "", seed: int = 45920) -> Path:
    print(f"🎨 [CineGen] Gerando imagem base via FLUX.3 Klein...", flush=True)
    sys.path.insert(0, str(BASE_DIR / "scripts"))
    from generate_tecnico_reference import build_workflow_standalone
    wf = build_workflow_standalone(prompt_text, negative_text or "worst quality, blurry", prefix="CineGen_Auto_Img", seed=seed)
    payload = json.dumps({"prompt": wf}).encode("utf-8")
    req = urllib.request.Request(PROMPT_ENDPOINT, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        prompt_id = res.get("prompt_id")
    
    img_path = wait_for_prompt_completion(prompt_id)
    print(f"✅ [CineGen] Imagem gerada: {img_path}", flush=True)
    free_comfyui_vram()
    return img_path

def generate_video_kandinsky(image_name: str, video_prompt: str, audio_prompt: str, duration_sec: float, seed: int = 64000) -> Path:
    # 3.0s = 73 frames, 4.0s = 97 frames, 5.0s = 121 frames
    if duration_sec <= 3.2:
        length = 73
    elif duration_sec <= 4.2:
        length = 97
    else:
        length = 121

    print(f"🎬 [CineGen] Renderizando vídeo Kandinsky 6.0 Lite ({duration_sec}s / {length} frames)...", flush=True)
    sys.path.insert(0, str(BASE_DIR / "scripts"))
    from run_comfy_kandinsky_3s import build_workflow
    wf = build_workflow(
        image_name=image_name,
        video_prompt=video_prompt,
        audio_prompt=audio_prompt,
        seed=seed,
        length=length,
        prefix="CineGen_Auto_K6"
    )
    payload = json.dumps({"prompt": wf}).encode("utf-8")
    req = urllib.request.Request(PROMPT_ENDPOINT, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        prompt_id = res.get("prompt_id")

    video_path = wait_for_prompt_completion(prompt_id, timeout_sec=900)
    print(f"✅ [CineGen] Vídeo base 480p concluído: {video_path}", flush=True)
    free_comfyui_vram()
    return video_path

def run_upscale_1080p(video_in: Path, video_out: Path):
    print(f"⚡ [CineGen] Executando upscale 2x-NomosUni SPAN para Full HD 1080p...", flush=True)
    sys.path.insert(0, str(BASE_DIR / "scripts"))
    from upscale_video_pipeline import upscale_video_to_1080p
    upscale_video_to_1080p(str(video_in), str(video_out))
    print(f"✅ [CineGen] Vídeo 1080p pronto: {video_out}", flush=True)

def run_dubbing(video_in: Path, dub_config: dict, video_out: Path):
    print(f"🎙️ [CineGen] Iniciando dublagem PT-BR em estúdio local...", flush=True)
    actor_voice = dub_config.get("voz", "narrador")
    ref_audio = dub_config.get("ref_audio")
    if not ref_audio:
        ref_audio = str(VOICES_DIR / f"{actor_voice}.wav")
    
    cmd = [
        sys.executable,
        str(BASE_DIR / "scripts" / "cinegen_dublar_shot.py"),
        "--video_in", str(video_in),
        "--text", dub_config.get("fala", ""),
        "--ref_audio", ref_audio,
        "--emotion", dub_config.get("emocao", "NORMAL"),
        "--temp", str(dub_config.get("temperatura", 0.60)),
        "--start_offset", str(dub_config.get("start_offset", 0.25)),
        "--video_out", str(video_out)
    ]
    subprocess.run(cmd, check=True)

def process_job(job_file: Path):
    print(f"\n=======================================================", flush=True)
    print(f"📥 [AUTO-ENGINE] Nova tarefa detectada: {job_file.name}", flush=True)
    print(f"=======================================================", flush=True)

    proc_file = PROCESSING_DIR / job_file.name
    shutil.move(str(job_file), str(proc_file))

    with open(proc_file, "r", encoding="utf-8") as f:
        job = json.load(f)

    cena_id = job.get("cena_id", f"cena_{int(time.time())}")
    episode = job.get("episode", "experimento_vertice_ep3_oficial")
    duration_sec = float(job.get("duracao_segundos", 3.0))

    ep_dir = BASE_DIR / "projects" / episode
    ep_images = ep_dir / "images"
    ep_videos = ep_dir / "videos"
    ep_images.mkdir(parents=True, exist_ok=True)
    ep_videos.mkdir(parents=True, exist_ok=True)

    ensure_comfyui_running()

    # 1. Tratar Imagem
    img_conf = job.get("imagem", {})
    modo_img = img_conf.get("modo", "existente")
    if modo_img == "gerar":
        p_img = img_conf.get("prompt", "")
        n_img = img_conf.get("negative", "")
        seed_img = int(img_conf.get("seed", 45920))
        raw_img = generate_image_flux(p_img, n_img, seed=seed_img)
        scene_img_name = f"{cena_id}.png"
        target_img = ep_images / scene_img_name
        shutil.copy2(str(raw_img), str(target_img))
        shutil.copy2(str(raw_img), str(COMFY_INPUT / scene_img_name))
    else:
        src_path = img_conf.get("caminho", "")
        if not os.path.isabs(src_path):
            src_path = str(BASE_DIR / src_path)
        scene_img_name = f"{cena_id}_input{Path(src_path).suffix}"
        target_img = COMFY_INPUT / scene_img_name
        shutil.copy2(src_path, str(target_img))

    # 2. Tratar Vídeo
    vid_conf = job.get("video", {})
    raw_video = generate_video_kandinsky(
        image_name=scene_img_name,
        video_prompt=vid_conf.get("prompt_visual", ""),
        audio_prompt=vid_conf.get("prompt_audio", ""),
        duration_sec=duration_sec,
        seed=int(vid_conf.get("seed", 64000))
    )
    base_video_path = ep_videos / f"{cena_id}_base_480p.mp4"
    shutil.copy2(str(raw_video), str(base_video_path))

    # 3. Upscale 1080p
    upscale_enabled = job.get("upscale_1080p", True)
    en_1080p_path = ep_videos / f"{cena_id}_animado_1080p.mp4"
    if upscale_enabled:
        run_upscale_1080p(base_video_path, en_1080p_path)
    else:
        en_1080p_path = base_video_path

    # 4. Dublagem PT-BR
    dub_conf = job.get("dublagem_pt", {})
    pt_1080p_path = ep_videos / f"{cena_id}_dublado_1080p.mp4"
    if dub_conf.get("ativo", False):
        run_dubbing(en_1080p_path, dub_conf, pt_1080p_path)

    # 5. Sincronização MEGA
    if job.get("sincronizar_mega", True) and MEGA_DIR.exists():
        print(f"☁️ [CineGen] Sincronizando com MEGAsync para celular...", flush=True)
        if en_1080p_path.exists():
            shutil.copy2(str(en_1080p_path), str(MEGA_DIR / en_1080p_path.name))
        if pt_1080p_path.exists():
            shutil.copy2(str(pt_1080p_path), str(MEGA_DIR / pt_1080p_path.name))
        print("📲 [CineGen] Arquivos disponíveis no MEGAsync!", flush=True)

    # 6. Finalização
    job["status"] = "CONCLUIDO"
    job["finalizado_em"] = time.strftime("%Y-%m-%d %H:%M:%S")
    job["arquivos_gerados"] = {
        "imagem": str(target_img),
        "video_base": str(base_video_path),
        "video_en_1080p": str(en_1080p_path),
        "video_pt_1080p": str(pt_1080p_path) if dub_conf.get("ativo", False) else None
    }
    
    done_file = COMPLETED_DIR / f"{cena_id}_done.json"
    with open(done_file, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2, ensure_ascii=False)
    
    if proc_file.exists():
        proc_file.unlink()

    print(f"🎉 [AUTO-ENGINE] Cena {cena_id} produzida e entregue com sucesso!", flush=True)

def main_loop():
    ensure_dirs()
    print("=======================================================", flush=True)
    print("🎬 CINEGEN AUTO-ENGINE (AUTO-PILOT PIPELINE)", flush=True)
    print(f"👀 Monitorando pasta: {INBOX_DIR}", flush=True)
    print("⚡ Modo: Zero intervenção manual (Auto VRAM release)", flush=True)
    print("Pressione Ctrl+C para encerrar.", flush=True)
    print("=======================================================", flush=True)

    while True:
        try:
            pending = list(INBOX_DIR.glob("*.json"))
            if pending:
                for job_path in pending:
                    try:
                        process_job(job_path)
                    except Exception as err:
                        print(f"❌ [ERRO CRÍTICO] Falha ao processar {job_path.name}: {err}", flush=True)
                        traceback.print_exc()
                        failed_path = FAILED_DIR / job_path.name
                        if job_path.exists():
                            shutil.move(str(job_path), str(failed_path))
            time.sleep(3)
        except KeyboardInterrupt:
            print("\n🛑 Encerrando CineGen Auto-Engine...", flush=True)
            break
        except Exception as e:
            print(f"⚠️ Erro no loop de monitoramento: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    main_loop()
