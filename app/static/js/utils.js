export function parseTimeToMinutes(timeStr) {
  const parts = timeStr.trim().split(" ");
  let [hh, mm] = parts[0].split(":").map(Number);
  const meridiem = parts[1];
  if (meridiem === "PM" && hh < 12) hh += 12;
  if (meridiem === "AM" && hh === 12) hh = 0;
  return hh * 60 + mm;
}

export function convertTo24HourFormat(timeStr) {
  const timeParts = timeStr.trim().split(" ");
  let [hours, minutes] = timeParts[0].split(":").map(Number);
  const meridiem = timeParts[1];
  if (meridiem === "PM" && hours < 12) hours += 12;
  if (meridiem === "AM" && hours === 12) hours = 0;
  const formattedHours = String(hours).padStart(2, "0");
  const formattedMinutes = String(minutes).padStart(2, "0");
  return `${formattedHours}:${formattedMinutes}`;
}

export function textParser(s) {
  return s.toLowerCase();
}

export function debounce(fn, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), wait);
  };
}
