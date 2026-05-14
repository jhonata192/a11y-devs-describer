# Arquitetura do Sistema — Bot Acess v3

Sistema de processamento de documentos com IA local para acessibilidade de pessoas cegas e com baixa visão.

---

## 1. Visão Geral

Bot Telegram que recebe documentos (PDF, imagens), extrai metadados estruturais via Python, decide o pipeline com roteador LLM (phi3:mini), descreve visualmente com moondream via Ollama, traduz para português com Qwen2.5:1.5b e exporta para DOCX, PDF e TXT acessíveis.

### Princípios

- **100% local** — sem APIs externas, sem dependência de nuvem
- **Arquitetura híbrida 3 camadas** — determinística + LLM roteador + executores fixos
- **Agentes modulares** — cada modelo de IA é um agente independente com `keep_alive=0`
- **Acessibilidade real** — audiodescrição em português de elementos visuais
- **Assíncrono** — processamento não bloqueante com asyncio

---

## 2. Arquitetura Híbrida (3 Camadas)

```
┌──────────────────────────────────────────────────────────────────┐
│                      Telegram Bot (aiogram)                       │
│                        interface única                            │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                    Agente Mestre (orquestrador)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  ┌───────┐ │
│  │ StateManager │  │ PreAnalise   │  │ RouterIA   │  │ Cache │ │
│  │ task_id,     │→ │ (Python)     │→ │ (phi3:mini)│→ │ SHA256│ │
│  │ progresso    │  │ JSON estru-  │  │ plano JSON │  │       │ │
│  │              │  │ tural        │  │            │  │       │ │
│  └──────────────┘  └──────────────┘  └─────┬──────┘  └───────┘ │
│                                            │                    │
│  ┌─────────────────────────────────────────▼──────────────────┐ │
│  │                     Policies Layer                          │ │
│  │  Regras: PDF sem texto → image_description obrigatório     │ │
│  │          Translation sempre presente                        │ │
│  └─────────────────────────────────────────┬──────────────────┘ │
│                                            │                    │
│  ┌─────────────────────────────────────────▼──────────────────┐ │
│  │                 PipelineExecutor                            │ │
│  │  ┌────────────────┐  ┌─────────────────┐  ┌──────────────┐  │ │
│  │  │ DescritorVisual │  │   OCRAgent      │  │   Tradutor   │  │ │
│  │  │ (moondream)     │  │ (Tesseract por) │→│ (qwen2.5:1.5b│  │ │
│  │  │ layout/visual   │  │ texto exato     │  │ )            │  │ │
│  │  │ keep_alive=0    │  │                 │  │ keep_alive=0 │  │ │
│  │  └────────────────┘  └─────────────────┘  └──────────────┘  │ │
│  │  Saida: descricao visual + OCR text combinados               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Fallback: pipeline com OCR (descritor + OCR + tradutor)          │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                       Exportadores                                │
│  ┌──────┐  ┌──────┐  ┌──────┐                                    │
│  │ DOCX │  │ PDF  │  │ TXT  │                                    │
│  └──────┘  └──────┘  └──────┘                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Agentes

### BaseAgent

Classe abstrata que encapsula chamadas à API Ollama com `keep_alive=0`.

```python
class BaseAgent:
    async def executar(entrada: str, is_image: bool = False) -> str
