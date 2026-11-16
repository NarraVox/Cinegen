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
CineGen Script Planner - Três Etapas Sequenciais com Qwen 3.5
Suporte a Roteiros Descritivos em Prosa com Criação Automática de Falas.
Processamento inteligente por cenas/blocos dramáticos para roteiros longos.
"""

import os
import sys
import gc
import json
import re
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

# Suporte a stdout UTF-8 no Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

DEFAULT_QWEN_9B = r"C:\IA_dublagem\MODELS\Qwen3.5-9B-Q3_K_M.gguf"
DEFAULT_QWEN_4B = r"C:\IA_dublagem\MODELS\Qwen3.5-4B-Q4_K_M.gguf"

def clean_llm_json_response(raw_text: str) -> Any:
    text = raw_text.strip()
    
    if '</think>' in text:
        text = text.split('</think>', 1)[1].strip()
    elif '<think>' in text:
        idx_bracket = text.find('[')
        idx_brace = text.find('{')
        indices = [i for i in [idx_bracket, idx_brace] if i != -1]
        if indices:
            text = text[min(indices):].strip()

    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        text = match.group(1).strip()
    
    json_match = re.search(r'(\[[\s\S]*\]|\{[\s\S]*\})', text)
    if json_match:
        text = json_match.group(1).strip()

    text = re.sub(r',\s*([}\]])', r'\1', text)
    return json.loads(text)

class CineGenPlanner:
    def __init__(self, model_path: Optional[str] = None, n_ctx: int = 4096):
        if model_path is None:
            if os.path.exists(DEFAULT_QWEN_9B):
                model_path = DEFAULT_QWEN_9B
            elif os.path.exists(DEFAULT_QWEN_4B):
                model_path = DEFAULT_QWEN_4B
            else:
                raise FileNotFoundError("Nenhum modelo Qwen 3.5 encontrado em C:\\IA_dublagem\\MODELS\\")
        
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.llm = None

    def load_model(self):
        if self.llm is not None:
            return
        
        print(f"🧠 [PLANNER] Carregando Qwen 3.5 com KV Cache em 4-bits ({os.path.basename(self.model_path)})...", flush=True)
        import llama_cpp
        from llama_cpp import Llama
        t0 = time.time()
        self.llm = Llama(
            model_path=self.model_path,
            n_gpu_layers=-1,
            n_ctx=self.n_ctx,
            type_k=getattr(llama_cpp, 'GGML_TYPE_Q4_0', 2),
            type_v=getattr(llama_cpp, 'GGML_TYPE_Q4_0', 2),
            flash_attn=True,
            verbose=False
        )
        print(f"✅ [PLANNER] Qwen 3.5 pronto na GPU (KV Cache Q4_0 ativo) em {time.time()-t0:.2f}s!", flush=True)

    def unload_model(self):
        if self.llm is not None:
            print("🧹 [PLANNER] Descarregando Qwen 3.5 e liberando VRAM...", flush=True)
            del self.llm
            self.llm = None
        
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
        print("✅ [PLANNER] VRAM liberada com sucesso.", flush=True)

    def _query_qwen(self, system_prompt: str, user_prompt: str, max_tokens: int = 2500, temperature: float = 0.2) -> str:
        self.load_model()
        formatted_prompt = (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        response = self.llm(
            formatted_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["<|im_end|>", "<|endoftext|>"]
        )
        return response["choices"][0]["text"].strip()

    # =========================================================================
    # ETAPA 1: ANÁLISE E DIVISÃO NARRATIVA (COM CRIAÇÃO DE DIÁLOGOS)
    # =========================================================================
    def run_stage1_narrative(
        self,
        script_text: str,
        actors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        print("🎬 [ETAPA 1] Executando Análise e Divisão Narrativa...", flush=True)
        actor_names = [a.get("name", "Personagem") for a in actors]
        actor_list_str = ", ".join(actor_names)

        # Detecta divisão de cenas estruturadas (ex: CENA 1, CENA 2...)
        if re.search(r'CENA\s+\d+', script_text, re.IGNORECASE):
            raw_blocks = re.split(r'(CENA\s+\d+[^\n]*)', script_text, flags=re.IGNORECASE)
            chunks = []
            curr_title = ""
            for item in raw_blocks:
                item = item.strip()
                if not item:
                    continue
                if re.match(r'^CENA\s+\d+', item, re.IGNORECASE):
                    curr_title = item
                else:
                    chunks.append(f"{curr_title}\n\n{item}" if curr_title else item)
            print(f"🎬 [ETAPA 1] Roteiro estruturado detectado: {len(chunks)} cenas identificadas. Processando cena por cena...", flush=True)
        else:
            paragraphs = [p.strip() for p in script_text.split("\n\n") if p.strip()]
            if len(paragraphs) > 3:
                print(f"📖 [ETAPA 1] Roteiro longo detectado ({len(paragraphs)} parágrafos). Processando por blocos dramáticos...", flush=True)
                chunks = []
                current_chunk = []
                curr_len = 0
                for p in paragraphs:
                    current_chunk.append(p)
                    curr_len += len(p)
                    if curr_len >= 600:
                        chunks.append("\n\n".join(current_chunk))
                        current_chunk = []
                        curr_len = 0
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
            else:
                chunks = [script_text]

        all_shots = []
        shot_counter = 1

        system_prompt = (
            "Você é um Diretor de Cinema e Roteirista de elite para produções audiovisuais com IA.\n"
            "Sua tarefa é analisar o trecho do roteiro e dividi-lo em planos cinematográficos individuais de ~3.0 segundos.\n"
            "DIRETRIZES TÉCNICAS OBRIGATÓRIAS:\n"
            "1. NÃO use bloco de pensamento <think>. Responda DIRETAMENTE com o JSON puro.\n"
            "2. RESPEITO RIGOROSO À ESTRUTURA NARRATIVA E AMBIENTES:\n"
            "   - Laboratório / Cápsulas Neurais (início e desfecho): interior sci-fi, luzes azuis/frias, monitores.\n"
            "   - Sala de Comando / Centro Tático: ambiente militar, telas táticas com registros de anomalia.\n"
            "   - Cenário Devastado: cidade em ruínas, veículos abandonados, fumaça preta e escombros.\n"
            "   - Área Externa com IA: interface holográfica/digital materializando presença virtual.\n"
            "3. CENAS DE AÇÃO, CONFRONTO E PERSEGUIÇÃO SEM FALAS:\n"
            "   - Quando o trecho tratar de perseguição, confronto com ameaças, fuga dinâmica entre escombros ou suspense, NÃO invente falas forçadas!\n"
            "   - Nestes planos de pura adrenalina e suspense, defina 'speaker': null e 'dialogue': '' (vazio), priorizando a ação cinematográfica no campo 'action'.\n"
            "4. PLANOS DE DIÁLOGO:\n"
            "   - Crie falas diretas, concisas e inteligentes (~15 caracteres por segundo, ~40 a 50 caracteres por plano de 3s) EXCLUSIVAMENTE nos momentos de conversa legítima entre os personagens ou ordens de comando.\n"
            "5. Saída ESTRITAMENTE em formato JSON (lista de objetos)."
        )

        for chunk_idx, chunk in enumerate(chunks):
            user_prompt = f"""
