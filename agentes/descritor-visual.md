# Descritor Visual

- **Modelo**: `llava:7b`
- **Arquivo**: `bot/agents/descritor_visual.py`
- **Config**: `VISION_MODEL` (env) / `settings.vision_model`

## Quem sou

Sou o agente especializado em descrever elementos visuais de imagens. Uso o modelo LLaVA 7B (~4.7GB) para gerar descrições detalhadas em português.

## Para que sirvo

Converter imagens (PNG, JPG, páginas de PDF convertidas) em texto descritivo visual. Descrevo APENAS a estrutura visual (layout, cores, logotipos, posicionamento) — a leitura de texto fica por conta do OCR Agent.

## O que faço

- Recebo uma imagem em base64
- Envio para o LLaVA 7B com prompt detalhado em português (~800 chars)
- Retorno a descrição visual em português (sem ler texto)
- `keep_alive=0`: modelo descarregado da RAM após responder

## Notas

- LLaVA 7B é significativamente melhor que moondream em descrever documentos com precisão
- Usa swap de memória se necessário (modelo ~4.7GB, RAM disponível ~1.55GB)
- O prompt foca exclusivamente em elementos visuais: estrutura, cores, logotipos, iluminação
- Texto exato é extraído separadamente pelo OCR Agent (Tesseract)
- Configurável via `VISION_MODEL` no `.env`
