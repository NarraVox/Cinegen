# 🎬 CineGen — Autonomous AI Cinema Studio

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-v0.0.1%20%7C%20Experimental-orange)](https://github.com/NarraVox)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Hardware Target](https://img.shields.io/badge/Hardware-NVIDIA_RTX_3050_6GB-76B900)](https://www.nvidia.com/)

> **Motor conceitual e código-fonte inicial de pesquisa para geração de cinema com Inteligência Artificial.**

---

> [!WARNING]
> ### ⚠️ AVISO IMPORTANTE: ESTÁGIO INICIAL DE DESENVOLVIMENTO (v0.0.1)
> * **O CINEGEN AINDA NÃO ESTÁ FUNCIONANDO COMO UM PROGRAMA FINAL OU EXECUTÁVEL NESTE MOMENTO.**
> * Este repositório contém estritamente o **primeiro código-fonte experimental** criado para o projeto, servindo como base de engenharia e pesquisa.
> * **NÃO EXISTE INSTALADOR DISPONÍVEL (`setup.exe`)** e **não há como executar o programa de forma pronta ou com 1 clique** para usuários comuns.
> * O projeto está em seus primeiros testes de viabilidade técnica. Em um futuro próximo, teremos novidades, atualizações e versões funcionais consolidadas.

---

## 👁️ 1. O que é o Projeto CineGen?

O **CineGen** é um projeto de código aberto idealizado por **Paulo Henrik Carvalho Araújo** para viabilizar a criação de cenas cinematográficas com atores consistentes utilizando Inteligência Artificial em GPUs domésticas de entrada (com foco no limite de **6 GB de VRAM** da NVIDIA GeForce RTX 3050).

O motor pesquisa a união de duas tecnologias de ponta em modelos abertos:
1. **FLUX.3 Klein (4B GGUF)**: Para geração de imagens estáticas, enquadramentos de fotografia real (35mm/85mm), eliminação do aspecto artificial plástico de IA e fixação facial de múltiplos atores (ancoragem espacial esquerda/direita com `<ref_image_0>` e `<ref_image_1>`).
2. **Kandinsky 6.0 Lite (INT8 / W4A4)**: Para difusão temporal ultraleve de micro-takes de vídeo de 3 a 4 segundos a 24 FPS diretamente na GPU local.

---

## 🏛️ 2. Estrutura do Código-Fonte (`cinegen/`)

Seguindo o padrão arquitetural profissional do ecossistema NarraVox, **todo o código original do projeto está centralizado na pasta `cinegen/`**:

```text
CineGen/
├── cinegen/                      # 📦 PASTA CENTRAL DO CÓDIGO-FONTE ORIGINAL
│   ├── __init__.py               # Ponto de entrada do pacote Python
│   ├── __main__.py               # Ponto de entrada do CLI (python -m cinegen)
│   ├── engine.py                 # Orquestrador central (CineGenEngine)
│   ├── client.py                 # Cliente de rede HTTP REST / Polling com daemon ComfyUI
│   ├── preprocessor.py           # Normalização EXIF e enquadramento inteligente 9:16
│   ├── prompt_builder.py         # Construtor de prompts fotográficos com ancoragem espacial
│   ├── workflow_builder.py       # Gerador dinâmico de árvores de nós GGUF
│   ├── cli.py                    # Interface de comandos de terminal
│   ├── ui/                       # 🎨 Interface Gráfica do Estúdio (HTML/CSS/JS)
│   │   ├── index.html            # Layout visual do estúdio de cinema
│   │   ├── css/                  # Folhas de estilo futuristas
│   │   └── js/                   # Controladores da interface e polling de cenas
│   └── mcp/                      # 🤖 Servidor MCP para controle por agentes de IA
│       └── comfy_mcp_server.py   # Model Context Protocol Server
│
├── scripts/                      # 🛠️ Scripts mestres de pipeline, upscale e testes
├── docs/                         # 📖 Manuais técnicos de arquitetura e prompts
├── LICENSE                       # Licença oficial Apache License 2.0
├── NOTICE                        # Atribuição oficial de autoria e aviso de modelos
├── COPYRIGHT.md                  # Declaração formal de autoria e direitos autorais
├── THIRD_PARTY_LICENSES.md       # Relação de ferramentas e modelos parceiros
└── .gitignore                    # Bloqueio estrito de arquivos pesados e fotos pessoais
```

---

## 🚫 3. O que NÃO está incluído neste repositório

Para manter o repositório leve, limpo e em estrita conformidade legal:
* **Modelos neurais pesados (`.safetensors`, `.gguf`, `.ckpt`) NÃO fazem parte deste repositório.**
* **O software ComfyUI NÃO está embutido aqui** (deverá ser instalado separadamente pelo usuário quando o projeto for lançado).
* **Nenhum arquivo de foto pessoal ou mídia privada de teste está incluído.**

---

## 📜 4. Autoria e Licença

* **Autor e Desenvolvedor Original**: **Paulo Henrik Carvalho Araújo**
* **Organização**: NarraVox Studios
* **Licença**: **[Apache License 2.0](LICENSE)**

Você pode estudar, testar e contribuir com o código, desde que respeite os termos da licença e mantenha todos os avisos de autoria e direitos autorais preservados. Consulte [`COPYRIGHT.md`](COPYRIGHT.md) para mais detalhes.

---

*CineGen v0.0.1 — Em desenvolvimento contínuo por NarraVox Studios.* 🎬⚡
