fetch("data.json")
  .then(respuesta => respuesta.json())
  .then(datos => {

    document.getElementById("molienda").innerHTML =
      datos.molienda_diaria.toLocaleString("es-AR") + " t";

    document.getElementById("acumulado").innerHTML =
      datos.molienda_acumulada.toLocaleString("es-AR") + " t";

    document.getElementById("fecha").innerHTML =
      datos.fecha || "-";

    document.getElementById("actualizado").innerHTML =
      datos.actualizado || "-";

  })
  .catch(error => {

    document.getElementById("molienda").innerHTML =
      "Sin datos";

    console.log(error);

  });
