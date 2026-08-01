
fetch("data.json")
  .then(function(response) {
    return response.json();
  })
  .then(function(data) {

    document.getElementById("molienda").innerHTML =
      Number(data.molienda_diaria).toLocaleString("es-AR") + " t";

    document.getElementById("acumulado").innerHTML =
      Number(data.molienda_acumulada).toLocaleString("es-AR") + " t";

    document.getElementById("fecha").innerHTML =
      data.fecha;

    document.getElementById("actualizado").innerHTML =
      data.actualizado;

  })
  .catch(function(error) {

    console.error(error);

    document.getElementById("molienda").innerHTML =
      "ERROR";

  });

