// document.addEventListener("DOMContentLoaded", function () {
//   const tableContainer = document.getElementById("table-container");
//   if (tableContainer.innerHTML.trim() !== "") {
//     tableContainer.style.display = "block";
//   }
// });

document.addEventListener("DOMContentLoaded", function () {
  const checkboxes = document.querySelectorAll('input[name="selected_rows"]');
    checkboxes.forEach(checkbox => {
      checkbox.addEventListener("change", function () {
        toggleRowSelection(checkbox);
      });
    });
});

function filterTable() {
  const instructorInput = document.getElementById("filterInstructor").value.toLowerCase();
  const groupInput = document.getElementById("filterGroup").value.toLowerCase();
  const rows = document.querySelectorAll("tbody tr");

  rows.forEach(row => {
    const checkbox = row.querySelector('input[name="selected_rows"]');
    if (!checkbox) return; // Seguridad

    const instructorCell = row.cells[7]; // Columna "Instructor"
    const groupCell = row.cells[8]; // Columna "Group"

    if (instructorCell && groupCell) {
      const instructorName = instructorCell.textContent.toLowerCase();
      const groupName = groupCell.textContent.toLowerCase();

      // Mostrar la fila solo si coincide con los filtros y NO está en la lista de eliminadas
      if (
        !deletedRows.has(checkbox.value) && // No mostrar si está eliminada
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

  rows.forEach(row => {
    if (row.style.display !== "none") {  // Solo afecta las filas visibles
      const checkbox = row.querySelector('input[name="selected_rows"]');
      if (checkbox) {
        checkbox.checked = selectAllCheckbox.checked;
        toggleRowSelection(checkbox); // Aplicar resaltado
      }
    }
  });
}

let deletedRows = new Set(); // Almacenar los índices eliminados

function deleteSelectedRows() {
  const checkboxes = document.querySelectorAll('input[name="selected_rows"]:checked');
  checkboxes.forEach(checkbox => {
    const row = checkbox.closest("tr");
    if (row) {
      deletedRows.add(checkbox.value); // Guardar índice eliminado
      row.style.display = "none"; // Ocultar la fila eliminada
    }
  });

  // Actualizar el input de selección
  document.getElementById('selectAll').checked = false;

}

function prepareDownload() {
  document.getElementById('selectedRowsInput').value = Array.from(deletedRows).join(',');
  document.getElementById('downloadForm').submit();
}