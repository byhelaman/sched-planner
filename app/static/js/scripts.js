// Cuando el DOM esté completamente cargado, adjunta los event listeners
// a los checkboxes y filas existentes. Esto garantiza que los checkboxes
// generados dinámicamente sigan siendo manejados correctamente.

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

  // Muestra la superposición de carga cuando el usuario envía el formulario de subida.
  const uploadForm = document.getElementById("uploadForm");
  if (uploadForm) {
    uploadForm.addEventListener("submit", function () {
      const overlay = document.getElementById("loading-overlay");
      if (overlay) {
        overlay.classList.remove("hidden");
      }
    });
  }
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
  // Si el clic ocurrió sobre el propio checkbox, deja que el manejador
  // de cambio se encargue de ello.
  if (event.target && event.target.matches('input[name="selected_rows"]')) {
    return;
  }
  const row = event.currentTarget;
  const checkbox = row.querySelector('input[name="selected_rows"]');
  if (checkbox) {
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
  let anyVisible = false;

  rows.forEach((row) => {
    const checkbox = row.querySelector('input[name="selected_rows"]');
    if (!checkbox) return;

    const instructorCell = row.cells[7];
    const groupCell = row.cells[8];

    if (instructorCell && groupCell) {
      const instructorName = instructorCell.textContent.toLowerCase();
      const groupName = groupCell.textContent.toLowerCase();

      if (
        (instructorName.includes(instructorInput) || instructorInput === "") &&
        (groupName.includes(groupInput) || groupInput === "")
      ) {
        row.style.display = "";
        anyVisible = true;
      } else {
        row.style.display = "none";
      }
    }
  });

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

  const table = document.querySelector("table");
  table.style.display = "";
  const noDataRow = document.getElementById("noDataRow");
  if (noDataRow) {
    noDataRow.remove();
  }
}

function toggleRowSelection(checkbox) {
  const row = checkbox.closest("tr");
  if (checkbox.checked) {
    row.classList.add("selected-row");
  } else {
    row.classList.remove("selected-row");
  }
  updateSelectedCount();
}

function toggleSelectAll() {
  const selectAllCheckbox = document.getElementById("selectAll");
  const rows = document.querySelectorAll("tbody tr");
  rows.forEach((row) => {
    if (row.style.display !== "none") {
      const checkbox = row.querySelector('input[name="selected_rows"]');
      if (checkbox) {
        checkbox.checked = selectAllCheckbox.checked;
        toggleRowSelection(checkbox);
      }
    }
  });
}

function deleteSelectedRows() {
  const checkboxes = document.querySelectorAll(
    'input[name="selected_rows"]:checked'
  );
  let indicesToDelete = [];
  checkboxes.forEach((checkbox) => {
    indicesToDelete.push(checkbox.value);
  });
  if (indicesToDelete.length > 0) {
    document.getElementById("selectedRowsDeleteInput").value =
      indicesToDelete.join(",");
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