PERSONAGENS DO ELENCO:
{actor_list_str}

TRECHO DO ROTEIRO:
{chunk}

Retorne uma lista JSON com os planos no seguinte formato:
[
  {{
    "shot_id": "shot_{shot_counter:03d}",
    "order": {shot_counter},
    "duration_seconds": 3.0,
    "characters": ["{actor_names[0] if actor_names else 'Personagem'}"],
    "speaker": "{actor_names[0] if actor_names else 'null'}",
    "dialogue": "Fala curta criada para o personagem ou vazia",
    "action": "Ação descritiva do que acontece no plano",
    "emotion": "expressão emocional",
    "environment": "descrição do local e luz",
    "needs_animation": true
  }}
]
"""
            raw_output = self._query_qwen(system_prompt, user_prompt, max_tokens=1800, temperature=0.2)
            try:
                shots = clean_llm_json_response(raw_output)
                if not isinstance(shots, list):
                    if isinstance(shots, dict) and "shots" in shots:
                        shots = shots["shots"]
                    else:
                        shots = [shots]
                
                # Re-indexa os shot_ids
                for s in shots:
                    s["shot_id"] = f"shot_{shot_counter:03d}"
                    s["order"] = shot_counter
                    all_shots.append(s)
                    shot_counter += 1
            except Exception as e:
                print(f"⚠️ [ETAPA 1] Bloco {chunk_idx+1} usou fallback heurístico ({e})", flush=True)
                fallback_shots = self._fallback_stage1(chunk, actors, start_idx=shot_counter)
                for s in fallback_shots:
                    all_shots.append(s)
                    shot_counter += 1

        print(f"✅ [ETAPA 1] Roteiro dividido com sucesso em {len(all_shots)} planos narrativos com diálogos cinematográficos!", flush=True)
        return all_shots

    def _fallback_stage1(self, script_text: str, actors: List[Dict[str, Any]], start_idx: int = 1) -> List[Dict[str, Any]]:
        lines = [line.strip() for line in script_text.split("\n") if line.strip()]
        actor_names = [a.get("name", "Personagem") for a in actors]
        shots = []
        shot_idx = start_idx

        for line in lines:
            speaker = None
            dialogue = line
            for name in actor_names:
                if line.lower().startswith(name.lower() + ":"):
                    speaker = name
                    dialogue = line[len(name)+1:].strip().strip('"').strip("'")
                    break

            if not speaker:
                chars_present = [n for n in actor_names if n.lower() in line.lower()]
                shots.append({
                    "shot_id": f"shot_{shot_idx:03d}",
                    "order": shot_idx,
                    "duration_seconds": 3.0,
                    "characters": chars_present if chars_present else actor_names[:1],
                    "speaker": None,
                    "dialogue": "",
                    "action": dialogue,
                    "emotion": "ambient / reaction",
                    "environment": "cinematic location",
                    "needs_animation": True
                })
                shot_idx += 1
                continue

            chunks = [dialogue[i:i+45] for i in range(0, max(len(dialogue), 1), 45)]
            for chunk in chunks:
                shots.append({
                    "shot_id": f"shot_{shot_idx:03d}",
                    "order": shot_idx,
                    "duration_seconds": 3.0,
                    "characters": [speaker],
                    "speaker": speaker,
                    "dialogue": chunk.strip(),
                    "action": f"{speaker} em cena",
                    "emotion": "expressivo",
                    "environment": "cinematic location",
                    "needs_animation": True
                })
                shot_idx += 1
        return shots

    # =========================================================================
    # ETAPA 2: PLANEJAMENTO VISUAL E PROMPTS DE IMAGEM (FLUX.3)
    # =========================================================================
    def run_stage2_visual(
        self,
        stage1_shots: List[Dict[str, Any]],
        actors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        print("🎨 [ETAPA 2] Planejando Visuais e Prompts de Imagem (FLUX.3 Klein)...", flush=True)
        actor_map = {a.get("name", "").lower(): a for a in actors}

        # Divide os planos em lotes de até 6 planos para JSON seguro
        batch_size = 6
        merged_shots = []
        image_catalog: Dict[str, str] = {}
        next_img_id = 1

        system_prompt = (
            "Você é o Diretor de Fotografia cinematográfico.\n"
            "Sua responsabilidade é planejar a composição visual e os prompts para o modelo FLUX.3 Klein.\n"
            "DIRETRIZES CRÍTICAS:\n"
            "1. NÃO use bloco <think>. Responda DIRETAMENTE com o JSON puro.\n"
            "2. NÃO invente características físicas conflitantes dos personagens (a identidade visual vem 100% das fotos de referência).\n"
            "3. Indique enquadramento (close-up, medium shot, wide shot), luz (golden hour, soft rim light, 35mm film grain, 8k), pose e expressão.\n"
            "4. REUSO INTELIGENTE DE IMAGENS: Se planos vizinhos tiverem o mesmo personagem no mesmo ângulo/cenário e atitude compatível, "
            "defina 'reuse_image_id' com o ID da imagem anterior (ex: 'img_001') para economizar tempo de GPU e manter continuidade!\n"
            "5. Os prompts no campo 'flux_prompt' devem ser em INGLÊS, concisos e fotorrealistas.\n"
            "6. Responda em lista JSON."
        )

        for b_start in range(0, len(stage1_shots), batch_size):
            batch = stage1_shots[b_start:b_start + batch_size]
            user_prompt = f"""
