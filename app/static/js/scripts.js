// Declarar la variable global para almacenar índices de filas eliminadas
let deletedRows = new Set();

// Cuando el DOM esté completamente cargado, se agregan los event listeners a los checkboxes existentes.
document.addEventListener("DOMContentLoaded", function () {
  const checkboxes = document.querySelectorAll('input[name="selected_rows"]');
  checkboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", function () {
      toggleRowSelection(checkbox);
    });
  });

  const rows = document.querySelectorAll("tbody tr");
  rows.forEach((row) => {
    row.addEventListener("mouseenter", function () {
      row.classList.add("hover-row");
    });
    row.addEventListener("mouseleave", function () {
      row.classList.remove("hover-row");
    });
    row.addEventListener("click", toggleRowSelectionByClick);
  });
});

function toggleRowSelectionByClick(event) {
  // Si el clic se hizo sobre el checkbox, se omite para evitar doble acción
  if (event.target && event.target.matches('input[name="selected_rows"]')) {
    return;
  }
  const row = event.currentTarget; // La fila sobre la que se hizo clic
  const checkbox = row.querySelector('input[name="selected_rows"]');
  if (checkbox) {
    // Cambia el estado del checkbox y actualiza el resaltado
    checkbox.checked = !checkbox.checked;
    toggleRowSelection(checkbox);
  }
}

function filterTable() {
  const instructorInput = document
    .getElementById("filterInstructor")
    .value.toLowerCase();
  const groupInput = document.getElementById("filterGroup").value.toLowerCase();
  const rows = document.querySelectorAll("tbody tr");

  rows.forEach((row) => {
    const checkbox = row.querySelector('input[name="selected_rows"]');
    if (!checkbox) return; // Por seguridad, si no hay checkbox, se omite la fila

    const instructorCell = row.cells[7]; //Instructor
    const groupCell = row.cells[8]; //Group

    if (instructorCell && groupCell) {
      const instructorName = instructorCell.textContent.toLowerCase();
      const groupName = groupCell.textContent.toLowerCase();

      // Mostrar la fila solo si:
      // - No está marcada como eliminada
      // - El nombre del instructor o grupo coinciden con los filtros (o el filtro está vacío)
      if (
        !deletedRows.has(checkbox.value) &&
        (instructorName.includes(instructorInput) || instructorInput === "") &&
        (groupName.includes(groupInput) || groupInput === "")
      ) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
    }
  });
}

function clearFilters() {
  document.getElementById("filterInstructor").value = "";
  document.getElementById("filterGroup").value = "";
  filterTable();
}

function toggleRowSelection(checkbox) {
  const row = checkbox.closest("tr"); // Encuentra la fila más cercana
  if (checkbox.checked) {
    row.classList.add("selected-row"); // Resalta la fila seleccionada
  } else {
    row.classList.remove("selected-row"); // Quita el resaltado si se deselecciona
  }
}

function toggleSelectAll() {
  const selectAllCheckbox = document.getElementById("selectAll");
  const rows = document.querySelectorAll("tbody tr");

  rows.forEach((row) => {
    // Solo afecta a las filas que están visibles
    if (row.style.display !== "none") {
      const checkbox = row.querySelector('input[name="selected_rows"]');
      if (checkbox) {
        checkbox.checked = selectAllCheckbox.checked;
        toggleRowSelection(checkbox); // Actualiza el resaltado
      }
    }
  });
}

function deleteSelectedRows() {
  const checkboxes = document.querySelectorAll(
    'input[name="selected_rows"]:checked'
  );
  checkboxes.forEach((checkbox) => {
    deletedRows.add(checkbox.value); // Agregar el índice al conjunto de eliminados
    checkbox.checked = false; // Desmarcar checkbox después de eliminar
  });
  filterTable(); // Actualiza la vista de la tabla
}

function prepareDownload() {
  // Obtener los índices de las filas eliminadas y pasarlos al input oculto
  const deletedIndices = Array.from(deletedRows).join(",");
  document.getElementById("selectedRowsInput").value = deletedIndices;

  // Enviar el formulario de descarga
  document.getElementById("downloadForm").submit();

  // Opcionalmente, ocultar la vista previa y el formulario después de enviar
  document.getElementById("wrap").remove();
  document.getElementById("downloadForm").remove();
}
