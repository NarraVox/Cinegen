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
CineGen Web Server & REST API
Serve a interface UI (HTML/CSS/JS) e orquestra a produção cinematográfica em segundo plano.
"""

import os
import sys
import json
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from .orchestrator import ProductionOrchestrator, PROJECTS_ROOT

BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"

app = FastAPI(title="CineGen AI Cinema Studio", version="2026.DIRECTOR")

# Habilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = ProductionOrchestrator()
active_production_thread: Optional[threading.Thread] = None

# Modelos Pydantic para requisições
class ActorModel(BaseModel):
    name: str
    gender: Optional[str] = "Feminino"
    image: Optional[str] = None
    ref_path: Optional[str] = None

class StartCineRequest(BaseModel):
    script: str
    actors: List[ActorModel]

class ResumeProjectRequest(BaseModel):
    job_id: str

@app.get("/")
def get_index():
    index_file = UI_DIR / "index.html"
    return FileResponse(index_file)

@app.get("/api/cine/status")
def get_system_status():
    import torch
    gpu_info = {
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None",
        "vram_total_mb": round(torch.cuda.get_device_properties(0).total_memory / (1024**2)) if torch.cuda.is_available() else 0,
        "vram_used_mb": round(torch.cuda.memory_allocated(0) / (1024**2)) if torch.cuda.is_available() else 0,
    }
    return {
        "success": True,
        "gpu": gpu_info,
        "is_running": orchestrator.is_running
    }

@app.get("/api/cine/projects")
def list_saved_projects():
    projects = []
    if os.path.exists(PROJECTS_ROOT):
        for entry in sorted(os.listdir(PROJECTS_ROOT), reverse=True):
            entry_path = os.path.join(PROJECTS_ROOT, entry)
            if os.path.isdir(entry_path):
                status_file = os.path.join(entry_path, "job_status.json")
                if os.path.exists(status_file):
                    try:
                        with open(status_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            projects.append({
                                "job_id": data.get("job_id", entry),
                                "title": data.get("title", entry),
                                "progress": data.get("progress", 0.0),
                                "current_stage": data.get("current_stage", "pronto"),
                                "created_at": data.get("created_at"),
                                "completed": data.get("completed", False)
                            })
                    except Exception:
                        pass
    return {"success": True, "projects": projects}

@app.post("/api/start-cine")
def start_cine(req: StartCineRequest, background_tasks: BackgroundTasks):
    global active_production_thread
    if orchestrator.is_running:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Já existe uma produção ativa em andamento."}
        )

    actors_dicts = [a.dict() for a in req.actors]
    
    def run_worker():
        try:
            orchestrator.start_production(req.script, actors_dicts)
        except Exception as e:
            print(f"❌ Erro na thread de produção: {e}", flush=True)

    active_production_thread = threading.Thread(target=run_worker, daemon=True)
    active_production_thread.start()

    return {
        "success": True,
        "message": "Produção audiovisual iniciada com sucesso!",
        "job_id": orchestrator.current_job.get("job_id") if orchestrator.current_job else "starting"
    }

@app.post("/api/cine/resume-project")
def resume_project(req: ResumeProjectRequest):
    global active_production_thread
    if orchestrator.is_running:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Já existe uma produção ativa em andamento."}
        )

    project_dir = os.path.join(PROJECTS_ROOT, req.job_id)
    status_file = os.path.join(project_dir, "job_status.json")
    if not os.path.exists(status_file):
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")

    with open(status_file, "r", encoding="utf-8") as f:
        job_data = json.load(f)

    script_text = job_data.get("script", "")
    actors = job_data.get("actors", [])

    def run_worker():
        try:
            orchestrator.start_production(script_text, actors, job_id=req.job_id)
        except Exception as e:
            print(f"❌ Erro na retomada: {e}", flush=True)

    active_production_thread = threading.Thread(target=run_worker, daemon=True)
    active_production_thread.start()

    return {"success": True, "message": f"Retomando projeto {req.job_id}..."}

@app.get("/api/get-scenes")
def get_scenes_status():
    if not orchestrator.current_job:
        return {
            "progress": 0,
            "status": "Pronto para gravar",
            "scenes": [],
            "current_stage": "idle"
        }

    job = orchestrator.current_job
    return {
        "progress": job.get("progress", 0.0),
        "status": job.get("status_message", "Processando..."),
        "current_stage": job.get("current_stage", "iniciando"),
        "scenes": job.get("scenes", []),
        "completed": job.get("completed", False),
        "final_video": job.get("final_video"),
        "error": job.get("error")
    }

# Monta arquivos estáticos da UI
app.mount("/css", StaticFiles(directory=str(UI_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(UI_DIR / "js")), name="js")
if os.path.exists(PROJECTS_ROOT):
    app.mount("/projects", StaticFiles(directory=PROJECTS_ROOT), name="projects")

def run_server(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    print(f"🎬 [CINEGEN SERVER] Iniciando servidor web em http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    run_server()
