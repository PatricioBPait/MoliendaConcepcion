
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
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )

    respuesta.raise_for_status()

    soup = BeautifulSoup(respuesta.text, "html.parser")

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
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )

    respuesta.raise_for_status()

    texto = ""

    with pdfplumber.open(BytesIO(respuesta.content)) as pdf:
        for pagina in pdf.pages:
            texto += (pagina.extract_text() or "") + "\n"

    return texto


def numero(valor):
    """
    Convierte valores como:
    19.112 -> 19112
    859.628 -> 859628
    """
    valor = valor.strip()

    if valor in ("-", ""):
        return None

    valor = valor.replace(".", "").replace(",", ".")

    try:
        return int(float(valor))
    except ValueError:
        return None


def extraer_concepcion(texto):

    lineas = texto.splitlines()

    # ---------------------------------------------------------
    # 1. Encontrar el encabezado de CAÑA MOLIDA BRUTA
    # ---------------------------------------------------------

    indice_encabezado = None

    for i, linea in enumerate(lineas):

        if "Fecha" in linea and "Concepción" in linea and "Cruz Alta" in linea:

            # Nos interesa el bloque que corresponde a
            # "Caña molida bruta (t)"
            bloque = "\n".join(lineas[max(0, i - 5):i + 3])

            if "Caña molida bruta" in bloque:
                indice_encabezado = i
                break

    if indice_encabezado is None:
        raise Exception(
            "No se encontró la tabla de Caña molida bruta"
        )

    print("Encabezado encontrado en línea:", indice_encabezado)

    # ---------------------------------------------------------
    # 2. Buscar todas las filas con fecha
    # ---------------------------------------------------------

    registros = []

    patron_fecha = re.compile(r"^\d{2}/\d{2}/\d{4}$")

    for linea in lineas:

        columnas = linea.split()

        if not columnas:
            continue

        if not patron_fecha.match(columnas[0]):
            continue

        # En esta tabla:
        #
        # Fecha
        # Aguilares
        # Bella Vista
        # Concepción
        # Cruz Alta
        #
        # Por lo tanto Concepción = índice 3
        if len(columnas) <= 3:
            continue

        fecha = columnas[0]

        valor_concepcion = numero(columnas[3])

        if valor_concepcion is not None:
            registros.append(
                {
                    "fecha": fecha,
                    "molienda": valor_concepcion
                }
            )

    if not registros:
        raise Exception(
            "No se encontraron datos de molienda para Concepción"
        )

    # ---------------------------------------------------------
    # 3. Tomar el último día que tenga un valor válido
    # ---------------------------------------------------------

    ultimo = registros[-1]

    fecha_ultimo = ultimo["fecha"]
    molienda = ultimo["molienda"]

    print("Última fecha con datos:", fecha_ultimo)
    print("Molienda Concepción:", molienda)

    # ---------------------------------------------------------
    # 4. Buscar TOTAL ZAFRA
    # ---------------------------------------------------------

    acumulada = None

    for i, linea in enumerate(lineas):

        if linea.startswith("Total zafra"):

            columnas = linea.split()

            # Total zafra
            # Aguilares
            # Bella Vista
            # Concepción
            #
            # Índice 3 = Concepción

            if len(columnas) > 3:

                acumulada = numero(columnas[3])

                if acumulada is not None:
                    break

    if acumulada is None:
        raise Exception(
            "No se encontró el acumulado de zafra de Concepción"
        )

    print("Acumulado Concepción:", acumulada)

    return {
        "fecha": fecha_ultimo,
        "molienda": molienda,
        "acumulada": acumulada
    }


# -------------------------------------------------------------
# PROGRAMA PRINCIPAL
# -------------------------------------------------------------

pdf = obtener_pdf()

if not pdf:
    raise Exception("No se encontró PDF del IPAAT")

print("PDF encontrado:")
print(pdf)


texto = leer_pdf(pdf)


datos = extraer_concepcion(texto)


salida = {
    "ingenio": "Concepción",
    "fecha": datos["fecha"],
    "molienda_diaria": datos["molienda"],
    "molienda_acumulada": datos["acumulada"],
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


print("")
print("===================================")
print(" ACTUALIZADO CORRECTAMENTE")
print("===================================")
print("Ingenio:", salida["ingenio"])
print("Fecha:", salida["fecha"])
print("Molienda diaria:", salida["molienda_diaria"])
print("Molienda acumulada:", salida["molienda_acumulada"])
print("Hora actualización:", salida["actualizado"])
print("===================================")
