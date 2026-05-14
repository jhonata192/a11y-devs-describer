# Gerenciador de Estado

- **Arquivo**: `bot/agents/state_manager.py`
- **Modelos**: Nenhum (Python puro)

## Quem sou

Sou o gerenciador de estado das tarefas. Acompanho o progresso, erros e resultados de cada processamento.

## Para que sirvo

Manter rastreabilidade de cada tarefa: saber em que etapa está, quanto tempo levou, se houve erro e qual foi o resultado.

## O que faço

- Gero um `task_id` único (8 chars) para cada tarefa
- Armazeno:
  - Nome do arquivo
  - Status: `processing` → `done` ou `error`
  - Progresso: 0.0 a 1.0
  - Etapa atual (ex: "Pré-análise", "Roteamento IA")
  - Lista de erros
  - Resultado final (string)
  - Timestamps de início e fim
- Forneço métodos para atualizar e consultar estado

## Uso

```python
from bot.agents.state_manager import state_manager

task_id = state_manager.criar_tarefa(file_path)
state_manager.atualizar(task_id, etapa="Pré-análise", progresso=0.1)
state_manager.atualizar(task_id, status="error", erro="Falha no OCR")
state = state_manager.obter(task_id)
```

## Notas

- Singleton: `state_manager` é instância única global
- Thread-safe para operações básicas (sem locks ainda)
- Pode ser extendido para persistência em disco/Redis
