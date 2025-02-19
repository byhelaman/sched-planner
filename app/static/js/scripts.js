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

function updateSelectedCount() {
  const selectedRows = document.querySelectorAll(
    'input[name="selected_rows"]:checked'
  );
  const rowsCount = selectedRows.length;

  const deleteForm = document.getElementById("deleteForm");
  const box = document.getElementById("selected-items");

  deleteForm.style.display = rowsCount > 0 ? "inline-block" : "none";
  box.textContent = rowsCount;
}

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
  let anyVisible = false; // Variable para verificar si hay filas visibles

  rows.forEach((row) => {
    const checkbox = row.querySelector('input[name="selected_rows"]');
    if (!checkbox) return;

    const instructorCell = row.cells[7]; // Instructor
    const groupCell = row.cells[8]; // Group

    if (instructorCell && groupCell) {
      const instructorName = instructorCell.textContent.toLowerCase();
      const groupName = groupCell.textContent.toLowerCase();

      if (
        (instructorName.includes(instructorInput) || instructorInput === "") &&
        (groupName.includes(groupInput) || groupInput === "")
      ) {
        row.style.display = "";
        anyVisible = true; // Hay al menos una fila visible
      } else {
        row.style.display = "none";
      }
    }
  });

  // Mostrar mensaje si no hay filas visibles
  const table = document.querySelector("table");
  const noDataRow = document.getElementById("noDataRow");

  if (!anyVisible) {
    if (!noDataRow) {
      const tbody = document.querySelector("tbody");
      const tr = document.createElement("tr");
      tr.id = "noDataRow";
      const td = document.createElement("td");
      td.colSpan = 11;
      td.textContent = "not found data";
      td.style.textAlign = "center";
      tr.appendChild(td);
      tbody.appendChild(tr);
    }
  } else {
    table.style.display = "";
    if (noDataRow) {
      noDataRow.remove();
    }
  }
}

function clearFilters() {
  document.getElementById("filterInstructor").value = "";
  document.getElementById("filterGroup").value = "";
  filterTable();

  // Mostrar la tabla si no hay datos
  const table = document.querySelector("table");
  table.style.display = "";
  const noDataRow = document.getElementById("noDataRow");
  if (noDataRow) {
    noDataRow.remove();
  }
}

function toggleRowSelection(checkbox) {
  const row = checkbox.closest("tr"); // Encuentra la fila más cercana
  if (checkbox.checked) {
    row.classList.add("selected-row"); // Resalta la fila seleccionada
  } else {
    row.classList.remove("selected-row"); // Quita el resaltado si se deselecciona
  }
  updateSelectedCount();
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

// Función modificada para enviar los índices de las filas seleccionadas al servidor para eliminación definitiva
function deleteSelectedRows() {
  // Recolecta todos los checkboxes seleccionados
  const checkboxes = document.querySelectorAll(
    'input[name="selected_rows"]:checked'
  );
  // Array para almacenar los índices de filas a eliminar
  let indicesToDelete = [];

  checkboxes.forEach((checkbox) => {
    indicesToDelete.push(checkbox.value);
  });
  // Si hay filas seleccionadas, se envían al servidor para eliminación definitiva
  if (indicesToDelete.length > 0) {
    // Se asigna el valor al campo oculto del formulario de eliminación
    document.getElementById("selectedRowsDeleteInput").value =
      indicesToDelete.join(",");
    // Se envía el formulario de eliminación
    document.getElementById("deleteForm").submit();
  }
}

function prepareDownload() {
  document.getElementById("downloadForm").submit();
}

function cleanSchedule() {
  document.getElementById("cleanForm").submit();
}

function copySchedule() {
  fetch("/copy", {
    method: "GET",
  })
    .then((response) => {
      if (response.ok) {
        return response.text();
      } else {
        throw new Error("Error copying data");
      }
    })
    .then((schedules) => {
      navigator.clipboard.writeText(schedules);
      alert("Copied Schedule");
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}