PLANOS DA ETAPA 1:
{json.dumps([{
    "shot_id": s["shot_id"],
    "characters": s["characters"],
    "speaker": s["speaker"],
    "dialogue": s["dialogue"],
    "action": s["action"],
    "emotion": s["emotion"],
    "environment": s["environment"]
} for s in batch], indent=2, ensure_ascii=False)}

Formato JSON esperado para cada plano:
[
  {{
    "shot_id": "{batch[0]['shot_id']}",
    "framing": "cinematic medium close-up",
    "spatial_layout": "solo centered",
    "image_id": "img_{next_img_id:03d}",
    "reuse_image_id": null,
    "flux_prompt": "Cinematic 35mm photography of character in cinematic setting, photorealistic 8k, warm cinematic lighting",
    "lighting": "cinematic rim lighting",
    "atmosphere": "tense and immersive"
  }}
]
"""
            raw_output = self._query_qwen(system_prompt, user_prompt, max_tokens=2200, temperature=0.1)
            try:
                visual_shots = clean_llm_json_response(raw_output)
                if not isinstance(visual_shots, list):
                    if isinstance(visual_shots, dict) and "shots" in visual_shots:
                        visual_shots = visual_shots["shots"]
                    else:
                        visual_shots = [visual_shots]
            except Exception:
                visual_shots = []

            visual_by_id = {s.get("shot_id"): s for s in visual_shots if isinstance(s, dict)}

            for idx_in_batch, s1 in enumerate(batch):
                s_id = s1.get("shot_id")
                v_info = visual_by_id.get(s_id, {})
                chars = s1.get("characters", [])
                is_couple = len(chars) >= 2

                reuse_id = v_info.get("reuse_image_id")
                if not reuse_id and (len(merged_shots) > 0):
                    prev = merged_shots[-1]
                    if prev.get("characters") == chars and prev.get("environment") == s1.get("environment"):
                        reuse_id = prev.get("image_id")

                if reuse_id and reuse_id in image_catalog:
                    img_id = reuse_id
                    is_reused = True
                else:
                    img_id = v_info.get("image_id") or f"img_{next_img_id:03d}"
                    next_img_id += 1
                    is_reused = False

                flux_prompt = v_info.get("flux_prompt")
                if not flux_prompt or len(flux_prompt) < 15:
                    env = s1.get("environment", "war-torn city streets with dust and dramatic cinematic shadows")
                    emotion = s1.get("emotion", "tense and watchful")
                    action_desc = s1.get("action", "")
                    
                    if not s1.get("dialogue") or not s1.get("speaker"):
                        # Plano de pura ação / tiroteio / suspense
                        flux_prompt = (
                            f"Cinematic 35mm wide action still, {action_desc}, in {env}, "
                            f"volumetric smoke, muzzle flashes, falling debris, photorealistic 8k, dramatic cinematic contrast"
                        )
                    elif is_couple:
                        flux_prompt = (
                            f"Cinematic 35mm film still of two characters together at {env}, {emotion}, "
                            f"photorealistic 8k, atmospheric lighting, shallow depth of field, high-end film still"
                        )
                    else:
                        char_name = chars[0] if chars else "character"
                        flux_prompt = (
                            f"Cinematic portrait of {char_name} in {env}, {emotion}, "
                            f"natural cinematic lighting, 35mm film photography, 8k resolution, award winning cinematography"
                        )

                ref_bindings = []
                for c_name in chars:
                    c_key = c_name.lower().strip()
                    if c_key in actor_map and actor_map[c_key].get("ref_path"):
                        ref_bindings.append({
                            "name": c_name,
                            "ref_path": actor_map[c_key]["ref_path"],
                            "gender": actor_map[c_key].get("gender", "Feminino")
                        })

                merged = {
                    **s1,
                    "framing": v_info.get("framing", "medium close-up cinematic portrait"),
                    "spatial_layout": v_info.get("spatial_layout", "left: right" if is_couple else "solo centered"),
                    "image_id": img_id,
                    "is_image_reused": is_reused,
                    "flux_prompt": flux_prompt,
                    "lighting": v_info.get("lighting", "cinematic volumetric lighting"),
                    "atmosphere": v_info.get("atmosphere", "suspenseful and cinematic"),
                    "ref_bindings": ref_bindings,
                    "is_couple": is_couple
                }
                if not is_reused:
                    image_catalog[img_id] = flux_prompt
                merged_shots.append(merged)

        unique_imgs = len(set(s["image_id"] for s in merged_shots))
        print(f"✅ [ETAPA 2] {len(merged_shots)} planos mapeados para {unique_imgs} imagens únicas ({len(merged_shots)-unique_imgs} planos reaproveitados).", flush=True)
        return merged_shots

    # =========================================================================
    # ETAPA 3: PLANEJAMENTO DOS PROMPTS DE ANIMAÇÃO (KANDINSKY 6.0 LITE)
    # =========================================================================
    def run_stage3_animation(
        self,
        stage2_shots: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        print("🎥 [ETAPA 3] Planejando Animação e Foley (Kandinsky 6.0 Lite)...", flush=True)
        batch_size = 6
        final_shots = []

        system_prompt = (
            "Você é um Diretor de Animação e Efeitos especializado no modelo Kandinsky 6.0 Lite (vídeos de 3 segundos a 24fps).\n"
            "DIRETRIZES TÉCNICAS OBRIGATÓRIAS:\n"
            "1. NÃO use bloco de pensamento <think>. Responda DIRETAMENTE com o JSON puro.\n"
            "2. Priorize movimentos faciais e de câmera sutis: leve movimento dos lábios ao falar, "
            "piscar natural de olhos, suave brisa movendo fios de cabelo, respiração relaxada, slow camera push-in.\n"
            "3. NUNCA solicite acrobacias corporais, cambalhotas, lutas ou movimentos rápidos.\n"
            "4. Prompts em INGLÊS no campo 'video_prompt' e ambiente foley limpo em 'audio_prompt'.\n"
            "5. Responda estritamente em formato JSON."
        )

        for b_start in range(0, len(stage2_shots), batch_size):
            batch = stage2_shots[b_start:b_start + batch_size]
            user_prompt = f"""