```

### Pré-Análise (Determinística — sem LLM)

- PyMuPDF + Pillow
- Extrai verdades estruturais: tipo, páginas, texto embutido, imagens, densidade
- Gera JSON que alimenta o roteador

### Roteador IA (phi3:mini)

- Recebe JSON da Pré-Análise
- Decide pipeline (`simple`, `detailed`, `full_accessibility`)
- Decide steps (`image_description`, `translation`, `summarize`)
- Decide nível de detalhe (`baixo`, `medio`, `alto`)

### Policies (regras fixas)

- PDF sem texto extraível SEMPRE ativa `image_description`
- Imagens e PDFs SEMPRE recebem step `ocr` (a menos que `image_description` ja esteja presente)
- Tradução SEMPRE presente (saída em português)
- detail_level inválido corrigido para `medio`

### DescritorVisual (moondream)

- Modelo de visão 1B params (~1.7GB)
- Prompt: descrição visual em português (APENAS layout, cores, logotipos — sem ler texto)
- Recebe imagem base64, retorna descrição visual em português
- `keep_alive=0` — descarregado da RAM após responder

### Tradutor (qwen2.5:1.5b)

- Modelo de linguagem 1.5B params (~900MB)
- Prompt: `"Traduza o texto abaixo para o português brasileiro..."`
- Pós-processamento: remove preâmbulos com `_clean_translation()`
- `keep_alive=0` — descarregado da RAM após responder

### OCRAgent (Tesseract OCR)

- Extrai texto REAL de imagens usando Tesseract OCR
- Idioma: português (`por`)
- DPI configurável (200/300 conforme detail_level)
- Processa PDFs página por página
- Resolve o problema de alucinação de texto do moondream

### State Manager

- Singleton que gerencia estado de cada tarefa
- task_id, status, progresso, erros, resultado

---

## 4. Modelos Ollama

| Modelo | Tamanho | Função | Carregado sob demanda |
|---|---|---|---|---|
| `llava:7b` | 4.7 GB | Visão (descreve layout/visuais + texto) | ✅ keep_alive=0 |
| Tesseract OCR | — | Extração de texto exato | ✅ nativo |
| `phi3:mini` | 2.2 GB | Roteador IA | ✅ keep_alive=0 |
| `qwen2.5:1.5b` | 986 MB | Tradutor EN→PT-BR | ✅ keep_alive=0 |

---

## 5. Cache

Cache SHA-256 em `temp/cache/` para evitar reprocessar o mesmo arquivo.

- TTL: 1 hora
- Chave: `hash_16primeiros_hibrido-v2`
- Invalidado automaticamente após expirar
- Fallback não usa cache

---

## 6. Exportadores

| Formato | Biblioteca | Status |
|---|---|---|
| DOCX | python-docx | ✅ Headings, parágrafos, formatação acessível |
| PDF | reportlab | ✅ Títulos, corpo, metadados |
| TXT | nativo | ✅ Texto puro UTF-8 |

---

## 7. Bot Telegram

### Handlers

| Handler | Função |
|---|---|
| `handle_document` | Recebe PDFs e imagens |
| `handle_photo` | Recebe fotos |
| `handle_start` | Comando /start |
| `handle_help` | Comando /ajuda |

---

## 8. Fluxo de Dados

### PDF / Imagem

```
Usuário envia arquivo
  → handle_document()
  → download_file()
  → agente_mestre.process()
      1. StateManager.criar_tarefa()
      2. PreAnalise.analisar()           # Python determinístico
      3. RouterIA.rotear(metadata)       # phi3:mini → plano JSON
      4. Policies.aplicar(plano, meta)   # regras de segurança
      5. PipelineExecutor.executar()     # moondream → qwen
      6. fallback se erro
      7. cache.save()
  → export_docx(), export_pdf(), export_txt()
  → enviar arquivos
```

---

## 9. Estrutura de Arquivos

```
/
├── bot/
│   ├── agents/
│   │   ├── __init__.py           # Exporta todos os agentes
│   │   ├── base.py               # BaseAgent (classe abstrata)
│   │   ├── descritor_visual.py   # Moondream
│   │   ├── tradutor.py           # Qwen2.5:1.5b + _clean_translation
│   │   ├── pre_analise.py        # PyMuPDF + Pillow (determinístico)
│   │   ├── router_ia.py          # phi3:mini (roteador LLM)
│   │   ├── pipeline_executor.py  # Executa steps do plano
│   │   ├── state_manager.py      # Gerência de estado das tarefas
│   │   ├── ocr_agent.py          # Tesseract OCR
│   │   └── policies.py           # Regras fixas de segurança
│   ├── agente_mestre.py          # Orquestrador central (3 camadas)
│   ├── handlers/
│   ├── services/
│   ├── exporters/
│   ├── utils/
│   ├── __init__.py
│   ├── __main__.py
│   └── main.py
├── agentes/
│   ├── mestre.md
│   ├── descritor-visual.md
│   ├── tradutor.md
│   ├── pre-analise.md
│   ├── router-ia.md
│   ├── pipeline-executor.md
│   ├── state-manager.md
│   └── policies.md
├── config/
│   └── settings.py
├── tests/
├── temp/ (cache/ + output/)
├── logs/
├── README.md
├── arquitetura.md
├── agente.md
├── .env
├── requirements.txt
└── run.py
```

---

## 10. Considerações de Acessibilidade

- **Audiodescrição**: toda imagem recebe descrição textual em português
- **Pipeline híbrido**: regras (Python) garantem consistência + LLM adapta linguagem
- **OCR + Visão**: moondream descreve layout/estrutura visual; Tesseract extrai texto exato — sem alucinações
- **Cabeçalhos**: níveis de heading preservados no DOCX e PDF
- **Idioma**: metadados pt-BR incluídos nos documentos gerados
- **Keep Alive 0**: modelos descarregados da RAM após uso, liberando memória
- **Fallback**: se o pipeline híbrido falhar, pipeline simples garante entrega
