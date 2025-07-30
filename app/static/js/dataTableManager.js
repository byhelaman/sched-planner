import * as utils from "./utils.js";

const manager = (function () {
  // --- Variables de estado y elementos del DOM ---
  let table,
    tbody,
    headers,
    contextMenu,
    copyRowAction,
    filterInstructor,
    filterGroup,
    filterOverlaps,
    clearFiltersBtn,
    selectAllCheckbox,
    deleteBtn,
    downloadBtn,
    cleanBtn,
    copyBtn,
    selectedCountEl,
    overlapCountEl,
    deleteForm;

  let columnsConfig = [];
  let rowsData = [];
  let sortCriteria = [];
  let rightClickedRow = null;

  function sortData() {
    if (sortCriteria.length === 0) return;
    rowsData.sort((a, b) => {
      for (const criterion of sortCriteria) {
        const cfg = columnsConfig.find((c) => c.label === criterion.label);
        if (!cfg) continue;
        const va = cfg.parser(a.data[criterion.label]);
        const vb = cfg.parser(b.data[criterion.label]);
        let comparison = va < vb ? -1 : va > vb ? 1 : 0;
        if (comparison !== 0) {
          return criterion.direction === "asc" ? comparison : -comparison;
        }
      }
      return 0;
    });
  }

  function render() {
    const frag = document.createDocumentFragment();
    let visibleCount = 0;
    rowsData.forEach((item) => {
      item.row.style.display = item.visible ? "" : "none";
      item.row.classList.toggle("overlap-row", item.overlapped);
      frag.appendChild(item.row);
      if (item.visible) visibleCount++;
    });

    tbody.innerHTML = "";
    tbody.appendChild(frag);

    const selCount = rowsData.filter((it) => it.selected).length;
    selectedCountEl.textContent = selCount;
    overlapCountEl.textContent = rowsData.filter(
      (it) => it.visible && it.overlapped
    ).length;

    const existingNoData = document.getElementById("noDataRow");
    if (visibleCount === 0 && !existingNoData) {
      const tr = document.createElement("tr");
      tr.id = "noDataRow";
      const td = document.createElement("td");
      td.colSpan = headers.length;
      td.textContent = "Not found data";
      td.style.textAlign = "center";
      tr.appendChild(td);
      tbody.appendChild(tr);
    } else if (visibleCount > 0 && existingNoData) {
      existingNoData.remove();
    }
  }

  function updateSelectedCount() {
    const totalSelectedCount = rowsData.filter((it) => it.selected).length;

    // Actualiza el texto del contador
    selectedCountEl.textContent = totalSelectedCount;

    // Muestra u oculta el botón de eliminar según si hay filas seleccionadas
    deleteForm.style.display = totalSelectedCount > 0 ? "inline-block" : "none";

    // --- Lógica del checkbox "Select All" ---
    const visibleItems = rowsData.filter((it) => it.visible);
    const selectedVisibleCount = visibleItems.filter(
      (it) => it.selected
    ).length;

    if (
      visibleItems.length > 0 &&
      selectedVisibleCount === visibleItems.length
    ) {
      selectAllCheckbox.checked = true;
      selectAllCheckbox.indeterminate = false;
    } else if (selectedVisibleCount > 0) {
      selectAllCheckbox.checked = false;
      selectAllCheckbox.indeterminate = true;
    } else {
      selectAllCheckbox.checked = false;
      selectAllCheckbox.indeterminate = false;
    }
  }

  function updateSortHeaders() {
    columnsConfig.forEach((c) => {
      if (c.sortable) c.headerEl.textContent = c.headerEl.dataset.originalText;
    });
    sortCriteria.forEach((sc) => {
      const sortedCfg = columnsConfig.find((c) => c.label === sc.label);
      if (sortedCfg) {
        const arrow = sc.direction === "asc" ? " ↑" : " ↓";
        sortedCfg.headerEl.textContent =
          sortedCfg.headerEl.dataset.originalText + arrow;
      }
    });
  }

  function onFilterChange() {
    const instFilter = filterInstructor.value.trim().toLowerCase();
    const grpFilter = filterGroup.value.trim().toLowerCase();
    const onlyOverlap = filterOverlaps.checked;

    rowsData.forEach((item) => (item.overlapped = false));
    const byInstructor = {};
    rowsData.forEach((it) => {
      const key = it.data["Instructor"] || "__NO_INSTRUCTOR__";
      (byInstructor[key] = byInstructor[key] || []).push(it);
    });
    Object.values(byInstructor).forEach((list) => {
      for (let i = 0; i < list.length; i++) {
        for (let j = i + 1; j < list.length; j++) {
          const a = list[i],
            b = list[j];
          if (
            utils.parseTimeToMinutes(a.data["Start Time"]) <
              utils.parseTimeToMinutes(b.data["End Time"]) &&
            utils.parseTimeToMinutes(b.data["Start Time"]) <
              utils.parseTimeToMinutes(a.data["End Time"])
          ) {
            a.overlapped = b.overlapped = true;
          }
        }
      }
    });

    rowsData.forEach((item) => {
      const passInst =
        !instFilter ||
        item.data["Instructor"]?.toLowerCase().includes(instFilter);
      const passGrp =
        !grpFilter || item.data["Group"]?.toLowerCase().includes(grpFilter);
      const passOverlap = !onlyOverlap || item.overlapped;
      item.visible = passInst && passGrp && passOverlap;
    });

    render();
    updateSelectedCount();
  }

  function toggleRowSelection(item, isSelected) {
    item.selected = isSelected;
    const cb = item.row.querySelector('input[name="selected_rows"]');
    if (cb) cb.checked = isSelected;
    item.row.classList.toggle("selected-row", isSelected);
  }

  // --- Lógica de los manejadores de eventos (Event Handlers) ---
  function handleSortClick(e, cfg) {
    const existingIndex = sortCriteria.findIndex(
      (sc) => sc.label === cfg.label
    );
    if (e.shiftKey) {
      if (existingIndex > -1) {
        sortCriteria[existingIndex].direction =
          sortCriteria[existingIndex].direction === "asc" ? "desc" : "asc";
      } else {
        sortCriteria.push({ label: cfg.label, direction: "asc" });
      }
    } else {
      if (existingIndex > -1 && sortCriteria.length === 1) {
        sortCriteria[0].direction =
          sortCriteria[0].direction === "asc" ? "desc" : "asc";
      } else {
        sortCriteria = [{ label: cfg.label, direction: "asc" }];
      }
    }
    sortData();
    updateSortHeaders();
    render();
  }

  function handleRowClick(e) {
    const tr = e.target.closest("tr");
    if (!tr) return;
    const item = rowsData.find((it) => it.row === tr);
    if (!item) return;
    const cb = tr.querySelector('input[name="selected_rows"]');
    if (e.target !== cb) {
      cb.checked = !cb.checked;
    }
    toggleRowSelection(item, cb.checked);
    updateSelectedCount();
  }

  function bindEvents() {
    filterInstructor.addEventListener(
      "keyup",
      utils.debounce(onFilterChange, 120)
    );
    filterGroup.addEventListener("keyup", utils.debounce(onFilterChange, 120));
    filterOverlaps.addEventListener("change", onFilterChange);
    clearFiltersBtn.addEventListener("click", () => {
      filterInstructor.value = "";
      filterGroup.value = "";
      filterOverlaps.checked = false;
      selectAllCheckbox.checked = false;
      selectAllCheckbox.indeterminate = false;
      onFilterChange();
    });

    selectAllCheckbox.addEventListener("change", (e) => {
      rowsData.forEach((item) => {
        if (item.visible) toggleRowSelection(item, e.target.checked);
      });
      updateSelectedCount();
    });

    tbody.addEventListener("click", handleRowClick);
    tbody.addEventListener("mouseover", (e) =>
      e.target.closest("tr")?.classList.add("hover-row")
    );
    tbody.addEventListener("mouseout", (e) =>
      e.target.closest("tr")?.classList.remove("hover-row")
    );

    deleteBtn.addEventListener("click", () => {
      const indices = rowsData
        .filter((it) => it.selected)
        .map((it) => it.originalIndex);
      if (indices.length) {
        document.getElementById("selectedRowsDeleteInput").value =
          indices.join(",");
        deleteForm.submit();
      }
    });

    downloadBtn?.addEventListener("click", () =>
      document.getElementById("downloadForm").submit()
    );
    cleanBtn?.addEventListener("click", () =>
      document.getElementById("cleanForm").submit()
    );
    copyBtn.addEventListener("click", () => {
      fetch("/copy", { method: "GET" })
        .then((res) => {
          if (!res.ok) throw new Error("Error copying data");
          return res.text();
        })
        .then((txt) => {
          navigator.clipboard.writeText(txt);
          alert("Copied Schedule");
        })
        .catch((err) => console.error(err));
    });

    tbody.addEventListener("contextmenu", (e) => {
      e.preventDefault();
      const tr = e.target.closest("tr");
      if (!tr || tr.id === "noDataRow") return;
      rightClickedRow = tr;
      contextMenu.style.top = `${e.pageY}px`;
      contextMenu.style.left = `${e.pageX}px`;
      contextMenu.style.display = "block";
    });

    window.addEventListener("click", () => {
      if (contextMenu.style.display === "block")
        contextMenu.style.display = "none";
    });

    copyRowAction.addEventListener("click", () => {
      if (!rightClickedRow) return;
      const cells = rightClickedRow.cells;
      const date = cells[1].textContent.trim();
      const groupName = cells[8].textContent.trim();
      const startTime24h = utils.convertTo24HourFormat(
        cells[4].textContent.trim()
      );
      const endTime24h = utils.convertTo24HourFormat(
        cells[5].textContent.trim()
      );
      const formattedText = `${date}\n${groupName}\n${startTime24h} - ${endTime24h}`;
      navigator.clipboard
        .writeText(formattedText)
        .then(() => console.log("Row copied successfully"))
        .catch((err) => console.error("Error copying row: ", err));
    });

    columnsConfig.forEach((cfg) => {
      if (cfg.sortable) {
        cfg.headerEl.style.cursor = "pointer";
        cfg.headerEl.addEventListener("click", (e) => handleSortClick(e, cfg));
      }
    });
  }

  // Se expone un único método `init` que pone todo en marcha.
  function init(tableSelector) {
    // Asignar elementos del DOM
    table = document.querySelector(tableSelector);
    if (!table) return;
    tbody = table.tBodies[0];
    headers = Array.from(table.tHead.querySelectorAll("th"));
    contextMenu = document.getElementById("row-context-menu");
    copyRowAction = document.getElementById("copy-row-action");
    filterInstructor = document.getElementById("filterInstructor");
    filterGroup = document.getElementById("filterGroup");
    filterOverlaps = document.getElementById("filterOverlaps");
    clearFiltersBtn = document.getElementById("clearFilters");
    selectAllCheckbox = document.getElementById("selectAll");
    deleteBtn = document.getElementById("deleteSelected");
    downloadBtn = document.getElementById("downloadBtn");
    cleanBtn = document.getElementById("cleanBtn");
    copyBtn = document.getElementById("copyBtn");
    selectedCountEl = document.getElementById("selected-items");
    overlapCountEl = document.getElementById("overlap-items");
    deleteForm = document.getElementById("deleteForm");

    // Construir configuración y datos iniciales
    headers.forEach((th) => {
      th.dataset.originalText = th.textContent.trim();
    });
    columnsConfig = headers.map((th, idx) => ({
      label: th.dataset.originalText,
      index: idx,
      parser: /time/i.test(th.dataset.originalText)
        ? utils.parseTimeToMinutes
        : utils.textParser,
      sortable: idx > 0,
      headerEl: th,
    }));
    rowsData = Array.from(tbody.rows).map((row, i) => {
      const data = {};
      columnsConfig.forEach((cfg) => {
        data[cfg.label] = row.cells[cfg.index]?.textContent.trim() || "";
      });
      const cb = row.querySelector('input[name="selected_rows"]');
      row.dataset.originalIndex = i;
      return {
        row,
        data,
        visible: true,
        overlapped: false,
        selected: !!cb?.checked,
        originalIndex: i,
      };
    });

    // Enlazar todos los eventos y hacer el renderizado inicial
    bindEvents();
    onFilterChange();
  }

  return {
    init: init,
  };
})();

export const dataTableManager = manager;
