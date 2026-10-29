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
CineGen - Sistema Autônomo de Geração de Imagens e Vídeo Cinematográfico
"""

from .engine import CineGenEngine, GenerationResult
from .preprocessor import preprocess_reference
from .prompt_builder import build_solo_prompt, build_couple_prompt
from .workflow_builder import build_flux_workflow

__all__ = [
    "CineGenEngine",
    "GenerationResult",
    "preprocess_reference",
    "build_solo_prompt",
    "build_couple_prompt",
    "build_flux_workflow",
]
