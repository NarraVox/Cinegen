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

import argparse
import sys
import json
from pathlib import Path
from .engine import CineGenEngine

def main():
    parser = argparse.ArgumentParser(
        prog="cinegen",
        description="CineGen CLI: Sistema de Produção Audiovisual Cinematográfica com IA"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Comando status
    subparsers.add_parser("status", help="Verifica a conexão com o servidor local ComfyUI")

    # Comando serve (inicia estúdio web)
    serve_parser = subparsers.add_parser("serve", help="Inicia o servidor web CineGen Studio (FastAPI + UI)")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host IP (padrão: 127.0.0.1)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Porta HTTP (padrão: 8000)")

    # Comando plan (apenas planejamento com Qwen 3.5)
    plan_parser = subparsers.add_parser("plan", help="Executa o planejamento em 3 etapas com Qwen 3.5 a partir de um roteiro")
    plan_parser.add_argument("--script", required=True, help="Arquivo de texto ou string com o roteiro")
    plan_parser.add_argument("--actors", default=None, help="Arquivo JSON com elenco de personagens")
    plan_parser.add_argument("--output", default=None, help="Diretório para salvar o plano JSON")

    # Comando solo
    solo_parser = subparsers.add_parser("solo", help="Gera uma imagem de um único personagem com fidelidade estrita")
    solo_parser.add_argument("--actor", required=True, help="Caminho para a foto do ator/atriz")
    solo_parser.add_argument("--scenario", required=True, help="Descrição do cenário/ambiente cinematográfico")
    solo_parser.add_argument("--hair", default=None, help="Estilização opcional de cabelo (ex: 'long flowing golden blonde hair')")
    solo_parser.add_argument("--blonde", action="store_true", help="Atalho para deixar o cabelo loiro dourado")
    solo_parser.add_argument("--seed", type=int, default=941, help="Semente determinística (padrão: 941)")
    solo_parser.add_argument("--steps", type=int, default=8, help="Número de etapas de difusão (padrão: 8)")
    solo_parser.add_argument("--prefix", default="CineGen_CLI_Solo", help="Prefixo do arquivo salvo")

    # Comando couple (casal)
    couple_parser = subparsers.add_parser("couple", help="Gera uma cena de casal com ancoragem espacial e multi-referência")
    couple_parser.add_argument("--left", required=True, help="Caminho para a foto do personagem da esquerda")
    couple_parser.add_argument("--right", required=True, help="Caminho para a foto do personagem da direita")
    couple_parser.add_argument("--scenario", required=True, help="Descrição do cenário cinematográfico")
    couple_parser.add_argument("--right-hair", default=None, help="Estilização opcional de cabelo para a pessoa da direita")
    couple_parser.add_argument("--blonde", action="store_true", help="Atalho para deixar o cabelo da pessoa da direita loiro")
    couple_parser.add_argument("--seed", type=int, default=941, help="Semente determinística (padrão: 941)")
    couple_parser.add_argument("--steps", type=int, default=8, help="Número de etapas de difusão (padrão: 8)")
    couple_parser.add_argument("--prefix", default="CineGen_CLI_Casal", help="Prefixo do arquivo salvo")

    args = parser.parse_args()

    if args.command == "serve":
        from .server import run_server
        run_server(host=args.host, port=args.port)
        return

    if args.command == "plan":
        from .planner import CineGenPlanner
        script_content = args.script
        if Path(args.script).exists():
            script_content = Path(args.script).read_text(encoding="utf-8")

        actors = []
        if args.actors and Path(args.actors).exists():
            actors = json.loads(Path(args.actors).read_text(encoding="utf-8"))
        elif not actors:
            actors = [{"name": "Protagonista", "gender": "Masculino"}, {"name": "Especialista", "gender": "Feminino"}]

        planner = CineGenPlanner()
        plan = planner.plan_full_project(script_content, actors, project_dir=args.output or "projects/cli_run")
        print(f"[CineGen] Planejamento concluído com {len(plan['shots'])} planos!")
        return

    engine = CineGenEngine()

    if args.command == "status":
        alive = engine.check_health()
        if alive:
            print("[CineGen] Servidor ComfyUI está ONLINE e respondendo em 127.0.0.1:8188.")
            sys.exit(0)
        else:
            print("[CineGen] Servidor ComfyUI está OFFLINE. Inicie o ComfyUI antes de gerar imagens.")
            sys.exit(1)

    elif args.command == "solo":
        hair = args.hair
        if args.blonde and not hair:
            hair = "gorgeous long flowing golden blonde hair"

        print(f"[CineGen] Iniciando geração solo para: {args.actor}")
        print(f"[CineGen] Cenário: {args.scenario}")
        if hair:
            print(f"[CineGen] Estilização de cabelo: {hair}")

        try:
            res = engine.generate_solo(
                image_path=args.actor,
                scenario=args.scenario,
                hair_style=hair,
                seed=args.seed,
                steps=args.steps,
                output_prefix=args.prefix
            )
            print(f"\n[SUCESSO] Imagem gerada em {res.elapsed_seconds}s!")
            print(f"[ARQUIVO] {res.output_path}")
        except Exception as e:
            print(f"[ERRO] Falha na geração: {e}")
            sys.exit(1)

    elif args.command == "couple":
        right_hair = args.right_hair
        if args.blonde and not right_hair:
            right_hair = "long flowing golden blonde hair"

        print(f"[CineGen] Iniciando geração de casal com multi-referência:")
        print(f"  - Esquerda: {args.left}")
        print(f"  - Direita:  {args.right}")
        print(f"[CineGen] Cenário: {args.scenario}")

        try:
            res = engine.generate_couple(
                left_image_path=args.left,
                right_image_path=args.right,
                scenario=args.scenario,
                right_hair=right_hair,
                seed=args.seed,
                steps=args.steps,
                output_prefix=args.prefix
            )
            print(f"\n[SUCESSO] Imagem de casal gerada em {res.elapsed_seconds}s!")
            print(f"[ARQUIVO] {res.output_path}")
        except Exception as e:
            print(f"[ERRO] Falha na geração: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
