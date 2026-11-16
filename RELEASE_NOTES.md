# ⚡ CINEGEN v0.2.0 :: AGENT-DIRECTED CINEMA PROTOCOL

> [!NOTE]
> **ESTÚDIO DE CINEMA AUTÔNOMO DIRIGIDO POR AGENTES DE IA**  
> A versão **v0.2.0** introduz o paradigma da **Direção Autônoma por Agentes** no ecossistema CineGen. Em vez de uma interface gráfica fechada e rígida, a produção de cinema agora é orquestrada por agentes de raciocínio profundo (**Google Antigravity**, **OpenAI Codex / ChatGPT** e **Bionic LLM**), atuando diretamente como Diretores Técnicos e Cinematográficos em comunicação contínua com a GPU local (NVIDIA RTX 3050 6GB).

---

### 🌌 1. O NOVO PARADIGMA: CINEMA ORQUESTRADO POR AGENTES
- **Produtor Executivo & Diretor Técnico**: O criador define o roteiro e o tom em linguagem natural; o Agente de IA calcula a física da cena, a orçamentação temporal exata de fala (*Speech Budgeting*) e despacha as tomadas para renderização.
- **Micro-Takes e Cadência Temporal (24 FPS)**: Otimização rígida para blocos de 3.0s (73 frames), 4.0s (97 frames) e 5.0s (121 frames).
- **A Regra do Ponto Final (~1.0s de Respiro)**: Calibração das pausas dramáticas de atores virtuais para impedir cortes abruptos de áudio.
- **Shot Splitting Automático**: Decomposição automática de falas complexas em múltiplos ângulos de câmera (close-up para contra-campo).

---

### 🎬 2. PIPELINE MULTIMODAL INTEGRADO
- **Fotografia Base 35mm (FLUX.3 Klein)**: Geração de quadros fotorrealistas com lentes anamórficas de 35mm/85mm, profundidade de campo orgânica (bokeh) e fixação de elenco por ancoragem espacial (`<ref_image_0>`, `<ref_image_1>`).
- **Animação & Lip-Sync Orgânico (Kandinsky 6.0 Lite AV-DiT)**: Difusão temporal com tags canônicas de fala `<S>...<E>` ativando a sincronização labial natural de visemas e fonemas.
- **Arquitetura Dual-Master (EN vs PT-BR)**: Áudio de set orgânico nativo em inglês e trilha de dublagem neural local de estúdio em português brasileiro via Qwen3-TTS.
- **Masterização 1080p Full HD**: Upscaling neural via 2x-NomosUni SPAN eliminando ruídos e artefatos de compressão.

---

### 🛡️ 3. ENGENHARIA DE VRAM NA RTX 3050 (6GB)
- **Protocolo de Ciclo Descarregado (Offload Cycle)**: Liberação contínua de VRAM (`/free`) após cada estágio (FLUX.3 ➔ Kandinsky ➔ TTS ➔ SPAN Upscale), permitindo que todo o estúdio opere sem engasgos ou estouro de memória em placas de entrada com 6 GB de VRAM.

---

### 🚀 4. NOVO INSTALADOR OFICIAL (1 CLIQUE)
- **Instalação Simplificada (`setup_cinegen.bat`)**:
  - Detecção automática de Python 3.10/3.11/3.12 e aceleração por hardware NVIDIA CUDA.
  - Criação isolada do ambiente virtual (`venv_cinegen`) e instalação de dependências oficiais (`requirements.txt`).
  - Estruturação automática de diretórios de trabalho (`models/`, `queue/`, `projects/`).
  - Criação do inicializador rápido `INICIAR_CINEGEN.bat` com menu de inicialização do estúdio e do motor de fila autônoma.

---

> [!TIP]
> **Consulte o Manual do Diretor Bionic**: Para conhecer todos os padrões de orçamentação de fala, limites de palavras por segundo e diretrizes de prompt, consulte [docs/CINEGEN_MASTER_DIRECTOR_BIONIC.md](docs/CINEGEN_MASTER_DIRECTOR_BIONIC.md).

---

*CineGen v0.2.0 — NarraVox Studios. Democratizando a tecnologia audiovisual com IA.* ⚡🎬
