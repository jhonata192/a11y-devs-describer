# Bot Acess

Bot Telegram para conversão de documentos em formatos acessíveis para leitores de tela, com audiodescrição automática de imagens em português.

Arquitetura híbrida de 3 camadas: análise determinística (Python) + roteador IA (phi3:mini) + executores fixos (moondream + Qwen).

## Funcionalidades

- Recebe PDFs e imagens (png, jpg, tiff, bmp, gif, webp)
- Pré-análise estrutural automática (PyMuPDF + Pillow)
- Roteamento inteligente via phi3:mini (decide nível de detalhe, pipeline)
- Gera **audiodescrição** automática em português de imagens, gráficos e diagramas
- Políticas de segurança contra alucinação do LLM
- Fallback automático se o pipeline híbrido falhar
- Exporta para DOCX, PDF e TXT acessíveis
- 100% local, sem APIs externas
- Modelos carregados sob demanda (`keep_alive=0`)

## Requisitos

- Python 3.12+
- [Ollama](https://ollama.com) instalado
- Modelos: `llava:7b` (visão) + `phi3:mini` (roteador) + `qwen2.5:1.5b` (tradução)
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) instalado no PATH ou em `C:\Program Files\Tesseract-OCR`

## Instalação

### 1. Instalar Ollama

```
https://ollama.com/download
```

### 2. Baixar os modelos

```bash
ollama pull llava:7b
ollama pull phi3:mini
ollama pull qwen2.5:1.5b
```

### 3. Instalar dependências Python

```bash
pip install -r requirements.txt
```

### 4. Configurar

Copie `.env.example` para `.env` e configure o `BOT_TOKEN`.

### 5. Executar

```bash
python run.py
```

## Configuração

| Variável | Descrição | Padrão |
|---|---|---|
| `BOT_TOKEN` | Token do bot Telegram | obrigatório |
| `OLLAMA_URL` | URL do servidor Ollama | `http://localhost:11434` |
| `VISION_MODEL` | Modelo de visão (descrição visual) | `llava:7b` |
| `ROUTER_MODEL` | Modelo roteador | `phi3:mini` |
| `TRANSLATION_MODEL` | Modelo de tradução | `qwen2.5:1.5b` |
| `KEEP_ALIVE` | Keep alive dos modelos | `0` |
| `MAX_FILE_SIZE_MB` | Tamanho máximo de upload | 50 |
| `MAX_PAGES` | Número máximo de páginas | 50 |
| `OLLAMA_TIMEOUT` | Timeout por página (segundos) | 300 |
| `LOG_LEVEL` | Nível de logging | `INFO` |

## Estrutura

```
bot-acess/
├── bot/
│   ├── agents/           # Agentes (10 módulos)
│   ├── agente_mestre.py  # Orquestrador 3 camadas
│   ├── handlers/         # Comandos e mensagens
│   ├── exporters/        # DOCX, PDF, TXT
│   ├── services/         # Cache, file, cleanup
│   └── utils/            # Logger, validators
├── agentes/              # Docs dos agentes (9 .md)
├── config/               # Configurações
├── tests/                # Testes
├── temp/                 # Arquivos temporários
└── logs/                 # Logs
```

## Testes

```bash
pytest tests/
```
