"""Validate safe areas and export paired 300 dpi PNGs with bundled PDFium."""
import argparse, json, shutil
from pathlib import Path
import pdfplumber
import pypdfium2 as pdfium

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    root = parser.parse_args().output
    manifest = json.loads((root / "print-manifest.json").read_text(encoding="utf8"))
    with pdfplumber.open(root / "cartas-mpc.pdf") as pdf:
        if len(pdf.pages) != len(manifest["pages"]) or len(pdf.pages) % 2:
            raise ValueError("Las caras deben formar pares completos y coincidir con el manifiesto.")
        for i, page in enumerate(pdf.pages):
            if abs(page.width - 431.28) > .01 or abs(page.height - 269.28) > .01:
                raise ValueError("Tamano de pagina incorrecto")
            for char in page.chars:
                if char["text"].strip() and (char["x0"] < 17.18 or char["x1"] > 414.1 or char["top"] < 17.18 or char["bottom"] > 252.1):
                    raise ValueError(f"Texto fuera del area segura: pagina {i+1}")
    mpc = root / "mpc"
    mpc.mkdir(exist_ok=True)
    pdf = pdfium.PdfDocument(root / "cartas-mpc.pdf")
    try:
        for i, entry in enumerate(manifest["pages"]):
            page = pdf[i]
            bitmap = page.render(scale=300/72)
            try:
                image = bitmap.to_pil()
                if image.size != (1797, 1122): raise ValueError(f"Dimensiones PNG incorrectas: {image.size}")
                name = f"{i//2+1:03d}-" + ("front" if i % 2 == 0 else "back") + ".png"
                image.save(mpc / name, dpi=(300, 300))
                entry["uploadFile"] = name
            finally:
                bitmap.close()
                page.close()
    finally:
        pdf.close()
    (mpc / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf8")
    (mpc / "LEEME.txt").write_text(
        "MPC Large Landscape: corte 5.75 x 3.5 pulgadas (146.05 x 88.9 mm).\n"
        "PNG con sangrado: 1797 x 1122 px, 300 ppp. Emparejar 001-front con 001-back, etc.\n"
        "No rotar ni recortar. Puede haber cartas complementarias. Revisar la previsualizacion de MPC.\n"
        "Espirales originales: 1-2 Mind (azul), 3-4 Body (rojo), 5-6 Spirit (verde).\n",
        encoding="utf8",
    )
    shutil.make_archive(str(root / "cartas-mpc"), "zip", mpc)
    print("Verificadas y exportadas", len(manifest["pages"]), "caras")
if __name__ == "__main__": main()
