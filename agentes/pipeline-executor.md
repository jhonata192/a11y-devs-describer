# Executor de Pipeline

- **Arquivo**: `bot/agents/pipeline_executor.py`
- **Modelos**: Moondream (visão) + Qwen2.5:1.5b (tradução)

## Quem sou

Sou o executor de pipelines do sistema. Recebo um plano do Roteador IA (já filtrado pelas Policies) e executo os steps na ordem correta.

## Para que sirvo

Materializar o plano de acessibilidade: converter o arquivo em texto descritivo seguindo os steps definidos.

## O que faço

### Para PDFs:
- Itero páginas (até `MAX_PAGES`)
- Cada página → imagem (DPI ajustável: 200 para detalhe baixo/médio, 300 para alto)
- Cada imagem → `DescritorVisual` (moondream)
- Resultados parciais concatenados

### Para imagens:
- Arquivo → base64 → `DescritorVisual` (moondream)

### Pós-processo:
- Se step `translation`: chama `Tradutor` (qwen2.5:1.5b)
- Se step `summarize`: chama `Tradutor` com prompt de resumo

## Steps suportados

| Step | Agente | Descrição |
|---|---|---|
| `image_description` | `DescritorVisual` | Descrever cada imagem/página |
| `translation` | `Tradutor` | Traduzir EN→PT-BR |
| `summarize` | `Tradutor` | Resumir texto descritivo |

## Notas

- DPI de renderização de PDF varia com `detail_level` (200 ou 300)
- `keep_alive=0` garantido pelos agentes internos
- Se resultado final for vazio, o `agente_mestre` aciona fallback
