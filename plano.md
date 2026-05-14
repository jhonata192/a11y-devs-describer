Boa — isso aqui é exatamente o tipo de decisão de arquitetura que muda o jogo do teu projeto.
Vou te responder direto, mas já te adianto: as duas abordagens são válidas, mas servem objetivos diferentes. E no teu caso (acessibilidade + PDFs complexos + múltiplos modelos), tem uma opção que costuma ficar bem mais robusta.
 
🧠 1. Hoje você tem um “mestre determinístico”
Seu agente_mestre.py atual é basicamente:
• 
detecta tipo (PDF/imagem)
• 
segue pipeline fixo:
• 
descritor → tradutor
Isso é:
✔ rápido
✔ previsível
✔ fácil de debugar
❌ pouco flexível
❌ não escala bem para casos complexos (livro, gráfico, tabela, layout híbrido)
 
🤖 2. A ideia do “Agente IA roteador”
O que você está propondo é:
“um LLM decide qual pipeline usar”
Exemplo:
input: “PDF escaneado com 20 páginas, contém tabelas e imagens”
→ LLM decide:
• 
usar OCR pesado?
• 
dividir em chunks?
• 
usar modelo de visão?
• 
só descrição?
• 
pipeline híbrido?
Isso vira:
agente_mestre.py → LLM router → executa agentes
✔ muito flexível
✔ escalável
✔ adaptável a documentos novos
❌ pode errar rota
❌ precisa de guardrails
❌ mais lento e mais caro
 
⚖️ O ponto crítico (onde muita gente erra)
Se você deixar 100% da decisão para o LLM, você cria um problema:
“o roteador pode alucinar a estratégia”
Exemplo clássico:
• 
PDF com imagem escaneada
• 
LLM acha que é “texto puro”
• 
pula OCR
• 
resultado vira lixo
Isso é grave em acessibilidade.
 
🧩 Melhor arquitetura (recomendada pra teu caso)
O ideal não é escolher um OU outro.
É:
🏗️ Arquitetura híbrida (RECOMENDADA)
1. Camada determinística (pré-análise)
Python faz:
• 
tipo de arquivo (PDF/imagem)
• 
se PDF tem texto embutido ou é escaneado
• 
número de páginas
• 
presença de imagens (heurística)
• 
tamanho / complexidade
👉 isso é “verdade estrutural”
 
2. Camada LLM roteadora (decisão semântica)
Aí sim entra o modelo (Qwen 1.5B, etc):
Ele decide coisas como:
• 
“precisa descrição detalhada ou resumida?”
• 
“usar linguagem simples ou técnica?”
• 
“priorizar acessibilidade total ou síntese?”
• 
“gerar audiodescrição por imagem ou por página?”
👉 isso é “interpretação”
 
3. Executor fixo (seus agentes)
Depois:
• 
descritor de imagem
• 
OCR engine
• 
tradutor
• 
resumidor
• 
estruturador acessível
 
🧠 Em uma frase:
❌ LLM não decide “o que é o arquivo”
✅ LLM decide “como explicar o arquivo”
 
🔥 Por que isso é perfeito para acessibilidade
Porque documentos acessíveis exigem:
• 
consistência
• 
previsibilidade
• 
zero erro estrutural (OCR errado é crítico)
Mas também exigem:
• 
adaptação de linguagem
• 
descrição contextual inteligente
• 
sensibilidade ao tipo de conteúdo
👉 ou seja: mistura de regra + inteligência
 
🧪 Exemplo real de fluxo
PDF escaneado de livro
1. Python detecta:
• 
PDF
• 
sem texto embutido
• 
120 páginas
• 
muitas imagens
2. LLM roteador responde:
JSON
Copiar
{
  "pipeline": "deep_accessibility",
  "steps": [
    "ocr_per_page",
    "image_description_high_detail",
    "summarize_per_chapter",
    "generate_accessible_structure"
  ]
}
3. executor roda agentes
 
🚨 E sobre “só documentar como IA”
Isso é mais fraco.
Se você só disser:
“o mestre é um agente IA”
sem mudar arquitetura real:
❌ não melhora inteligência
❌ não melhora roteamento
❌ só é semântico, não funcional
 
🧭 Minha recomendação final (bem direta)
👉 NÃO escolha entre os dois extremos.
Faça isso:
✔ mestre híbrido:
• 
Python: decisões estruturais (seguras)
• 
LLM: decisões semânticas (inteligentes)
• 
agentes: execução fixa e confiável
 
