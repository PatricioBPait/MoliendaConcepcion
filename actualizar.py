import requests
import pdfplumber
import re
import json
from datetime import datetime
from io import BytesIO
from bs4 import BeautifulSoup
from urllib.parse import urljoin


# ============================================================
# CONFIGURACIÓN
# ============================================================

PAGINA_IPAAT = (
    "https://www.ipaat.gov.ar/nota/86/parte-diario-de-produccion"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
}


# ============================================================
# SESIÓN HTTP
# ============================================================

session = requests.Session()
session.headers.update(HEADERS)


# ============================================================
# BUSCAR EL PDF MÁS RECIENTE
# ============================================================

def buscar_pdf():

    print("")
    print("==========================================")
    print(" BUSCANDO PARTE DIARIO DEL IPAAT")
    print("==========================================")
    print(PAGINA_IPAAT)
    print("")

    respuesta = session.get(
        PAGINA_IPAAT,
        timeout=60
    )

    respuesta.raise_for_status()

    print("Página IPAAT descargada.")
    print("URL final:", respuesta.url)
    print("Tamaño:", len(respuesta.content), "bytes")

    soup = BeautifulSoup(
        respuesta.text,
        "html.parser"
    )

    candidatos = []

    for enlace in soup.find_all("a", href=True):

        href = enlace.get("href", "").strip()
        texto = enlace.get_text(" ", strip=True)

        if not href:
            continue

        url = urljoin(
            respuesta.url,
            href
        )

        texto_completo = (
            texto + " " + href
        ).lower()

        # Buscamos enlaces que claramente sean PDFs
        if (
            ".pdf" in url.lower()
            or "descargar" in texto_completo
            or "parte diario" in texto_completo
            or "zafra 2026" in texto_completo
        ):

            candidatos.append(
                {
                    "url": url,
                    "texto": texto
                }
            )

    print("")
    print("Enlaces candidatos encontrados:")

    for candidato in candidatos:

        print(
            "-",
            candidato["texto"],
            "=>",
            candidato["url"]
        )

    # --------------------------------------------------------
    # Primero priorizar enlaces PDF
    # --------------------------------------------------------

    for candidato in candidatos:

        url = candidato["url"]

        if ".pdf" in url.lower():

            print("")
            print("PDF seleccionado:")
            print(url)

            return url

    # --------------------------------------------------------
    # Si no aparece .pdf en el href,
    # probar los enlaces candidatos
    # --------------------------------------------------------

    for candidato in candidatos:

        print("")
        print(
            "Probando enlace:",
            candidato["url"]
        )

        try:

            r = session.get(
                candidato["url"],
                headers={
                    "Referer": PAGINA_IPAAT,
                    "Accept": "application/pdf,*/*",
                    "User-Agent": HEADERS["User-Agent"],
                },
                timeout=60,
                allow_redirects=True
            )

            if r.content.startswith(b"%PDF"):

                print(
                    "PDF válido encontrado:",
                    r.url
                )

                return r.url

        except Exception as error:

            print(
                "Error probando enlace:",
                error
            )

    raise Exception(
        "No se pudo encontrar el PDF del parte diario del IPAAT"
    )


# ============================================================
# DESCARGAR PDF
# ============================================================

def descargar_pdf(url):

    print("")
    print("==========================================")
    print(" DESCARGANDO PDF")
    print("==========================================")
    print(url)

    respuesta = session.get(
        url,
        headers={
            "Referer": PAGINA_IPAAT,
            "Accept": "application/pdf,*/*",
            "User-Agent": HEADERS["User-Agent"],
        },
        timeout=60,
        allow_redirects=True
    )

    respuesta.raise_for_status()

    print("URL final:", respuesta.url)
    print(
        "Content-Type:",
        respuesta.headers.get("Content-Type")
    )
    print(
        "Tamaño:",
        len(respuesta.content),
        "bytes"
    )

    # --------------------------------------------------------
    # VALIDACIÓN REAL DEL PDF
    # --------------------------------------------------------

    if not respuesta.content.startswith(b"%PDF"):

        print("")
        print("Los primeros bytes recibidos son:")
        print(repr(respuesta.content[:200]))

        raise Exception(
            "IPAAT no devolvió un PDF válido"
        )

    print("PDF válido confirmado.")

    return respuesta.content


# ============================================================
# EXTRAER TEXTO DEL PDF
# ============================================================

def extraer_texto(pdf_bytes):

    print("")
    print("==========================================")
    print(" LEYENDO PDF")
    print("==========================================")

    texto = ""

    with pdfplumber.open(
        BytesIO(pdf_bytes)
    ) as pdf:

        print(
            "Cantidad de páginas:",
            len(pdf.pages)
        )

        for numero, pagina in enumerate(
            pdf.pages,
            start=1
        ):

            contenido = (
                pagina.extract_text() or ""
            )

            print(
                "Página",
                numero,
                "-",
                len(contenido),
                "caracteres"
            )

            texto += contenido + "\n"

    return texto


# ============================================================
# CONVERTIR NÚMEROS
# ============================================================

def numero(valor):

    if valor is None:
        return None

    valor = valor.strip()

    if valor in ("", "-"):
        return None

    # 19.112 -> 19112
    # 859.628 -> 859628

    valor = valor.replace(
        ".",
        ""
    )

    valor = valor.replace(
        ",",
        "."
    )

    try:

        return int(
            float(valor)
        )

    except ValueError:

        return None


