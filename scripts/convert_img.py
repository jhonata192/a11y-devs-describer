import fitz

doc = fitz.open('paginas/pagina_001.pdf')
page = doc[0]
pix = page.get_pixmap(dpi=150)
pix.save('pagina_001.png')
doc.close()
print('Imagem salva como pagina_001.png')
