import json
import re
from datetime import datetime

# Archivo de datos que actualiza la página
archivo = "data.json"

# Este valor será reemplazado cuando conectemos
# la descarga automática del PDF del IPAAT
texto_pdf = """
Concepción   15430   1254800
"""

# Busca la línea del Ingenio Concepción
busqueda = re.search(
    r"Concepción\s+(\d+)\s+(\d+)",
    texto_pdf
)

if busqueda:

    molienda = int(busqueda.group(1))
    acumulada = int(busqueda.group(2))

    datos = {
        "ingenio": "Concepción",
        "fecha": datetime.now().strftime("%d/%m/%Y"),
        "molienda_diaria": molienda,
        "molienda_acumulada": acumulada,
        "actualizado": datetime.now().strftime("%H:%M")
    }

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

    print("Datos actualizados correctamente")

else:
    print("No se encontró Ingenio Concepción")
