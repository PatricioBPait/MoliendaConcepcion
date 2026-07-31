import requests
import pdfplumber
import re
import json
from datetime import datetime
from io import BytesIO
from bs4 import BeautifulSoup


PAGINA_IPAAT = "https://www.ipaat.gov.ar/nota/86/parte-diario-de-produccion"


def obtener_pdf():

    respuesta = requests.get(
        PAGINA_IPAAT,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    respuesta.raise_for_status()

    soup = BeautifulSoup(respuesta.text, "html.parser")
    print(respuesta.text[:2000])

    enlaces = soup.find_all("a", href=True)

    for enlace in enlaces:
        url = enlace["href"]

        if ".pdf" in url.lower():

            if url.startswith("/"):
                url = "https://www.ipaat.gov.ar" + url

            return url

    return None


def leer_pdf(url_pdf):

    respuesta = requests.get(
        url_pdf,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    respuesta.raise_for_status()

    texto = ""

    with pdfplumber.open(BytesIO(respuesta.content)) as pdf:

        for pagina in pdf.pages:
            texto += pagina.extract_text() or ""

    return texto


def extraer_concepcion(texto):

    patron = r"Concepción\s+(\d+)\s+(\d+)"

    resultado = re.search(
        patron,
        texto,
        re.IGNORECASE
    )

    if resultado:

        return (
            int(resultado.group(1)),
            int(resultado.group(2))
        )

    return None


# --- PROGRAMA PRINCIPAL ---

pdf = obtener_pdf()

if not pdf:
    raise Exception("No se encontró PDF del IPAAT")


print("PDF encontrado:")
print(pdf)


texto = leer_pdf(pdf)
print(texto[:5000])


datos = extraer_concepcion(texto)


if not datos:
    raise Exception("No se encontró Ingenio Concepción")


molienda, acumulada = datos


salida = {

    "ingenio": "Concepción",

    "fecha": datetime.now().strftime("%d/%m/%Y"),

    "molienda_diaria": molienda,

    "molienda_acumulada": acumulada,

    "actualizado": datetime.now().strftime("%H:%M")

}


with open(
    "data.json",
    "w",
    encoding="utf-8"
) as archivo:

    json.dump(
        salida,
        archivo,
        indent=2,
        ensure_ascii=False
    )


print("Actualizado correctamente")
print(salida)
