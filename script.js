
async function cargarDatos() {
  try {

    // Evita que el navegador use un data.json viejo
    const respuesta = await fetch(
      "data.json?t=" + Date.now(),
      {
        cache: "no-store"
      }
    );

    if (!respuesta.ok) {
      throw new Error(
        "No se pudo cargar data.json"
      );
    }

    const datos = await respuesta.json();

    console.log("Datos recibidos:", datos);

    // --------------------------------------------------
    // Molienda diaria
    // --------------------------------------------------

    document.getElementById("molienda").textContent =
      Number(datos.molienda_diaria).toLocaleString(
        "es-AR"
      ) + " t";

    // --------------------------------------------------
    // Acumulado
    // --------------------------------------------------

    document.getElementById("acumulado").textContent =
      Number(datos.molienda_acumulada).toLocaleString(
        "es-AR"
      ) + " t";

    // --------------------------------------------------
    // Fecha
    // --------------------------------------------------

    document.getElementById("fecha").textContent =
      datos.fecha || "-";

    // --------------------------------------------------
    // Actualizado
    // --------------------------------------------------

    document.getElementById("actualizado").textContent =
      datos.actualizado || "-";

  } catch (error) {

    console.error(
      "Error cargando datos:",
      error
    );

    document.getElementById("molienda").textContent =
      "Error";

    document.getElementById("acumulado").textContent =
      "-";

    document.getElementById("fecha").textContent =
      "-";

    document.getElementById("actualizado").textContent =
      "-";
  }
}


// Cargar al abrir la página
cargarDatos();


// Volver a comprobar cada 5 minutos
setInterval(
  cargarDatos,
  5 * 60 * 1000
);
