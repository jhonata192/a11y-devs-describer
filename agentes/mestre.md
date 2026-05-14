# Agente Mestre

- **Arquivo**: `bot/agente_mestre.py`
- **Modelos**: Nenhum (orquestrador não usa LLM diretamente)

## Quem sou

Sou o orquestrador central do sistema. Coordeno as 3 camadas da arquitetura híbrida: pré-análise determinística, roteamento IA e execução do pipeline.

## Para que sirvo

Coordenar o fluxo completo de processamento de um arquivo enviado pelo usuário, garantindo consistência, fallback em caso de erro e cache de resultados.

## O que faço

1. Crio uma tarefa no `StateManager` com ID único
2. Chamo `PreAnalise` para extrair verdades estruturais (Python, sem LLM)
3. Chamo `RouterIA` (phi3:mini) para decidir COMO processar
4. Aplico `Policies` para garantir regras de segurança
5. Executo o pipeline via `PipelineExecutor`
6. Se algo falhar, executo um fallback simples (descritor → tradutor)
7. Salvo resultado em cache

## Fluxo

```
agente_mestre.process(arquivo)
  → StateManager.criar_tarefa()
  → PreAnalise.analisar()          # JSON estrutural
  → RouterIA.rotear(metadata)       # plano JSON
  → Policies.aplicar(plano, meta)   # regras de segurança
  → PipelineExecutor.executar()     # executa agentes
  → fallback se erro
  → cache.save()
```

## Cache

- Versão: `hibrido-v1`
- Cache por hash do arquivo + versão
- Fallback não usa cache (resultado de emergência)
