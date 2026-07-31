import requests
import pdfplumber
import re
import json
from datetime import datetime
from io import BytesIO

URL_PDF = "https://www.ipaat.gov.ar/storage/notas/July2026/A9vKucc3vL49pGV3unK3.pdf"

# Descargar PDF
respuesta = requests.get(
    URL_PDF,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

respuesta.raise_for_status()

print("Tipo de archivo:", respuesta.headers.get("Content-Type"))
print("Primeros bytes:", respuesta.content[:20])
texto = ""

# Leer PDF
with pdfplumber.open(BytesIO(respuesta.content)) as pdf:
    for pagina in pdf.pages:
        texto += pagina.extract_text() or ""

print(texto)

# Buscar Concepción
patron = r"Concepción\s+(\d+)\s+(\d+)"

resultado = re.search(patron, texto, re.IGNORECASE)

if resultado:

    molienda = int(resultado.group(1))
    acumulada = int(resultado.group(2))

    datos = {
        "ingenio": "Concepción",
        "fecha": datetime.now().strftime("%d/%m/%Y"),
        "molienda_diaria": molienda,
        "molienda_acumulada": acumulada,
        "actualizado": datetime.now().strftime("%H:%M")
    }

    with open("data.json", "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=2, ensure_ascii=False)

    print("Actualizado:", datos)

else:
    print("No se encontró Concepción")