💡 Se quiser evoluir ainda mais (nível profissional mesmo)
Você pode adicionar:
• 
cache de decisões de roteamento
• 
“policy layer” (regras que o LLM nunca quebra)
• 
fallback deterministic pipeline se LLM falhar
• 
logs de decisão (debug de IA)

🏗️ Arquitetura Completa — Sistema de Acessibilidade Inteligente para Telegram
Seu projeto pode ficar parecido com uma plataforma profissional de processamento acessível multimodal.
A ideia central:
transformar conteúdos inacessíveis em conteúdos acessíveis para pessoas cegas ou baixa visão usando múltiplos agentes especializados.
 
🌐 Visão Geral da Arquitetura
Copiar
Telegram Bot
     ↓
Gateway de Entrada
     ↓
Agente Mestre (Orquestrador)
     ↓
Pré-Análise Estrutural
     ↓
Router IA (LLM)
     ↓
Pipeline Dinâmico de Agentes
     ↓
Pós-processamento
     ↓
Entrega Acessível ao Usuário
 
🧩 1. Telegram Gateway
Responsável por:
• 
receber:
• 
imagens
• 
PDFs
• 
EPUBs
• 
DOCX
• 
screenshots
• 
documentos escaneados
• 
baixar arquivos
• 
validar tamanho/formato
• 
criar ID único da tarefa
• 
enviar para fila
• 
devolver o conteudo acessivel.
 
Estrutura sugerida
Copiar
telegram/
├── bot.py
├── handlers/
├── commands/
├── middleware/
└── downloads/
 
🧠 2. Agente Mestre (Orquestrador)
Esse é o cérebro operacional.
Ele NÃO deve fazer IA pesada diretamente.
Ele coordena.
 
Responsabilidades
✔ controlar fluxo
✔ chamar agentes
✔ gerenciar estado
✔ carregar/descarregar modelos Ollama
✔ monitorar memória/RAM/VRAM
✔ aplicar fallback
 
Estrutura
Copiar
core/
├── agente_mestre.py
├── router.py
├── state_manager.py
├── pipeline_executor.py
├── model_manager.py
└── policies.py
 
🔍 3. Pré-Análise Estrutural (Determinística)
Essa camada é CRÍTICA.
Ela deve usar Python puro + libs.
NÃO LLM.
 
Objetivo
Extrair “verdades técnicas” do arquivo.
 
Exemplos
PDF
• 
tem texto embutido?
• 
é escaneado?
• 
quantas páginas?
• 
possui imagens?
• 
contém tabelas?
• 
resolução ruim?
• 
idioma detectado?
Imagem
• 
screenshot?
• 
documento?
• 
quadrinho?
• 
gráfico?
• 
fotografia?
• 
meme?
• 
baixa qualidade?
 
Ferramentas possíveis
• 
PyMuPDF
• 
pdfplumber
• 
Pillow
• 
OpenCV
• 
Tesseract
• 
OCRmyPDF
 
Resultado
Gera um JSON estruturado:
JSON
Copiar
{
  "tipo": "pdf",
  "paginas": 120,
  "texto_embutido": false,
  "possui_imagens": true,
  "densidade_visual": "alta",
  "idioma": "pt-br"
}
 
🤖 4. Router IA (LLM Decision Layer)
Agora entra o LLM.
Esse agente decide:
“qual estratégia de acessibilidade usar”
 
NÃO decide:
• 
se é PDF
• 
se precisa OCR
Isso é estrutural.
 
Decide:
• 
nível de detalhe
• 
quais agentes usar
• 
ordem
• 
profundidade
• 
simplificação
• 
resumo
• 
descrição longa/curta

🧠 Modelos ideais para Router
Leves e rápidos:
• 
Alibaba Cloud Qwen2.5 1.5B
• 
Phi-3 Mini
• 
Gemma 2B
• 
TinyLlama

🧾 Prompt do Router
Exemplo:
Copiar
Você é um roteador de acessibilidade.

OBJETIVO:
Transformar conteúdos inacessíveis em conteúdo acessível.

METADADOS:
- tipo: pdf
- paginas: 120
- texto_embutido: false
- possui_imagens: true

Decida:
1. pipeline
2. agentes necessários
3. nível de detalhamento
4. prioridade

Responda em JSON.
 
📦 5. Pipeline Executor
Recebe o plano do Router IA.
Executa cada agente.
 
Exemplo
JSON
Copiar
{
  "pipeline": "deep_accessibility",
  "steps": [
    "ocr",
    "layout_analysis",
    "image_description",
    "translation",
    "accessible_formatting"
  ]
}
 
