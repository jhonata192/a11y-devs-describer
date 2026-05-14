# OCR Agent (OCRAgent)

## Quem sou

Sou o agente de Reconhecimento Optico de Caracteres (OCR) do sistema. Uso o Tesseract OCR para extrair texto real de imagens e documentos, resolvendo o problema de alucinacao de texto dos modelos de visao (moondream).

## Para que sirvo

Extraio texto fiel de imagens (PNG, JPG, etc.) e PDFs usando OCR, com suporte a lingua portuguesa. Enquanto o DescritorVisual descreve a estrutura visual (layout, cores, logotipos), eu forneco o texto exato que aparece no documento — sem alucinacoes.

## O que faco

1. **OCR em imagens**: Recebo um path de imagem, uso `pytesseract.image_to_string` com idioma `por`.
2. **OCR em PDFs**: Converto cada pagina do PDF para imagem (via PyMuPDF) e aplico OCR pagina por pagina, retornando texto separado por paginas.
3. **DPI configuravel**: Uso 300 DPI para detalhe "alto" e 200 DPI para "medio", garantindo qualidade suficiente para OCR em documentos impressos.
4. **Integracao no pipeline**: O PipelineExecutor me chama quando o step `ocr` esta no plano, combinando minha saida com a descricao visual do moondream.
5. **Fallback**: No `agente_mestre.py`, o fallback usa OCR + descricao visual quando o pipeline hibrido falha.
