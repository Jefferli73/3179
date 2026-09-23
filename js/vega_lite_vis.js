// Shared look for all eleven charts, so the page reads as one system.
const vegaConfig = {
  font: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
  background: null,
  view: { stroke: null },
  title: {
    fontSize: 15,
    fontWeight: 600,
    color: "#1d2327",
    subtitleFontSize: 12,
    subtitleColor: "#5a6570",
    subtitlePadding: 4,
    anchor: "start",
    offset: 10
  },
  axis: {
    labelFontSize: 11,
    labelColor: "#4a5560",
    titleFontSize: 11,
    titleFontWeight: 500,
    titleColor: "#5a6570",
    domainColor: "#d5d8db",
    tickColor: "#d5d8db",
    gridColor: "#ecebe6",
    labelPadding: 4
  },
  legend: {
    labelFontSize: 11,
    labelColor: "#4a5560",
    titleFontSize: 11,
    titleFontWeight: 600,
    titleColor: "#1d2327",
    symbolStrokeWidth: 0
  },
  header: { labelFontSize: 12, labelFontWeight: 600, labelColor: "#1d2327" },
  range: { category: { scheme: "tableau10" } }
};

const charts = [
  ["nostalgia_matrix",  "js/nostalgia_matrix.vg.json"],
  ["designer_timeline", "js/designer_timeline.vg.json"],
  ["designer_bump",     "js/designer_bump.vg.json"],
  ["fleet_age_map",     "js/fleet_age_map.vg.json"],
  ["fleet_symbol_map",  "js/fleet_symbol_map.vg.json"],
  ["ev_hex_map",        "js/ev_hex_map.vg.json"],
  ["fleet_by_make",     "js/fleet_by_make.vg.json"],
  ["motive_stream",     "js/motive_stream.vg.json"],
  ["decade_butterfly",  "js/decade_butterfly.vg.json"],
  ["decade_waffle",     "js/decade_waffle.vg.json"],
  ["decade_gap",        "js/decade_gap.vg.json"]
];

charts.forEach(function (c) {
  vegaEmbed("#" + c[0], c[1], { config: vegaConfig, actions: false })
    .catch(function (err) { console.error(c[0], err); });
});
