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
Módulo Oficial de Construção de Prompts do CineGen
Segue as diretrizes validadas do FLUX.3, comunidade Reddit e modelos LLM 4B:
- Prompts curtos e compactos (limite estrito de 40 a 60 palavras)
- Instrução ultra-curta para o Qwen 4B (menos de 10 linhas)
- Linguagem fotográfica natural (35mm / 85mm portrait)
- Zero sopa de tags (sem '8k', 'photorealistic', 'masterpiece')
- Sem rótulos genéricos de gênero ('man/woman')
- Ancoragem espacial precisa para multi-referências
"""

MAX_RECOMMENDED_WORDS = 65

def validate_prompt(prompt: str) -> str:
    """Verifica e avisa caso o prompt ultrapasse o tamanho seguro."""
    words = prompt.strip().split()
    if len(words) > MAX_RECOMMENDED_WORDS:
        print(f"[CineGen Alerta] Prompt com {len(words)} palavras. O ideal é manter abaixo de {MAX_RECOMMENDED_WORDS} para evitar diluição de atenção visual.")
    return prompt

def build_solo_prompt(
    scenario: str,
    hair_style: str | None = None,
    mood: str = "warm gentle smile"
) -> str:
    """Gera um prompt solo compacto (aprox. 35-42 palavras)."""
    hair = f", with {hair_style}" if hair_style else ""
    prompt = (
        f"A candid 35mm photograph of <ref_image_0>, keeping authentic face and {mood} "
        f"faithful to <ref_image_0>{hair}. "
        f"Standing in {scenario}, warm golden hour light, natural skin texture, soft bokeh."
    )
    return validate_prompt(prompt)

def build_couple_prompt(
    scenario: str,
    right_hair: str | None = None,
    mood: str = "joyful smiles"
) -> str:
    """Gera um prompt de casal compacto com ancoragem espacial (aprox. 45-52 palavras)."""
    hair = f", with {right_hair}" if right_hair else ""
    prompt = (
        "A candid 35mm film photograph of a loving couple embracing warmly. "
        "The person from <ref_image_0> on the left has authentic facial features and friendly smile. "
        f"The person from <ref_image_1> on the right has authentic face{hair}, "
        f"resting head affectionately on shoulder in a warm hug, both sharing {mood}. "
        f"In {scenario}, soft twilight lighting, natural skin texture, beautiful bokeh."
    )
    return validate_prompt(prompt)

def get_qwen_system_prompt() -> str:
    """Retorna a instrução ultra-curta (pocket) para o Qwen 4B."""
    return (
        "Você é o gerador de prompts CineGen para o modelo FLUX.3.\n"
        "Converta a cena em um prompt em inglês de 40 a 50 palavras seguindo:\n"
        "1. Use apenas <ref_image_0> (esquerda) e <ref_image_1> (direita).\n"
        "2. NUNCA use 'man', 'woman', '8k', 'photorealistic', 'masterpiece'.\n"
        "3. Descreva o abraço (cabeça no ombro, braços ao redor) e estilo 'candid 35mm film'.\n\n"
        "Exemplo:\n"
        "\"A candid 35mm film photograph of a loving couple embracing warmly. "
        "The person from <ref_image_0> on the left has authentic face and smile. "
        "The person from <ref_image_1> on the right has authentic face, resting head gently on shoulder in a warm hug, "
        "sharing joyful smiles. In amusement park at dusk, soft twilight lighting, natural skin texture, beautiful bokeh.\"\n\n"
        "Retorne APENAS o prompt final em inglês."
    )
