# 🎬 CineGen — Autonomous AI Cinema Studio

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-v0.2.0%20%7C%20Agent--Directed%20Studio-brightgreen)](https://github.com/NarraVox/Cinegen)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Hardware Target](https://img.shields.io/badge/Hardware-NVIDIA_RTX_3050_6GB-76B900)](https://www.nvidia.com/)
[![Agents](https://img.shields.io/badge/Agents-Antigravity%20%7C%20Codex%20%7C%20Bionic-purple)](docs/CINEGEN_MASTER_DIRECTOR_BIONIC.md)

> **Estúdio de Cinema Autônomo com Inteligência Artificial: Produção cinematográfica de alta fidelidade operada por Agentes Autônomos de IA em GPUs domésticas (6 GB de VRAM).**

---

> [!NOTE]
> ### 🤖 Como o CineGen Funciona Atualmente: O Paradigma de Agentes
> * **O CineGen hoje opera através de Agentes Autônomos de IA** (como **Google Antigravity**, **OpenAI Codex / ChatGPT** e modelos locais **Bionic / Qwen**).
> * **Não se trata de um instalador `.exe` tradicional com botões**: o criador atua como **Produtor Executivo**, dialogando com o Agente Diretor em linguagem natural.
> * O Agente de IA assume a **Direção Técnica de Cinema**:
>   1. **Speech Budgeting (Orçamento de Fala e Tempo):** Calcula a contagem exata de quadros a 24 FPS (3.0s / 4.0s / 5.0s) de acordo com a cadência emocional da fala, prevenindo cortes bruscos de áudio.
>   2. **Shot Splitting:** Divide falas complexas em múltiplos ângulos sequenciais de câmera.
>   3. **Fotografia 35mm no FLUX.3 Klein:** Ancoragem de elenco e iluminação cinematográfica.
>   4. **Animação & Lip-Sync Orgânico no Kandinsky 6.0 Lite:** Tags canônicas `<S>...<E>` para sincronização labial perfeita em inglês.
>   5. **Dublagem Neural de Estúdio PT-BR:** Síntese local via Qwen3-TTS mantendo o *Time Budget* exato do clipe.
>   6. **Orquestração e Descarregamento Dinâmico de VRAM:** Liberação contínua de memória (`/free`) permitindo que todo o pipeline rode fluido em uma **RTX 3050 de 6 GB**.
>
> Essa metodologia orientada a agentes tem se mostrado extremamente produtiva e estável, entregando episódios e cenas completas com padrão estético de cinema.

---

## 🏛️ 1. O que é o Projeto CineGen?

O **CineGen** é um projeto de código aberto desenvolvido por **Paulo Henrik Carvalho Araújo** (NarraVox Studios) focado na democratização da produção de cinema e animação realista com IA.

Enquanto a maioria das soluções atuais exige servidores em nuvem de alto custo ou GPUs industriais de 24 GB a 80 GB, o CineGen foi projetado desde a base para operar localmente dentro do limite de **6 GB de VRAM** da NVIDIA GeForce RTX 3050.

### 🌟 Pilares do Motor:
1. **FLUX.3 Klein (4B GGUF):** Geração de imagens base estáticas com fotografia real de filme 35mm/85mm, profundidade de campo orgânica (bokeh) e fixação anatômica de personagens por ancoragem espacial (`<ref_image_0>`, `<ref_image_1>`).
2. **Kandinsky 6.0 Lite (AV-DiT Multimodal):** Difusão temporal de vídeo e áudio sincronizados a 24 FPS (tomadas de 3.0s a 5.0s).
3. **Qwen3-TTS Local:** Dublagem de estúdio em português brasileiro com clonagem de timbre e afinação acústica.
4. **Upscale Neural SPAN (2x-NomosUni):** Masterização final em **1080p Full HD** cristalino.

---

## 📖 2. Documentação e Regras de Produção

Consulte o manual canônico de planejamento cinematográfico utilizado pelos agentes:

* **[Manual Mestre do Diretor (Bionic / Agentes)](docs/CINEGEN_MASTER_DIRECTOR_BIONIC.md)**: Regras estritas de *Speech Budgeting*, tabelas de calibração empírica de 24 FPS, regras da pontuação (respiro de ~1.0s), diretrizes canônicas de prompt e ciclo de VRAM.

---

## 📁 3. Estrutura do Repositório

```text
CineGen/
├── cinegen/                      # 📦 Código-fonte do motor e interface
│   ├── __init__.py               # Ponto de entrada do pacote Python
│   ├── engine.py                 # Orquestrador de inferência
│   ├── client.py                 # Conector REST e polling
│   ├── preprocessor.py           # Enquadramento e preparação de referências
│   ├── prompt_builder.py         # Construtor de prompts fotográficos
│   ├── workflow_builder.py       # Gerador dinâmico de nós ComfyUI
│   ├── planner.py                # Planejador de cenas
│   ├── server.py                 # Servidor de streaming e visualização
│   └── ui/                       # Interface web do estúdio
│
├── docs/                         # 📖 Manuais técnicos oficiais
│   └── CINEGEN_MASTER_DIRECTOR_BIONIC.md # Diretrizes mestras para agentes
│
├── LICENSE                       # Licença Apache 2.0
├── NOTICE                        # Atribuições legais e autoria
├── COPYRIGHT.md                  # Declaração formal de autoria
├── THIRD_PARTY_LICENSES.md       # Licenças de modelos abertos utilizados
└── .gitignore                    # Bloqueio rigoroso de mídias privadas e modelos pesados
```

---

## 🚫 4. O que NÃO está incluído neste repositório

Para manter o repositório leve, limpo e em estrita conformidade de privacidade e direitos:
* **Modelos neurais binários (`.safetensors`, `.gguf`) NÃO fazem parte do repositório.**
* **Mídias privadas, gravações e testes de elenco NÃO são incluídos.**
* O ambiente local ComfyUI e seus nós customizados devem ser configurados localmente conforme as instruções dos desenvolvedores parceiros.

---

## 📜 5. Autoria e Licença

* **Autor e Arquiteto**: **Paulo Henrik Carvalho Araújo**
* **Organização**: NarraVox Studios
* **Licença**: **[Apache License 2.0](LICENSE)**

Consulte [`COPYRIGHT.md`](COPYRIGHT.md) e [`NOTICE`](NOTICE) para detalhes de atribuição.

---

*CineGen v0.2.0 — Criando o futuro do cinema independente com Inteligência Artificial.* 🎬⚡
