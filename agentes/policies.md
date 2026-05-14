# Políticas

- **Arquivo**: `bot/agents/policies.py`
- **Modelos**: Nenhum (Python puro)

## Quem sou

Sou a camada de regras fixas do sistema. Fico entre o Roteador IA e o Executor de Pipeline para garantir que decisões críticas nunca sejam ignoradas pelo LLM.

## Para que sirvo

Evitar alucinações do LLM roteador. Decisões estruturais (como "PDF sem texto precisa de descrição visual") são regras duras que o LLM não pode quebrar.

## O que faço

### Regra 1: PDF sem texto extraível SEMPRE descrever
Se o PDF não tem texto embutido e `image_description` não está nos steps, ela é adicionada. O pipeline sobe para `detailed` e detail_level nunca fica `baixo`.

### Regra 2: Tradução SEMPRE presente
Se `translation` não está nos steps, é adicionada. A saída final deve estar SEMPRE em português brasileiro.

### Regra 3: detail_level sanitizado
Se o valor for inválido (diferente de `baixo`, `medio`, `alto`), cai para `medio`.

## Exemplo

```python
plan = {"pipeline": "simple", "steps": ["translation"], "detail_level": "baixo"}
meta = {"tipo": "pdf", "texto_embutido": False, "paginas": 5}

# Após políticas:
# {"pipeline": "detailed", "steps": ["image_description", "translation"],
#  "detail_level": "medio", "priority": "speed"}
```

## Notas

- Aplicado APÓS o Router IA, ANTES do Pipeline Executor
- Não modifica o metadata original
- pipeline pode ser alterado de `simple` para `detailed` se regras exigirem
