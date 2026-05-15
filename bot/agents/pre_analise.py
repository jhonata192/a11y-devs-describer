import base64
from io import BytesIO
from pathlib import Path

from PIL import Image

from bot.utils.logger import logger


class PreAnalise:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._data: dict = {}

    async def analisar(self) -> dict:
        ext = self.file_path.suffix.lower()
        if ext == ".pdf":
            self._data = self._analisar_pdf()
        elif ext == ".docx":
            self._data = self._analisar_docx()
        elif ext == ".html":
            self._data = self._analisar_html()
        else:
            self._data = self._analisar_imagem()
        logger.info("Pre-analise concluida: {}", self._data)
        return self._data

    def _analisar_pdf(self) -> dict:
        import fitz

        doc = fitz.open(self.file_path)
        try:
            paginas = len(doc)
            texto_extraivel = 0
            total_chars = 0
            imagem_count = 0
            textos_paginas = []

            for i in range(min(paginas, 10)):
                page = doc[i]
                text = page.get_text()
                total_chars += len(text.strip())
                if text.strip():
                    texto_extraivel += 1
                    textos_paginas.append(text.strip())
                imagem_count += len(page.get_images())

            paginas_amostra = min(paginas, 10)
            if paginas_amostra > 0 and texto_extraivel > paginas_amostra * 0.3:
                texto_embutido = True
            else:
                texto_embutido = False

            densidade = "baixa"
            if paginas > 0:
                ratio = imagem_count / paginas
                if ratio >= 2:
                    densidade = "alta"
                elif ratio >= 0.5:
                    densidade = "media"

            return {
                "tipo": "pdf",
                "paginas": paginas,
                "texto_embutido": texto_embutido,
                "total_chars": total_chars,
                "possui_imagens": imagem_count > 0,
                "quantidade_imagens": imagem_count,
                "densidade_visual": densidade,
                "tamanho_bytes": self.file_path.stat().st_size,
                "texto_extraido": "\n\n".join(textos_paginas) if textos_paginas else "",
            }
        finally:
            doc.close()

    def _analisar_imagem(self) -> dict:
        with Image.open(self.file_path) as img:
            largura, altura = img.size
            modo = img.mode
            formato = img.format or self.file_path.suffix.lstrip(".").upper()

            proporcao = f"{largura // self._gcd(largura, altura)}:{altura // self._gcd(largura, altura)}"

            return {
                "tipo": "imagem",
                "formato": formato.lower(),
                "largura": largura,
                "altura": altura,
                "modo": modo,
                "proporcao": proporcao,
                "tamanho_bytes": self.file_path.stat().st_size,
                "texto_extraido": "",
            }

    def _analisar_docx(self) -> dict:
        from bot.utils.file_parsers import extract_text_from_docx
        text = extract_text_from_docx(self.file_path)
        return {
            "tipo": "docx",
            "tamanho_bytes": self.file_path.stat().st_size,
            "texto_embutido": True,
            "total_chars": len(text),
            "paginas": 1,
            "possui_imagens": False,
            "quantidade_imagens": 0,
            "densidade_visual": "baixa",
            "texto_extraido": text,
        }

    def _analisar_html(self) -> dict:
        from bot.utils.file_parsers import extract_text_from_html
        text = extract_text_from_html(self.file_path)
        return {
            "tipo": "html",
            "tamanho_bytes": self.file_path.stat().st_size,
            "texto_embutido": True,
            "total_chars": len(text),
            "paginas": 1,
            "possui_imagens": False,
            "quantidade_imagens": 0,
            "densidade_visual": "baixa",
            "texto_extraido": text,
        }

    @staticmethod
    def _gcd(a: int, b: int) -> int:
        while b:
            a, b = b, a % b
        return a
