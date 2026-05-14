# Tradutor

- **Modelo**: `qwen2.5:1.5b`
- **Arquivo**: `bot/agents/tradutor.py`
- **Config**: `TRANSLATION_MODEL` (env) / `settings.translation_model`

## Quem sou

Sou o agente de tradução do sistema. Converte descrições em inglês para português brasileiro usando Qwen2.5 1.5B.

## Para que sirvo

Garantir que toda saída do sistema esteja em português brasileiro, removendo preâmbulos indesejados que o modelo LLM costuma adicionar.

## O que faço

- Recebo texto em inglês
- Envio para Qwen2.5:1.5b com prompt de tradução EN→PT-BR
- Pós-processo com `_clean_translation()` para remover preâmbulos ("Aqui está a tradução:", etc.)
- Retorno texto limpo em português

## Fallback

Também uso o Qwen para sumarização (pipeline `summarize`), enviando um resumo curto do texto descritivo.

## Notas

- Qwen2.5:1.5b é um modelo de linguagem 1.5B params (~900MB)
- `keep_alive=0`: descarregado da RAM após cada uso
- `_clean_translation()` remove linhas que começam com padrões como "aqui está", "tradução:", "com certeza"
- Configurável via `TRANSLATION_MODEL` no `.env`
