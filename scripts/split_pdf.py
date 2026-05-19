import sys
import os

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("Instalando pypdf...")
    os.system("pip install pypdf")
    from pypdf import PdfReader, PdfWriter

pdf_path = r"C:\Users\JHONATA\teste\Grandezas e Medidas_cópia.pdf"
output_dir = r"C:\Users\JHONATA\teste\paginas"

os.makedirs(output_dir, exist_ok=True)

reader = PdfReader(pdf_path)
total_pages = len(reader.pages)
print(f"PDF tem {total_pages} páginas")

for i in range(total_pages):
    writer = PdfWriter()
    writer.add_page(reader.pages[i])
    output_path = os.path.join(output_dir, f"pagina_{i+1:03d}.pdf")
    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"Salvo: {output_path}")

print(f"\nConcluído! {total_pages} páginas salvas em: {output_dir}")
