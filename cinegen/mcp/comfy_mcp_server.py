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
ComfyUI MCP Server para CineGen
Permite aos agentes controlar o ComfyUI de forma programática e headless.
"""

import json
import urllib.request
import urllib.error
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("ComfyUI-CineGen")
BASE_URL = "http://127.0.0.1:8188"


def _api_get(endpoint: str):
    try:
        url = f"{BASE_URL}/{endpoint}"
        req = urllib.request.Request(url, headers={"User-Agent": "CineGen-MCP"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e), "status": "offline"}


def _api_post(endpoint: str, data: dict):
    try:
        url = f"{BASE_URL}/{endpoint}"
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "User-Agent": "CineGen-MCP"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def comfy_system_status() -> str:
    """Verifica se o ComfyUI esta online, relata VRAM da GPU, status da fila e versao do sistema."""
    data = _api_get("system_stats")
    if "error" in data:
        return f"ComfyUI está OFFLINE ou inacessível em {BASE_URL}. Erro: {data['error']}"
    
    devs = data.get("devices", [])
    gpu_info = "Nenhuma GPU detectada"
    if devs:
        d = devs[0]
        name = d.get("name", "Desconhecido")
        total_vram = d.get("total_vram", 0) / (1024**3)
        free_vram = d.get("free_vram", 0) / (1024**3)
        gpu_info = f"{name} (VRAM Livre: {free_vram:.2f} GB / Total: {total_vram:.2f} GB)"

    queue = _api_get("queue")
    q_running = len(queue.get("queue_running", []))
    q_pending = len(queue.get("queue_pending", []))

    return json.dumps({
        "status": "ONLINE",
        "gpu": gpu_info,
        "queue_running": q_running,
        "queue_pending": q_pending,
        "comfyui_version": data.get("system", {}).get("comfyui_version", "desconhecida")
    }, indent=2)


@mcp.tool()
def comfy_list_models() -> str:
    """Lista todos os modelos detectados pelo ComfyUI (Diffusion GGUF, VAE, CLIP)."""
    obj_info = _api_get("object_info")
    if "error" in obj_info:
        return f"Erro ao consultar modelos: {obj_info['error']}"
    
    models = {}
    if "UnetLoaderGGUF" in obj_info:
        models["diffusion_models_gguf"] = obj_info["UnetLoaderGGUF"]["input"]["required"]["unet_name"][0]
    if "CLIPLoaderGGUF" in obj_info:
        models["clip_models_gguf"] = obj_info["CLIPLoaderGGUF"]["input"]["required"]["clip_name"][0]
    if "VAELoader" in obj_info:
        models["vae_models"] = obj_info["VAELoader"]["input"]["required"]["vae_name"][0]
        
    return json.dumps(models, indent=2)


@mcp.tool()
def comfy_queue_workflow(workflow_json_path: str) -> str:
    """Envia um arquivo de workflow JSON para a fila do ComfyUI e retorna o prompt_id."""
    try:
        with open(workflow_json_path, "r", encoding="utf-8") as f:
            flow_data = json.load(f)
    except Exception as e:
        return f"Erro ao ler workflow JSON: {e}"

    res = _api_post("prompt", {"prompt": flow_data})
    return json.dumps(res, indent=2)


@mcp.tool()
def comfy_get_history(prompt_id: str) -> str:
    """Consulta o resultado de uma tarefa de renderizacao pelo prompt_id."""
    data = _api_get(f"history/{prompt_id}")
    return json.dumps(data, indent=2)


@mcp.tool()
def comfy_interrupt() -> str:
    """Interrompe a execucao atual imediatamente."""
    res = _api_post("interrupt", {})
    return json.dumps(res, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
