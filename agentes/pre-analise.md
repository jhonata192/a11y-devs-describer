# Pré-Análise

- **Arquivo**: `bot/agents/pre_analise.py`
- **Modelos**: Nenhum (100% Python, sem LLM)

## Quem sou

Sou a camada determinística do sistema. Uso PyMuPDF e Pillow para extrair "verdades estruturais" do arquivo — dados objetivos que não dependem de IA.

## Para que sirvo

Fornecer ao Roteador IA (phi3:mini) metadados confiáveis sobre o arquivo, evitando que o LLM alucine sobre o tipo ou estrutura do conteúdo.

## O que faço

### Para PDFs:
- Número de páginas
- Detecto se há texto extraível embutido (amostragem das primeiras 10 páginas)
- Conto imagens por página
- Calculo densidade visual (baixa/média/alta baseada na proporção imagem/página)
- Tamanho do arquivo em bytes

### Para imagens:
- Formato (PNG, JPEG, etc.)
- Dimensões (largura × altura)
- Modo de cor (RGB, CMYK, etc.)
- Proporção de aspecto simplificada (ex: "16:9")
- Tamanho do arquivo em bytes

## Saída (JSON)

```json
{
  "tipo": "pdf",
  "paginas": 120,
  "texto_embutido": false,
  "total_chars": 0,
  "possui_imagens": true,
  "quantidade_imagens": 45,
  "densidade_visual": "alta",
  "tamanho_bytes": 5242880
}
```

## Notas

- PyMuPDF (fitz) para análise de PDF
- Pillow (PIL) para análise de imagem
- Amostragem limitada a 10 páginas para performance
- Texto embutido = verdadeiro se >30% das páginas amostradas têm texto extraível