👁️ 6. Agentes Especializados
Aqui fica o poder do sistema.
 
📄 OCR Agent
Responsável por:
• 
OCR pesado
• 
limpeza
• 
deskew
• 
contraste
• 
reconstrução textual
 
Ferramentas
• 
Tesseract
• 
PaddleOCR
• 
EasyOCR
• 
Surya OCR
 
🖼️ Vision Agent
Descreve:
• 
imagens
• 
gráficos
• 
diagramas
• 
expressões matemáticas
• 
layouts
• 
quadrinhos

Modelos possíveis
• 
Moondream
• 
Qwen2.5-VL
• 
MiniCPM-V
• 
InternVL
• 
LLaVA

📚 Document Understanding Agent
Entende:
• 
capítulos
• 
seções
• 
hierarquia
• 
estrutura lógica
 
🌎 Translation Agent
Traduz:
• 
descrições
• 
OCR
• 
tabelas
• 
conteúdo híbrido

Modelos
• 
NLLB
• 
MarianMT
• 
Qwen
🧠 Summarizer Agent
Gera:
• 
resumo acessível
• 
síntese por página
• 
resumo por capítulo
 
🎧 Accessibility Agent
Esse é o diferencial.
Ele adapta conteúdo para cegos.
 
Exemplo
Imagem original:
“gráfico de barras”
Descrição acessível:
“o gráfico compara crescimento entre 2020 e 2025. O maior crescimento ocorre em…”
 
🧱 7. Model Manager (Ollama)
Muito importante.
 
Responsabilidades
✔ carregar modelos
✔ descarregar modelos
✔ controlar keep_alive
✔ evitar estouro de RAM
✔ cache de modelos
 
Estratégia ideal
modelos leves:
keep_alive longo
modelos pesados:
load sob demanda
 
Exemplo
Python
Copiar
Executar código
load_model("qwen2.5-vl")
run_task()
unload_model()
 
🧠 8. State Manager
Mantém contexto da tarefa.
 
Guarda:
• 
progresso
• 
páginas processadas
• 
erros
• 
resultados parciais
• 
logs
• 
cache
 
Exemplo
JSON
Copiar
{
  "task_id": "abc123",
  "status": "processing",
  "current_page": 15,
  "pipeline": "deep_accessibility"
}
 
🛡️ 9. Policy Layer (MUITO IMPORTANTE)
Evita decisões ruins do LLM.
 
Exemplo
regra:
PDF escaneado SEMPRE executa OCR
Mesmo se LLM disser que não precisa.
 
Isso evita:
• 
alucinação
• 
erro crítico
• 
pipeline quebrado
 
🔁 10. Fallback System
Se um agente falhar:
• 
troca modelo
• 
reduz qualidade
• 
tenta outro OCR
• 
muda pipeline
 
Exemplo
Copiar
Qwen2.5-VL falhou
↓
fallback → Moondream

Pode usar
• 
Redis Queue
• 
Celery
• 
asyncio queue

Benefícios
• 
múltiplos usuários
• 
paralelismo
• 
controle de carga
 
📤 12. Pós-Processamento
Transforma saída em conteúdo acessível.
 
Pode gerar
• 
TXT
• 
HTML acessível
• 
Markdown
• 
EPUB acessível
• 
DOCX acessível
• 
PDF 

📱 13. Entrega Telegram
O usuário recebe:
• 
descrição
• 
documento convertido
• 
progresso
• 
resumo

🧠 Fluxo Completo Real
Copiar
Usuário envia PDF
        ↓
Gateway baixa arquivo
        ↓
Agente Mestre cria tarefa
        ↓
Pré-análise detecta:
- PDF escaneado
- 50 páginas
- imagens complexas
        ↓
Router IA escolhe pipeline
        ↓
Executor chama:
- OCR
- Vision
- Accessibility
- Summary
        ↓
Pós-processamento
        ↓
Entrega acessível
 
🔥 O GRANDE DIFERENCIAL DO TEU PROJETO
A maioria dos sistemas faz:
OCR → texto cru
Você está indo para:
compreensão acessível multimodal
Isso é MUITO mais avançado.
Você está basicamente criando:
• 
leitor universal acessível
• 
interpretação multimodal
• 
descrição inteligente contextual
• 
reconstrução acessível de documentos
 
🧭 Minha recomendação técnica final
✔ Use:
• 
roteamento híbrido
• 
regras determinísticas
• 
LLM apenas para semântica
• 
agentes especializados pequenos
• 
modelos carregados sob demanda
