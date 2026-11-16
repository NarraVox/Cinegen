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
CineGen Production Orchestrator
Gerenciamento de ponta a ponta do pipeline cinematográfico:
1. Planejamento em 3 etapas com Qwen 3.5 (Narrativa, Visual/FLUX, Movimento/Kandinsky)
2. Descarregamento de VRAM
3. Geração de Imagens FLUX.3 Klein com Reuso Inteligente (sem duplicidade)
4. Animação de Planos com Kandinsky 6.0 Lite (5 passos PiFlow, Tile 256)
5. Upscale 2x SPAN para Full HD 1080p (~11s por plano)
6. Montagem Final FFmpeg do Episódio Completo
7. Checkpointing e Retomada sem perda de trabalho
"""

import os
import sys
import time
import json
import shutil
import base64
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

# stdout UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from .planner import CineGenPlanner, DEFAULT_QWEN_4B, DEFAULT_QWEN_9B
from .engine import CineGenEngine
from .preprocessor import preprocess_reference

COMFY_INPUT_DIR = r"C:\CineGen\comfyui\input"
COMFY_OUTPUT_DIR = r"C:\CineGen\comfyui\output"
PROJECTS_ROOT = r"C:\CineGen\projects"

class ProductionOrchestrator:
    def __init__(
        self,
        projects_dir: str = PROJECTS_ROOT,
        status_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.projects_dir = projects_dir
        self.status_callback = status_callback
        self.current_job: Optional[Dict[str, Any]] = None
        self.is_running = False
        os.makedirs(projects_dir, exist_ok=True)
        os.makedirs(COMFY_INPUT_DIR, exist_ok=True)
        os.makedirs(COMFY_OUTPUT_DIR, exist_ok=True)

    def _update_status(self, stage: str, progress: float, message: str, scenes: Optional[List[Dict[str, Any]]] = None):
        if not self.current_job:
            return
        self.current_job["current_stage"] = stage
        self.current_job["progress"] = round(progress, 1)
        self.current_job["status_message"] = message
        self.current_job["updated_at"] = time.time()
        if scenes is not None:
            self.current_job["scenes"] = scenes

        # Salva checkpoint no disco
        job_file = os.path.join(self.current_job["job_dir"], "job_status.json")
        try:
            with open(job_file, "w", encoding="utf-8") as f:
                json.dump(self.current_job, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Erro ao salvar checkpoint: {e}", flush=True)

        print(f"[{progress:.1f}%] [{stage}] {message}", flush=True)
        if self.status_callback:
            self.status_callback(self.current_job)

    def ensure_comfy_running(self, timeout_sec: int = 45) -> bool:
        """Garante que o ComfyUI esteja ativo e pronto na porta 8188."""
        url = "http://127.0.0.1:8188/system_stats"
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass

        print("🚀 [ORCHESTRATOR] Iniciando ComfyUI em modo background...", flush=True)
        comfy_bat = r"C:\CineGen\scripts\start_comfy_headless.bat"
        if os.path.exists(comfy_bat):
            subprocess.Popen([comfy_bat], shell=True, cwd=r"C:\CineGen\comfyui")
        else:
            comfy_python = r"C:\CineGen\comfyui\.venv\Scripts\python.exe"
            subprocess.Popen(
                [comfy_python, "main.py", "--listen", "127.0.0.1", "--port", "8188", "--disable-auto-launch", "--lowvram", "--enable-dynamic-vram", "--cuda-malloc"],
                cwd=r"C:\CineGen\comfyui"
            )

        start_t = time.time()
        while time.time() - start_t < timeout_sec:
            time.sleep(3)
            try:
                with urllib.request.urlopen(url, timeout=2) as resp:
                    if resp.status == 200:
                        print("✅ [ORCHESTRATOR] Servidor ComfyUI conectado com sucesso!", flush=True)
                        return True
            except Exception:
                pass
        raise TimeoutError("Falha ao inicializar o servidor ComfyUI na porta 8188.")

    def save_character_references(self, actors: List[Dict[str, Any]], job_refs_dir: str) -> List[Dict[str, Any]]:
        """Salva as referências visuais decodificadas de Base64 para PNGs estáveis."""
        os.makedirs(job_refs_dir, exist_ok=True)
        saved_actors = []

        for idx, act in enumerate(actors):
            name = act.get("name", f"Actor_{idx+1}").strip()
            safe_name = "".join(c for c in name if c.isalnum() or c in "_-").lower()
            ref_path = act.get("ref_path")
            base64_img = act.get("image")

            target_filename = f"ref_{safe_name}.png"
            dest_job_path = os.path.join(job_refs_dir, target_filename)
            dest_comfy_path = os.path.join(COMFY_INPUT_DIR, target_filename)

            if base64_img and "base64," in base64_img:
                header, encoded = base64_img.split("base64,", 1)
                img_data = base64.b64decode(encoded)
                with open(dest_job_path, "wb") as f:
                    f.write(img_data)
                # Copia para input do ComfyUI
                shutil.copy2(dest_job_path, dest_comfy_path)
                final_ref = dest_comfy_path
            elif ref_path and os.path.exists(ref_path):
                shutil.copy2(ref_path, dest_job_path)
                shutil.copy2(ref_path, dest_comfy_path)
                final_ref = dest_comfy_path
            else:
                # Se não enviou imagem nova, verifica se já existe uma referência com este nome no input do ComfyUI
                default_existing = os.path.join(COMFY_INPUT_DIR, f"ref_{safe_name}.png")
                if os.path.exists(default_existing):
                    final_ref = default_existing
                else:
                    final_ref = None

            saved_actors.append({
                "name": name,
                "gender": act.get("gender", "Feminino"),
                "ref_path": final_ref,
                "ref_filename": target_filename if final_ref else None
            })

        return saved_actors

    def start_production(
        self,
        script_text: str,
        actors: List[Dict[str, Any]],
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executa todo o pipeline automatizado do início ao fim.
        """
        if self.is_running:
            raise RuntimeError("Já existe uma produção em andamento. Aguarde ou reinicie.")

        self.is_running = True
        job_id = job_id or f"proj_{time.strftime('%Y%m%d_%H%M%S')}"
        job_dir = os.path.join(self.projects_dir, job_id)
        os.makedirs(job_dir, exist_ok=True)
        images_dir = os.path.join(job_dir, "images")
        videos_dir = os.path.join(job_dir, "videos")
        refs_dir = os.path.join(job_dir, "refs")
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(videos_dir, exist_ok=True)

        self.current_job = {
            "job_id": job_id,
            "title": f"Produção {job_id}",
            "job_dir": job_dir,
            "created_at": time.time(),
            "updated_at": time.time(),
            "current_stage": "iniciando",
            "progress": 0.0,
            "status_message": "Inicializando pipeline automatizado CineGen...",
            "script": script_text,
            "actors": actors,
            "scenes": [],
            "completed": False,
            "error": None
        }
        self._update_status("iniciando", 2.0, "Preparando projeto e referências de elenco...")

        try:
            # 1. Salva referências do elenco
            saved_actors = self.save_character_references(actors, refs_dir)
            self.current_job["actors"] = saved_actors

            # 2. Executa planejamento em 3 etapas com Qwen 3.5
            self._update_status("planejamento_qwen", 5.0, "🧠 Carregando Qwen 3.5 para planejamento cinematográfico...")
            planner = CineGenPlanner()
            
            plan_file = os.path.join(job_dir, "cinegen_plan.json")
            if os.path.exists(plan_file):
                print(f"📖 [ORCHESTRATOR] Encontrado plano pré-existente em {plan_file}, reaproveitando...", flush=True)
                with open(plan_file, "r", encoding="utf-8") as pf:
                    project_plan = json.load(pf)
            else:
                self._update_status("planejamento_qwen", 10.0, "🧠 Qwen 3.5: Analisando roteiro, visuais e animação...")
                project_plan = planner.plan_full_project(script_text, saved_actors, project_dir=job_dir)

            shots: List[Dict[str, Any]] = project_plan.get("shots", [])
            total_shots = len(shots)
            unique_image_ids = list(dict.fromkeys(s["image_id"] for s in shots))
            total_unique_images = len(unique_image_ids)

            # Inicializa a lista de cenas no job status
            scenes_status = []
            for s in shots:
                scenes_status.append({
                    "id": s["shot_id"],
                    "name": f"Plano {s['shot_id']} ({', '.join(s.get('characters', []))})",
                    "dialogue": s.get("dialogue", ""),
                    "image_id": s.get("image_id"),
                    "is_reused": s.get("is_image_reused", False),
                    "status": "Planejado",
                    "image_ready": False,
                    "video_ready": False,
                    "active": False
                })
            self.current_job["scenes"] = scenes_status

            self._update_status(
                "planejamento_concluido",
                20.0,
                f"✅ Planejamento concluído: {total_shots} planos | {total_unique_images} imagens únicas necessárias.",
                scenes=scenes_status
            )

            # 3. Garante ComfyUI ativo para renderização
            self._update_status("preparando_comfyui", 22.0, "Conectando ao ComfyUI para geração visual...")
            self.ensure_comfy_running()

            # 4. Fase de Geração de Imagens FLUX.3 (com Reuso Inteligente)
            self._update_status("gerando_imagens", 25.0, f"🎨 Geração FLUX.3 Klein: 0/{total_unique_images} imagens concluídas.")
            engine = CineGenEngine()

            # Mapa para armazenar o caminho real de cada image_id
            rendered_images: Dict[str, str] = {}

            # Agrupa planos por image_id
            for img_idx, img_id in enumerate(unique_image_ids):
                # Encontra o primeiro plano que define esta imagem
                representative_shot = next(s for s in shots if s["image_id"] == img_id)
                img_out_path = os.path.join(images_dir, f"{img_id}.png")
                comfy_in_copy = os.path.join(COMFY_INPUT_DIR, f"{job_id}_{img_id}.png")

                # Marca cenas correspondentes como ativas
                for sc in scenes_status:
                    if sc["image_id"] == img_id:
                        sc["active"] = True
                        sc["status"] = "Gerando Imagem..."

                calc_prog = 25.0 + (35.0 * (img_idx / max(total_unique_images, 1)))
                self._update_status(
                    "gerando_imagens",
                    calc_prog,
                    f"🎨 FLUX.3 Klein: Gerando imagem cinematográfica {img_idx+1}/{total_unique_images} ({img_id})...",
                    scenes=scenes_status
                )

                if os.path.exists(img_out_path):
                    print(f"⏩ [FLUX.3] Imagem {img_id} já existe em disco, reaproveitando!", flush=True)
                else:
                    is_couple = representative_shot.get("is_couple", False)
                    chars = representative_shot.get("characters", [])
                    refs = representative_shot.get("ref_bindings", [])

                    if is_couple and len(refs) >= 2:
                        # Geração de Casal com Ancoragem Espacial Esquerda / Direita
                        left_ref = refs[0]["ref_path"]
                        right_ref = refs[1]["ref_path"]
                        res = engine.generate_couple(
                            left_image_path=left_ref,
                            right_image_path=right_ref,
                            scenario=representative_shot.get("flux_prompt", "cinematic photo"),
                            seed=941 + img_idx,
                            steps=8,
                            output_prefix=f"{job_id}_{img_id}"
                        )
                        shutil.copy2(res.output_path, img_out_path)
                    else:
                        # Geração Solo com Referência Estrita
                        actor_ref = refs[0]["ref_path"] if refs else (saved_actors[0]["ref_path"] if saved_actors else None)
                        if not actor_ref or not os.path.exists(actor_ref):
                            # Fallback para referência padrão
                            actor_ref = os.path.join(COMFY_INPUT_DIR, "ref_actor_default.png")

                        res = engine.generate_solo(
                            image_path=actor_ref,
                            scenario=representative_shot.get("flux_prompt", "cinematic photo"),
                            seed=941 + img_idx,
                            steps=8,
                            output_prefix=f"{job_id}_{img_id}"
                        )
                        shutil.copy2(res.output_path, img_out_path)

                # Salva cópia na pasta input do ComfyUI para uso imediato pelo Kandinsky
                shutil.copy2(img_out_path, comfy_in_copy)
                rendered_images[img_id] = f"{job_id}_{img_id}.png"

                # Atualiza cenas que usam essa imagem
                for sc in scenes_status:
                    if sc["image_id"] == img_id:
                        sc["active"] = False
                        sc["image_ready"] = True
                        sc["status"] = "Imagem Pronta"

            self._update_status(
                "imagens_concluidas",
                60.0,
                f"✅ Todas as {total_unique_images} imagens foram renderizadas com fidelidade real!",
                scenes=scenes_status
            )

            # 5. Fase de Animação de Planos (Kandinsky 6.0 Lite) & Upscale (2x-NomosUni SPAN)
            from scripts.cinegen_video_master import queue_kandinsky_generation, wait_for_completion, run_upscale

            shot_video_paths = []
            for s_idx, shot in enumerate(shots):
                s_id = shot["shot_id"]
                img_id = shot["image_id"]
                comfy_img_name = rendered_images.get(img_id, f"{job_id}_{img_id}.png")
                
                final_shot_1080p = os.path.join(videos_dir, f"{s_id}_1080p.mp4")

                # Atualiza status do plano na UI
                for sc in scenes_status:
                    if sc["id"] == s_id:
                        sc["active"] = True
                        sc["status"] = "Animando Vídeo (Kandinsky 6.0)..."

                calc_prog = 60.0 + (30.0 * (s_idx / max(total_shots, 1)))
                self._update_status(
                    "animando_planos",
                    calc_prog,
                    f"🎥 Kandinsky 6.0: Animando plano {s_idx+1}/{total_shots} ({s_id})...",
                    scenes=scenes_status
                )

                if os.path.exists(final_shot_1080p):
                    print(f"⏩ [KANDINSKY] Vídeo 1080p do plano {s_id} já existe, reaproveitando!", flush=True)
                else:
                    # Animação no Kandinsky 6.0 Lite
                    v_prompt = shot.get("video_prompt", "subtle cinematic head movement and natural breathing")
                    a_prompt = shot.get("audio_prompt", "natural ambient soft breeze, clean foley, no music")
                    prefix = f"{job_id}_{s_id}_k6"

                    prompt_id = queue_kandinsky_generation(
                        image_name=comfy_img_name,
                        video_prompt=v_prompt,
                        audio_prompt=a_prompt,
                        prefix=prefix,
                        seed=64000 + s_idx
                    )
                    raw_video_path = wait_for_completion(prompt_id, timeout_sec=900)

                    # Upscale ultrarrápido 2x-NomosUni SPAN para Full HD 1080p (~11s)
                    self._update_status(
                        "upscale_1080p",
                        calc_prog + 1.0,
                        f"⚡ 2x SPAN: Upscaling plano {s_idx+1}/{total_shots} para Full HD 1080p...",
                        scenes=scenes_status
                    )
                    run_upscale(raw_video_path, output_path=final_shot_1080p)

                shot_video_paths.append(final_shot_1080p)

                # Marca plano como pronto
                for sc in scenes_status:
                    if sc["id"] == s_id:
                        sc["active"] = False
                        sc["video_ready"] = True
                        sc["status"] = "Plano 1080p Concluído"

            # 6. Montagem Final (Concatenação FFmpeg do Episódio Completo)
            self._update_status("montagem_final", 92.0, "🎬 Montando episódio final em Full HD 1080p com FFmpeg...", scenes=scenes_status)
            final_episode_path = os.path.join(job_dir, f"{job_id}_episodio_completo_1080p.mp4")
            
            self._assemble_final_video(shot_video_paths, final_episode_path)

            # Gera relatório de produção em Markdown
            self._generate_production_report(job_dir, project_plan, shot_video_paths, final_episode_path)

            self.current_job["final_video"] = final_episode_path
            self.current_job["completed"] = True
            self._update_status("concluido", 100.0, f"🎉 Produção Cinematográfica Completa! Episódio pronto em: {os.path.basename(final_episode_path)}", scenes=scenes_status)

            return self.current_job

        except Exception as e:
            err_msg = f"Erro no processo de produção: {str(e)}"
            print(f"❌ [ORCHESTRATOR] {err_msg}", flush=True)
            if self.current_job:
                self.current_job["error"] = err_msg
                self._update_status("erro", self.current_job.get("progress", 0.0), f"❌ {err_msg}")
            raise e
        finally:
            self.is_running = False

    def _assemble_final_video(self, shot_paths: List[str], output_path: str):
        """Concatena os planos em um único vídeo contínuo em 1080p via FFmpeg."""
        if not shot_paths:
            return
        if len(shot_paths) == 1:
            shutil.copy2(shot_paths[0], output_path)
            return

        concat_list_file = os.path.join(os.path.dirname(output_path), "concat_shots.txt")
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for sp in shot_paths:
                f.write(f"file '{sp.replace(os.sep, '/')}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_file,
            "-c:v", "copy",
            "-c:a", "copy",
            output_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"⚠️ Aviso no concat direto (-c copy), tentando re-encode unificado: {res.stderr[:200]}", flush=True)
            cmd_reencode = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list_file,
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k",
                output_path
            ]
            subprocess.run(cmd_reencode, check=True)
        print(f"🎬 [MONTAGEM] Episódio completo montado com sucesso: {output_path}", flush=True)

    def _generate_production_report(self, job_dir: str, plan: Dict[str, Any], shots: List[str], final_video: str):
        report_path = os.path.join(job_dir, "production_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Relatório de Produção CineGen\n\n")
            f.write(f"- **Data:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Total de Planos:** {len(plan.get('shots', []))}\n")
            f.write(f"- **Imagens Únicas Geradas:** {plan.get('unique_images_needed', 0)}\n")
            f.write(f"- **Vídeo Final:** `{final_video}`\n\n")
            f.write(f"## Detalhamento dos Planos\n\n")
            f.write(f"| Plano | Personagens | Fala | Imagem ID | Reusada? | Duração |\n")
            f.write(f"|---|---|---|---|---|---|\n")
            for s in plan.get("shots", []):
                reused_str = "Sim" if s.get("is_image_reused") else "Não"
                f.write(f"| {s['shot_id']} | {', '.join(s.get('characters', []))} | {s.get('dialogue', '')} | {s.get('image_id')} | {reused_str} | {s.get('duration_seconds')}s |\n")
