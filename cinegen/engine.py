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

import time
from pathlib import Path
from dataclasses import dataclass

from .preprocessor import preprocess_reference
from .prompt_builder import build_solo_prompt, build_couple_prompt
from .workflow_builder import build_flux_workflow
from .client import ComfyClient

@dataclass
class GenerationResult:
    output_path: Path
    elapsed_seconds: float
    seed: int
    steps: int
    prompt: str

class CineGenEngine:
    def __init__(self, comfy_url: str = "http://127.0.0.1:8188"):
        self.client = ComfyClient(comfy_url)

    def check_health(self) -> bool:
        return self.client.is_alive()

    def generate_solo(
        self,
        image_path: str | Path,
        scenario: str,
        hair_style: str | None = None,
        seed: int = 941,
        steps: int = 8,
        output_prefix: str = "CineGen_Solo"
    ) -> GenerationResult:
        """
        Gera uma cena com um único personagem mantendo fidelidade estrita.
        """
        if not self.check_health():
            raise RuntimeError("ComfyUI não está acessível em 127.0.0.1:8188. Inicie o servidor primeiro.")

        ref_filename = preprocess_reference(image_path)
        prompt = build_solo_prompt(scenario, hair_style=hair_style)
        workflow = build_flux_workflow(
            prompt_text=prompt,
            reference_images=[ref_filename],
            output_prefix=output_prefix,
            seed=seed,
            steps=steps
        )

        t0 = time.time()
        prompt_id = self.client.queue_prompt(workflow)
        outputs = self.client.wait_for_completion(prompt_id)
        elapsed = round(time.time() - t0, 2)

        if not outputs:
            raise RuntimeError(f"Nenhum arquivo de imagem retornado para o prompt {prompt_id}.")

        return GenerationResult(
            output_path=outputs[0],
            elapsed_seconds=elapsed,
            seed=seed,
            steps=steps,
            prompt=prompt
        )

    def generate_couple(
        self,
        left_image_path: str | Path,
        right_image_path: str | Path,
        scenario: str,
        right_hair: str | None = None,
        seed: int = 941,
        steps: int = 8,
        output_prefix: str = "CineGen_Casal"
    ) -> GenerationResult:
        """
        Gera uma cena de casal com ancoragem espacial (esquerda/direita) e multi-referência.
        """
        if not self.check_health():
            raise RuntimeError("ComfyUI não está acessível em 127.0.0.1:8188. Inicie o servidor primeiro.")

        left_ref = preprocess_reference(left_image_path, output_name="ref_left_actor.png")
        right_ref = preprocess_reference(right_image_path, output_name="ref_right_actor.png")

        prompt = build_couple_prompt(scenario, right_hair=right_hair)
        workflow = build_flux_workflow(
            prompt_text=prompt,
            reference_images=[left_ref, right_ref],
            output_prefix=output_prefix,
            seed=seed,
            steps=steps
        )

        t0 = time.time()
        prompt_id = self.client.queue_prompt(workflow)
        outputs = self.client.wait_for_completion(prompt_id)
        elapsed = round(time.time() - t0, 2)

        if not outputs:
            raise RuntimeError(f"Nenhum arquivo de imagem retornado para o prompt {prompt_id}.")

        return GenerationResult(
            output_path=outputs[0],
            elapsed_seconds=elapsed,
            seed=seed,
            steps=steps,
            prompt=prompt
        )