PLANOS PARA ANIMAR:
{json.dumps([{
    "shot_id": s["shot_id"],
    "characters": s["characters"],
    "speaker": s["speaker"],
    "dialogue": s["dialogue"],
    "action": s["action"],
    "emotion": s["emotion"]
} for s in batch], indent=2, ensure_ascii=False)}

Formato JSON esperado:
[
  {{
    "shot_id": "{batch[0]['shot_id']}",
    "video_prompt": "The character speaks with natural mouth movement, subtle head tilt, gentle breeze moving strands of hair, slow cinematic camera zoom, highly stable motion",
    "audio_prompt": "Subtle ambient room tone, distant atmospheric hum, quiet clean foley, no music",
    "motion_level": "subtle",
    "animation_type": "dialogue_speaking"
  }}
]
"""
            raw_output = self._query_qwen(system_prompt, user_prompt, max_tokens=2200, temperature=0.1)
            try:
                anim_shots = clean_llm_json_response(raw_output)
                if not isinstance(anim_shots, list):
                    if isinstance(anim_shots, dict) and "shots" in anim_shots:
                        anim_shots = anim_shots["shots"]
                    else:
                        anim_shots = [anim_shots]
            except Exception:
                anim_shots = []

            anim_by_id = {s.get("shot_id"): s for s in anim_shots if isinstance(s, dict)}

            for s2 in batch:
                s_id = s2.get("shot_id")
                a_info = anim_by_id.get(s_id, {})

                speaker = s2.get("speaker")
                dialogue = s2.get("dialogue")
                emotion = s2.get("emotion", "expressive")
                action_text = s2.get("action", "action scene")

                if speaker and dialogue:
                    default_v_prompt = (
                        f"The character speaks with {emotion} expression, subtle natural mouth motion, "
                        f"soft eye blinks, gentle ambient breeze in hair, slow cinematic camera zoom, highly stable motion"
                    )
                    default_a_prompt = "Natural subtle room tone, clean quiet foley, no music"
                    default_type = "dialogue_speaking"
                elif "tiro" in action_text.lower() or "soldado" in action_text.lower() or "monstro" in action_text.lower() or "fuga" in action_text.lower():
                    default_v_prompt = (
                        f"Intense cinematic tracking shot of {action_text}, "
                        f"rising war smoke, flying dust particles, camera shake, highly stable realistic motion"
                    )
                    default_a_prompt = "Heavy adrenaline breathing, distant rapid gunfire, crumbling concrete, war zone ambiance, no music"
                    default_type = "action_combat"
                else:
                    default_v_prompt = (
                        f"The character listens and reacts with {emotion} gaze, subtle natural breathing, "
                        f"soft atmospheric breeze, slow subtle camera movement, highly cinematic"
                    )
                    default_a_prompt = "Natural subtle ambient atmosphere, quiet foley, no music"
                    default_type = "reaction_listening"

                video_prompt = a_info.get("video_prompt") or default_v_prompt
                audio_prompt = a_info.get("audio_prompt") or default_a_prompt

                final_shot = {
                    **s2,
                    "video_prompt": video_prompt,
                    "audio_prompt": audio_prompt,
                    "motion_level": a_info.get("motion_level", "subtle"),
                    "animation_type": a_info.get("animation_type", default_type),
                    "status": "planned"
                }
                final_shots.append(final_shot)

        print(f"✅ [ETAPA 3] {len(final_shots)} planos de animação e áudio configurados com precisão!", flush=True)
        return final_shots

    # =========================================================================
    # PIPELINE INTEGRADO COMPLETO
    # =========================================================================
    def plan_full_project(
        self,
        script_text: str,
        actors: List[Dict[str, Any]],
        project_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        t_start = time.time()
        print("="*70)
        print("🎬 [CINEGEN PLANNER] INICIANDO PLANEJAMENTO INTEGRADO EM 3 ETAPAS")
        print("="*70)

        self.load_model()
        try:
            stage1 = self.run_stage1_narrative(script_text, actors)
            stage2 = self.run_stage2_visual(stage1, actors)
            stage3 = self.run_stage3_animation(stage2)
        finally:
            self.unload_model()

        elapsed = round(time.time() - t_start, 2)
        unique_images = list({s["image_id"] for s in stage3})

        project_plan = {
            "title": f"Projeto CineGen - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "created_at": time.time(),
            "elapsed_planning_seconds": elapsed,
            "total_shots": len(stage3),
            "unique_images_needed": len(unique_images),
            "actors": actors,
            "shots": stage3
        }

        if project_dir:
            os.makedirs(project_dir, exist_ok=True)
            plan_file = os.path.join(project_dir, "cinegen_plan.json")
            with open(plan_file, "w", encoding="utf-8") as f:
                json.dump(project_plan, f, indent=2, ensure_ascii=False)
            print(f"📁 [PLANNER] Plano completo salvo em: {plan_file}")

        print(f"🎉 [PLANNER] Planejamento concluído com perfeição em {elapsed}s!")
        return project_plan
