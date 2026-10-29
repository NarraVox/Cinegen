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
from pathlib import Path
from .engine import CineGenEngine

def main():
    parser = argparse.ArgumentParser(
        prog="cinegen",
        description="CineGen CLI: Sistema de Geração de Imagens Cinematográficas com Fidelidade Real"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Comando status
    subparsers.add_parser("status", help="Verifica a conexão com o servidor local ComfyUI")

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
