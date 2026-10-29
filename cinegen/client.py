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

import json
import time
import urllib.request
import urllib.error
from pathlib import Path

COMFY_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = Path(r"C:\CineGen\comfyui\output")

class ComfyClient:
    def __init__(self, base_url: str = COMFY_URL):
        self.base_url = base_url

    def is_alive(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base_url}/system_stats", timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def queue_prompt(self, workflow: dict) -> str:
        payload = json.dumps({"prompt": workflow}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/prompt",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["prompt_id"]

    def wait_for_completion(self, prompt_id: str, poll_interval: float = 2.0, timeout: float = 600.0) -> list[Path]:
        start = time.time()
        while time.time() - start < timeout:
            time.sleep(poll_interval)
            try:
                with urllib.request.urlopen(f"{self.base_url}/history/{prompt_id}", timeout=5) as resp:
                    history = json.loads(resp.read().decode("utf-8"))
                    if prompt_id in history:
                        status = history[prompt_id].get("status", {})
                        if status.get("completed", False):
                            outputs = history[prompt_id].get("outputs", {})
                            saved_files = []
                            for _, out in outputs.items():
                                if "images" in out:
                                    for img in out["images"]:
                                        filename = img.get("filename")
                                        if filename:
                                            saved_files.append(OUTPUT_DIR / filename)
                            return saved_files
            except Exception:
                pass
        raise TimeoutError(f"A execução do prompt {prompt_id} excedeu {timeout} segundos.")
