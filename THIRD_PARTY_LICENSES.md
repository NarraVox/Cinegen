# Licenças e Atribuições de Terceiros (Third-Party Licenses)

Este documento relaciona as bibliotecas, ferramentas, frameworks, serviços e arquiteturas de inteligência artificial de terceiros com as quais o **CineGen** interage, orquestra ou faz referência, acompanhadas de suas respectivas licenças e requisitos de atribuição.

---

## 1. Bibliotecas e Módulos Python

| Componente | Função no CineGen | Licença | Compatibilidade com Apache 2.0 |
| :--- | :--- | :--- | :--- |
| **Python Standard Library** (`urllib`, `json`, `argparse`, `pathlib`, `dataclasses`, `time`) | Comunicação HTTP, parsing de argumentos, manipulação de arquivos | Python Software Foundation License (PSF) | Totalmente compatível |
| **Pillow (PIL)** | Pré-processamento de imagens de referência (EXIF, crop 9:16) | HPND License | Permissiva e compatível |
| **MCP (Model Context Protocol SDK)** | Servidor de ferramentas para agentes de IA em `mcp_server/` | MIT License | Totalmente compatível |
| **PyTorch (`torch`)** *(opcional em scripts de teste)* | Tensores e manipulação CUDA local | BSD-3-Clause / PyTorch License | Totalmente compatível |
| **Transformers (`transformers`)** *(opcional em scripts)* | Tokenização e arquiteturas de visão e linguagem | Apache License 2.0 | Totalmente compatível |
| **WebSockets** *(opcional em scripts de monitoramento)* | Monitoramento assíncrono de eventos | BSD-3-Clause | Totalmente compatível |

---

## 2. Ferramentas e Serviços de Execução Externa

### A. ComfyUI
* **Projeto Original**: [ComfyUI (comfyanonymous)](https://github.com/comfyanonymous/ComfyUI)
* **Licença**: GNU General Public License v3.0 (GPL-3.0).
* **Relação com o CineGen**: O CineGen **NÃO embute, não modifica internamente e não distribui o código-fonte ou binários do ComfyUI** dentro de sua árvore de distribuição. O CineGen atua exclusivamente como uma camada cliente/controladora que se comunica com o daemon do ComfyUI rodando em processo independente através de chamadas de rede locais HTTP/REST (`http://127.0.0.1:8188`) e payloads JSON.
* **Compatibilidade Jurídica**: De acordo com a doutrina padrão da *Free Software Foundation (FSF)* e da *Open Source Initiative (OSI)*, a comunicação entre processos separados via API de rede e troca de dados estruturados (HTTP/JSON em "arm's length") não constitui agregação estática ou linkagem que transforme o cliente em obra derivada ("derivative work") do servidor. Dessa forma, o CineGen mantém legitimamente sua licença independente sob **Apache License 2.0**, enquanto o usuário final deve respeitar os termos da GPL-3.0 ao instalar e executar o ComfyUI em seu próprio ambiente.

### B. FFmpeg
* **Projeto Original**: [FFmpeg Project](https://ffmpeg.org)
* **Licença**: LGPL v2.1+ / GPL v2.0+ (conforme as opções de compilação do executável do usuário).
* **Relação com o CineGen**: Utilizado opcionalmente em scripts de concatenação e multiplexação de áudio/vídeo via execução de subprocessos de linha de comando (`subprocess.run`). O binário do FFmpeg não é distribuído no código-fonte do CineGen.

---

## 3. Arquiteturas de Modelos de Inteligência Artificial e Pesos

> [!NOTE]
> **Aviso Importante sobre Pesos de Modelos:** O repositório do CineGen contém **estritamente o código-fonte de engenharia, orquestração e scripts de automação**. Nenhum arquivo de peso neural, checkpoint binário (`.safetensors`, `.gguf`, `.ckpt`), tensor de quantização ou modelo pré-treinado é distribuído no repositório. O usuário final deve obter os modelos diretamente de seus mantenedores oficiais nos repositórios adequados (como o Hugging Face), sujeitando-se aos termos de cada licenciante.

As arquiteturas referenciadas nos workflows e scripts do CineGen incluem:

1. **FLUX.1 / FLUX.2 / FLUX.3 [klein]**
   - **Autor/Organização**: Black Forest Labs (BFL)
   - **Licenciamento do Modelo**: FLUX.1 [schnell] é licenciado sob Apache License 2.0; versões [dev] utilizam a FLUX.1 Non-Commercial License da BFL.
   - **Papel no CineGen**: Geração de quadros base fotorrealistas e multi-referência facial.

2. **Wan2.1 / Wan2.2 (Wan-Video)**
   - **Autor/Organização**: Wan-Video Team / Alibaba Cloud
   - **Licenciamento do Modelo**: Apache License 2.0.
   - **Papel no CineGen**: Arquitetura DiT de geração de movimento temporal I2V / T2V.

3. **Kandinsky 6.0 Lite**
   - **Autor/Organização**: Sber AI / FusionBrain
   - **Licenciamento do Modelo**: Apache License 2.0.
   - **Papel no CineGen**: Motor de difusão de vídeo ultraleve quantizado (INT8 / W4A4).

4. **Qwen2.5-VL / Qwen3-VL / Qwen 3.5**
   - **Autor/Organização**: Equipe Qwen / Alibaba Cloud
   - **Licenciamento do Modelo**: Apache License 2.0 / Qwen Community License.
   - **Papel no CineGen**: Raciocínio de cena, construção de prompts e encoders de visão-linguagem.

5. **HunyuanVideo VAE**
   - **Autor/Organização**: Tencent Holdings Limited
   - **Licenciamento**: Tencent Hunyuan Community License / Apache 2.0 para VAEs de decodificação de vídeo.

6. **2x-NomosUni SPAN**
   - **Autor/Organização**: Philip Hofmann / OpenModelDB
   - **Licenciamento**: CC-BY 4.0 / Permissiva para modelos de super-resolução.

---

## 4. Requisitos de Conformidade para Usuários e Desenvolvedores

Ao utilizar, compilar ou redistribuir o CineGen:
1. **Preserve os Avisos de Licença**: Os arquivos `LICENSE`, `NOTICE` e `THIRD_PARTY_LICENSES.md` devem acompanhar qualquer redistribuição do código-fonte.
2. **Ambiente ComfyUI Independente**: Certifique-se de configurar o ComfyUI em diretório próprio conforme a licença GPL-3.0 do autor original.
3. **Download Responsável de Modelos**: Baixe pesos e modelos apenas a partir de canais oficiais e confiáveis, respeitando as eventuais restrições comerciais ou não comerciais estabelecidas pelos criadores de cada modelo.