# ============================================================
# EXTRAER TABLA CAÑA MOLIDA BRUTA
# ============================================================

def extraer_cania_molida(texto):

    lineas = texto.splitlines()

    print("")
    print("==========================================")
    print(" BUSCANDO CAÑA MOLIDA BRUTA")
    print("==========================================")

    # --------------------------------------------------------
    # Encontrar el encabezado correcto
    # --------------------------------------------------------

    inicio_tabla = None

    for i, linea in enumerate(lineas):

        if (
            "Fecha" in linea
            and "Concepción" in linea
            and "Cruz Alta" in linea
        ):

            bloque = "\n".join(
                lineas[
                    max(0, i - 10):
                    i + 5
                ]
            )

            if (
                "Caña molida bruta"
                in bloque
            ):

                inicio_tabla = i

                print(
                    "Encabezado encontrado "
                    "en línea:",
                    i
                )

                break

    if inicio_tabla is None:

        raise Exception(
            "No se encontró la tabla "
            "'Caña molida bruta (t)'"
        )

    # --------------------------------------------------------
    # Leer las filas posteriores
    # --------------------------------------------------------

    registros = []

    patron_fecha = re.compile(
        r"^(\d{2}/\d{2}/\d{4})\s+"
    )

    for linea in lineas[
        inicio_tabla:
    ]:

        linea = linea.strip()

        coincidencia = (
            patron_fecha.match(linea)
        )

        if not coincidencia:
            continue

        columnas = linea.split()

        if len(columnas) < 4:
            continue

        fecha = columnas[0]

        # ----------------------------------------------------
        # Estructura:
        #
        # Fecha
        # Aguilares
        # Bella Vista
        # Concepción
        # Cruz Alta
        #
        # Concepción = índice 3
        # ----------------------------------------------------

        molienda = numero(
            columnas[3]
        )

        if molienda is None:

            print(
                fecha,
                "-> Concepción sin dato"
            )

            continue

        print(
            fecha,
            "-> Concepción:",
            molienda,
            "t"
        )

        registros.append(
            {
                "fecha": fecha,
                "molienda": molienda
            }
        )

    if not registros:

        raise Exception(
            "No se encontraron datos "
            "válidos de Concepción"
        )

    # --------------------------------------------------------
    # Ordenar por fecha
    # --------------------------------------------------------

    registros.sort(
        key=lambda x:
        datetime.strptime(
            x["fecha"],
            "%d/%m/%Y"
        )
    )

    ultimo = registros[-1]

    print("")
    print(
        "Última fecha con molienda:",
        ultimo["fecha"]
    )

    print(
        "Molienda diaria:",
        ultimo["molienda"],
        "t"
    )

    return ultimo


# ============================================================
# EXTRAER TOTAL ZAFRA
# ============================================================

def extraer_acumulado(texto):

    print("")
    print("==========================================")
    print(" BUSCANDO TOTAL ZAFRA")
    print("==========================================")

    lineas = texto.splitlines()

    for linea in lineas:

        linea = linea.strip()

        if not linea.startswith(
            "Total zafra"
        ):
            continue

        columnas = linea.split()

        print(
            "Fila encontrada:",
            linea
        )

        if len(columnas) < 4:
            continue

        # Total zafra
        # Aguilares
        # Bella Vista
        # Concepción

        acumulado = numero(
            columnas[3]
        )

        if acumulado is not None:

            print(
                "Acumulado Concepción:",
                acumulado,
                "t"
            )

            return acumulado

    raise Exception(
        "No se encontró el acumulado "
        "de zafra de Concepción"
    )


# ============================================================
# GUARDAR DATA.JSON
# ============================================================

def guardar_datos(
    fecha,
    molienda,
    acumulado
):

    datos = {

        "ingenio": "Concepción",

        "fecha": fecha,

        "molienda_diaria": molienda,

        "molienda_acumulada": acumulado,

        "actualizado": datetime.now().strftime(
            "%d/%m/%Y %H:%M"
        )
    }

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

    return datos


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

print("")
print("##########################################")
print("# MOLIENDA CONCEPCIÓN - IPAAT")
print("##########################################")
print("")

try:

    # 1. Buscar PDF actual
    url_pdf = buscar_pdf()

    # 2. Descargar PDF
    pdf_bytes = descargar_pdf(
        url_pdf
    )

    # 3. Extraer texto
    texto = extraer_texto(
        pdf_bytes
    )

    # 4. Buscar molienda de Concepción
    ultimo = extraer_cania_molida(
        texto
    )

    # 5. Buscar acumulado
    acumulado = extraer_acumulado(
        texto
    )

    # 6. Guardar
    datos = guardar_datos(
        ultimo["fecha"],
        ultimo["molienda"],
        acumulado
    )

    # --------------------------------------------------------
    # RESULTADO FINAL
    # --------------------------------------------------------

    print("")
    print("##########################################")
    print("# ACTUALIZACIÓN CORRECTA")
    print("##########################################")
    print(
        "Ingenio:",
        datos["ingenio"]
    )
    print(
        "Fecha:",
        datos["fecha"]
    )
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
    print("##########################################")
    print("")


except Exception as error:

    print("")
    print("##########################################")
    print("# ERROR")
    print("##########################################")
    print(str(error))
    print("##########################################")
    print("")

    raise
