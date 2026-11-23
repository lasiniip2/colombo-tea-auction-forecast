const canvas = document.querySelector("#price-chart");
const points = JSON.parse(document.querySelector("#chart-data").textContent);
const catalogueColours = {
  "Low Grown": "#875132", "High Grown": "#496b87",
  "Dust": "#b9772d", "Off Grade": "#76557b"
};
const colour = catalogue => catalogueColours[catalogue] || "#635449";
const legend = document.querySelector("#chart-legend");
const detail = document.querySelector("#chart-detail");
const money = new Intl.NumberFormat("en-LK", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
let screenPoints = [];
for (const catalogue of [...new Set(points.map(point => point.catalogue))].sort()) {
  const label = document.createElement("span");
  const dot = document.createElement("i");
  dot.style.backgroundColor = colour(catalogue);
  label.append(dot, catalogue);
  legend.append(label);
}

function drawChart() {
  const { width, height } = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  const ctx = canvas.getContext("2d");
  ctx.scale(ratio, ratio);
  const margin = { left: 69, top: 14, right: 20, bottom: 56 };
  const right = width - margin.right;
  const bottom = height - margin.bottom;
  const prices = points.flatMap(point => [point.actual, point.forecast]);
  const low = Math.min(...prices);
  const high = Math.max(...prices);
  const pad = Math.max((high - low) * .045, 1);
  const position = value => (value - low + pad) / (high - low + 2 * pad);
  const x = value => margin.left + position(value) * (right - margin.left);
  const y = value => bottom - position(value) * (bottom - margin.top);
  const format = new Intl.NumberFormat("en-LK", { maximumFractionDigits: 0 });
  ctx.font = "12px system-ui";
  ctx.fillStyle = "#675347";
  for (let tick = 0; tick <= 4; tick += 1) {
    const value = low + (high - low || 1) * tick / 4;
    ctx.strokeStyle = "#eadcd0";
    ctx.beginPath();
    ctx.moveTo(x(value), margin.top);
    ctx.lineTo(x(value), bottom);
    ctx.moveTo(margin.left, y(value));
    ctx.lineTo(right, y(value));
    ctx.stroke();
    ctx.textAlign = "center";
    ctx.fillText(format.format(value), x(value), bottom + 17);
    ctx.textAlign = "right";
    ctx.fillText(format.format(value), margin.left - 8, y(value) + 4);
  }
  ctx.strokeStyle = "#886d5a";
  ctx.setLineDash([5, 5]);
  ctx.beginPath();
  ctx.moveTo(x(low), y(low));
  ctx.lineTo(x(high), y(high));
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.globalAlpha = .62;
  screenPoints = points.map(point => ({ point, x: x(point.actual), y: y(point.forecast) }));
  for (const { point, x, y } of screenPoints) {
    ctx.fillStyle = colour(point.catalogue);
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, 2 * Math.PI);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
  ctx.fillStyle = "#332319";
  ctx.textAlign = "center";
  ctx.fillText("Recorded price (LKR)", (margin.left + right) / 2, height - 10);
  ctx.save();
  ctx.translate(13, (margin.top + bottom) / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("Predicted price (LKR)", 0, 0);
  ctx.restore();
}

new ResizeObserver(drawChart).observe(canvas);
canvas.addEventListener("pointermove", event => {
  const { left, top } = canvas.getBoundingClientRect();
  let nearest;
  let distance = 64;
  for (const candidate of screenPoints) {
    const squared = (candidate.x - (event.clientX - left)) ** 2
      + (candidate.y - (event.clientY - top)) ** 2;
    if (squared < distance) {
      nearest = candidate.point;
      distance = squared;
    }
  }
  detail.hidden = !nearest;
  if (nearest) {
    detail.textContent = `${nearest.catalogue} · ${nearest.category} · ${nearest.date} · Recorded LKR ${money.format(nearest.actual)} · Predicted LKR ${money.format(nearest.forecast)}`;
  }
});
canvas.addEventListener("pointerleave", () => { detail.hidden = true; });
