import json
import re

plan_path = r"C:\CineGen\projects\experimento_vertice_ep3_oficial\cinegen_plan.json"
with open(plan_path, "r", encoding="utf-8") as f:
    plan = json.load(f)

shots = plan.get("shots", [])
print(f"Total de planos analisados: {len(shots)}")

headers_count = 0
pt_count = 0
found_list = []

for s in shots:
    p = s.get("flux_prompt", "")
    has_header = bool(re.search(r"\b(CENA\s*\d+|Local:)\b", p, re.I))
    # Detecta palavras típicas com acentuação ou termos específicos em pt
    has_pt = bool(re.search(r"[áéíóúâêôãõç]|laborat|capsul|escombro|fumaca|soldado|criatura|destru|anomalia|simula|resposta|pergunta|participante", p, re.I))
    
    if has_header:
        headers_count += 1
    if has_pt:
        pt_count += 1
        found_list.append((s["shot_id"], p))

print(f"1. Prompts com vazamento de cabeçalho (CENA / Local): {headers_count}")
print(f"2. Prompts com palavras em português: {pt_count}")
print(f"Total de prompts que precisam de correção fina: {len(found_list)}")
print("\nExemplos de prompts identificados:")
for sid, text in found_list[:6]:
    print(f" - [{sid}] {text}")
