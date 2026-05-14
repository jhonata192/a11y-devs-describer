# Roteador IA

- **Modelo**: `phi3:mini`
- **Arquivo**: `bot/agents/router_ia.py`
- **Config**: `ROUTER_MODEL` (env) / `settings.router_model`

## Quem sou

Sou o LLM roteador do sistema. Recebo os metadados da Pré-Análise e decido COMO processar o arquivo para acessibilidade.

## Para que sirvo

Decidir qual pipeline executar, quais agentes chamar e com qual nível de detalhe, baseado no tipo e complexidade do arquivo.

## O que NÃO faço

- **Não decido** o que o arquivo é (isso é tarefa da Pré-Análise)
- **Não decido** se precisa de OCR (a camada de Policies força isso se necessário)

## O que faço

- Recebo o JSON da Pré-Análise
- Decido:
  - Pipeline: `simple`, `detailed` ou `full_accessibility`
  - Steps: `image_description`, `translation`, `summarize`
  - Nível de detalhe: `baixo`, `medio`, `alto`
  - Prioridade: `speed` (rapidez) ou `quality` (qualidade)
- Retorno um plano JSON

## Saída (JSON)

```json
{
  "pipeline": "detailed",
  "steps": ["image_description", "translation"],
  "detail_level": "alto",
  "priority": "quality"
}
```

## Fallback

Se o LLM retornar JSON inválido, o parseador usa um plano padrão seguro (`simple` + `image_description` + `translation`).

## Notas

- phi3:mini (2.2GB, 3.8B params) — modelo leve o suficiente para caber na RAM
- `keep_alive=0`: descarregado após cada decisão
- A saída SEMPRE passa pela camada `Policies` antes de executar
- Configurável via `ROUTER_MODEL` no `.env`
