import { dataTableManager } from "./dataTableManager.js";

// Listener para el overlay de carga global
document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", () => {
    document.getElementById("loading-overlay")?.classList.remove("hidden");
  });
});

// Inicializa el módulo que gestiona la tabla cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", () => {
  const scheduleTable = document.querySelector("table#data");
  if (scheduleTable) {
    dataTableManager.init("table#data");
  }
});
