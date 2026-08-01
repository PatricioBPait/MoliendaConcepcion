
import requests
import pdfplumber
import re
import json
from datetime import datetime
from io import BytesIO


# ============================================================
# PDF DEL IPAAT
# ============================================================

URL_PDF = (
    "https://www.ipaat.gov.ar/storage/notas/July2026/"
    "Eq2hviytlfh0CSduXaIO.pdf"
)


# ============================================================
# DESCARGAR PDF
# ============================================================

def descargar_pdf():

    print("Descargando PDF del IPAAT...")
    print(URL_PDF)
respuesta = requests.get(
    URL_PDF,
    headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/pdf,*/*",
        "Referer": "https://www.ipaat.gov.ar/"
    },
    timeout=60,
    allow_redirects=True
)

respuesta.raise_for_status()

print("URL final:", respuesta.url)
print("Content-Type:", respuesta.headers.get("Content-Type"))
print("Tamaño:", len(respuesta.content))

if not respuesta.content.startswith(b"%PDF"):
    print("Contenido recibido no comienza con %PDF")
    print(respuesta.content[:200])
    raise Exception("IPAAT no devolvió un PDF válido")    
    respuesta.raise_for_status()

    print("PDF descargado correctamente.")
    print("Tamaño:", len(respuesta.content), "bytes")

    return respuesta.content


# ============================================================
# EXTRAER TEXTO DEL PDF
# ============================================================

def extraer_texto(pdf_bytes):

    texto = ""

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:

        print("Cantidad de páginas:", len(pdf.pages))

        for numero_pagina, pagina in enumerate(pdf.pages, start=1):

            contenido = pagina.extract_text() or ""

            print(
                "Página",
                numero_pagina,
                "- caracteres:",
                len(contenido)
            )

            texto += contenido + "\n"

    return texto


# ============================================================
# CONVERTIR NÚMEROS
# ============================================================

def convertir_numero(valor):

    if valor is None:
        return None

    valor = valor.strip()

    if valor in ("", "-"):
        return None

    # Ejemplo:
    # 19.112 -> 19112
    # 859.628 -> 859628

    valor = valor.replace(".", "")
    valor = valor.replace(",", ".")

    try:
        return int(float(valor))
    except ValueError:
        return None


# ============================================================
# EXTRAER DATOS DE CONCEPCIÓN
# ============================================================

def buscar_datos_concepcion(texto):

    lineas = texto.splitlines()

    print("")
    print("Buscando datos de Concepción...")
    print("")

    registros = []

    # --------------------------------------------------------
    # Buscar filas de fechas
    # --------------------------------------------------------

    patron_fecha = re.compile(
        r"^(\d{2}/\d{2}/\d{4})\s+"
    )

    for linea in lineas:

        linea = linea.strip()

        coincidencia = patron_fecha.match(linea)

        if not coincidencia:
            continue

        columnas = linea.split()

        print("Fila encontrada:", linea)

        # ----------------------------------------------------
        # La tabla es:
        #
        # Fecha
        # Aguilares
        # Bella Vista
        # Concepción
        # Cruz Alta
        #
        # Concepción = columna 4
        # índice Python = 3
        # ----------------------------------------------------

        if len(columnas) < 4:
            continue

        fecha = columnas[0]

        molienda_concepcion = convertir_numero(
            columnas[3]
        )

        if molienda_concepcion is None:

            print(
                "  Concepción sin dato para",
                fecha
            )

            continue

        print(
            "  >>> CONCEPCIÓN:",
            molienda_concepcion,
            "t"
        )

        registros.append(
            {
                "fecha": fecha,
                "molienda": molienda_concepcion
            }
        )

    if not registros:

        raise Exception(
            "No se encontraron datos de molienda de Concepción"
        )

    # --------------------------------------------------------
    # Ordenar por fecha
    # --------------------------------------------------------

    registros.sort(
        key=lambda x: datetime.strptime(
            x["fecha"],
            "%d/%m/%Y"
        )
    )

    ultimo = registros[-1]

    print("")
    print("Último dato encontrado:")
    print("Fecha:", ultimo["fecha"])
    print("Molienda:", ultimo["molienda"], "t")

    return ultimo


# ============================================================
# BUSCAR ACUMULADO DE CONCEPCIÓN
# ============================================================

def buscar_acumulado(texto):

    print("")
    print("Buscando acumulado de zafra...")

    lineas = texto.splitlines()

    for linea in lineas:

        linea_limpia = linea.strip()

        if linea_limpia.lower().startswith(
            "total zafra"
        ):

            columnas = linea_limpia.split()

            print(
                "Fila Total zafra encontrada:",
                linea_limpia
            )

            # ------------------------------------------------
            # La estructura esperada es:
            #
            # Total zafra
            # Aguilares
            # Bella Vista
            # Concepción
            # Cruz Alta
            #
            # Concepción = índice 3
            # ------------------------------------------------

            if len(columnas) >= 4:

                acumulado = convertir_numero(
                    columnas[3]
                )

                if acumulado is not None:

                    print(
                        ">>> ACUMULADO CONCEPCIÓN:",
                        acumulado,
                        "t"
                    )

                    return acumulado

    raise Exception(
        "No se encontró el acumulado de zafra de Concepción"
    )


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

print("")
print("==========================================")
print(" ACTUALIZACIÓN MOLIENDA CONCEPCIÓN")
print("==========================================")
print("")

try:

    # Descargar PDF
    pdf_bytes = descargar_pdf()

    # Leer PDF
    texto = extraer_texto(pdf_bytes)

    # Buscar molienda diaria
    ultimo = buscar_datos_concepcion(texto)

    # Buscar acumulado
    acumulado = buscar_acumulado(texto)

    # --------------------------------------------------------
    # Crear data.json
    # --------------------------------------------------------

    datos = {

        "ingenio": "Concepción",

        "fecha": ultimo["fecha"],

        "molienda_diaria": ultimo["molienda"],

        "molienda_acumulada": acumulado,

        "actualizado": datetime.now().strftime(
            "%d/%m/%Y %H:%M"
        )
    }

    print("")
    print("==========================================")
    print(" DATOS FINALES")
    print("==========================================")
    print("Ingenio:", datos["ingenio"])
    print("Fecha:", datos["fecha"])
    print(
        "Molienda diaria:",
        datos["molienda_diaria"],
        "t"
    )
    print(
        "Molienda acumulada:",
        datos["molienda_acumulada"],
        "t"
    )
    print(
        "Actualizado:",
        datos["actualizado"]
    )
    print("==========================================")

    # --------------------------------------------------------
    # Guardar JSON
    # --------------------------------------------------------

    with open(
        "data.json",
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            datos,
            archivo,
            indent=2,
            ensure_ascii=False
        )

    print("")
    print("data.json actualizado correctamente.")
    print("")

except Exception as error:

    print("")
    print("==========================================")
    print(" ERROR")
    print("==========================================")
    print(str(error))
    print("==========================================")
    print("")

    raise
