const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require(process.env.SKILL + "/scripts/apply_theme.js");

const REPO = process.env.REPO;
const OUT = process.argv[2] || "split_computing_talk.pptx";

const THEME = {
  name: "Split Computing",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "14232E", lt1: "FFFFFF", dk2: "1F3A4D", lt2: "EEF3F5",
    accent1: "1B8A7A", // teal: local / winner
    accent2: "E8613C", // signal orange: network / offload
    accent3: "3D6F99", // steel blue: splits
    accent4: "E5A23A", // amber: server
    accent5: "7A8C99", // grey
    accent6: "B23A48",
    hlink: "3D6F99", folHlink: "7A8C99",
  },
};
const HEX = THEME.colors;
const MUTED = "5E6E7A";

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(Comp, { color: "#" + color, size: String(size) })
  );
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
  pres.title = "Network-Aware Split Computing for Edge AI";
  pres.author = "Chih-Kuan Ho";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;
  const W = 13.333;

  // ---------- layouts ----------
  pres.defineSlideMaster({
    title: "Title dark",
    background: { color: HEX.dk1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.0, w: 11.7, h: 1.9, fontFace: "Cambria", fontSize: 40, bold: true, color: C.background1, valign: "bottom", align: "left" }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.1, w: 11.7, h: 1.6, fontSize: 18, color: "C9D6DE", valign: "top" }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "Content",
    background: { color: HEX.lt1 },
    margin: [0.5, 0.6, 0.6, 0.6],
    slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: MUTED, align: "right" },
    objects: [
      { text: { text: "EE289 · Split computing on a two-laptop testbed", options: { x: 0.6, y: 7.0, w: 6, h: 0.3, fontSize: 10, color: MUTED } } },
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.9, fontFace: "Cambria", fontSize: 32, bold: true, color: C.text1, valign: "middle" }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "Closing dark",
    background: { color: HEX.dk1 },
    slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: "9FB3C0", align: "right" },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.9, fontFace: "Cambria", fontSize: 32, bold: true, color: C.background1, valign: "middle" }, text: "" } },
    ],
  });

  const ic = {
    laptop: await icon(fa.FaLaptop, HEX.lt1),
    server: await icon(fa.FaServer, HEX.lt1),
    wifi: await icon(fa.FaWifi, HEX.lt1),
    layers: await icon(fa.FaLayerGroup, HEX.lt1),
    stopwatch: await icon(fa.FaStopwatch, HEX.lt1),
    route: await icon(fa.FaRoute, HEX.lt1),
    warn: await icon(fa.FaExclamationTriangle, HEX.lt1),
    check: await icon(fa.FaCheckCircle, HEX.lt1),
    chip: await icon(fa.FaMicrochip, HEX.lt1),
    flask: await icon(fa.FaFlask, HEX.lt1),
    chart: await icon(fa.FaChartBar, HEX.lt1),
    plug: await icon(fa.FaNetworkWired, HEX.lt1),
  };
  const iconCircle = (s, img, x, y, d, fill, name) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" }, objectName: name + " circle" });
    const p = d * 0.26;
    s.addImage({ data: img, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, objectName: name + " icon", altText: "" });
  };
  const card = (s, x, y, w, h, name, fill = C.background2) =>
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { type: "none" }, objectName: name });
  const txt = (s, text, o) => s.addText(text, Object.assign({ isTextBox: true, fontSize: 16, color: C.text1, valign: "top", margin: 0 }, o));

  // ---------- 1. Title ----------
  pres.addSection({ title: "Introduction" });
  let s = pres.addSlide({ masterName: "Title dark", sectionTitle: "Introduction" });
  s.addText("Network-Aware Split Computing for Edge AI", { placeholder: "title" });
  s.addText([
    { text: "Where does splitting a CNN between an edge device and a server actually pay off?", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 10 } },
    { text: "Chih-Kuan Ho · EE289 Course Project · Fall 2026", options: { fontSize: 16, color: "9FB3C0" } },
  ], { placeholder: "body" });
  s.addNotes(
    "Hi, I'm Chih-Kuan. My project is a measurement study of split computing: running part of a neural network on an edge device and the rest on a server. " +
    "The question is a practical one: for a given network link, should a device run the model itself, send the whole image to a server, or send something in between? " +
    "I built a two-laptop testbed to answer it, and the short answer from the first full run is surprising: on this hardware, the device should just run the model itself. " +
    "I'll show why, and what I'm checking next before I trust that answer. (About 30 seconds.)"
  );

  // ---------- 2. Motivation ----------
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Introduction" });
  s.addText("Three ways to run one camera frame through a CNN", { placeholder: "title" });
  const strat = [
    { t: "Full local", d: "Edge runs the whole model.\nNo network, but limited by edge compute.", c: C.accent1, img: ic.laptop },
    { t: "Full offload", d: "Edge sends the raw frame.\nServer GPU does everything.", c: C.accent2, img: ic.server },
    { t: "Split", d: "Edge runs the first layers and sends the intermediate activation.", c: C.accent3, img: ic.layers },
  ];
  strat.forEach((o, i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.55, 3.8, 3.3, "strategy card " + (i + 1));
    iconCircle(s, o.img, x + 0.35, 1.85, 0.9, o.c, o.t);
    txt(s, o.t, { x: x + 0.35, y: 2.95, w: 3.1, h: 0.5, fontSize: 22, bold: true, fontFace: "Cambria" });
    txt(s, o.d, { x: x + 0.35, y: 3.5, w: 3.1, h: 1.2, fontSize: 16, color: C.text2 });
  });
  txt(s, [
    { text: "The textbook pitch for splitting: ", options: { bold: true } },
    { text: "later layers shrink the data, so a well-placed cut can send less than the image while using the server's GPU. Whether that holds depends on bandwidth, round-trip time and how big the activation really is." },
  ], { x: 0.6, y: 5.2, w: 12.1, h: 1.2, fontSize: 18, color: C.text1 });
  s.addNotes(
    "There are three basic strategies. Full local: the edge runs everything, so there's no network cost, but edge compute is slow. " +
    "Full offload: send the raw frame to a GPU server. And split computing, from work like Neurosurgeon: run the first few layers on the edge and send the intermediate activation. " +
    "The argument for splitting is that deeper layers produce smaller data, so you might send fewer bytes than the image and still use the GPU. " +
    "Whether that actually works depends on the link and on the real size of the activation, which is what I measured. (About 50 seconds.)"
  );

  // ---------- 3. Research question ----------
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Introduction" });
  s.addText("Research question and scope", { placeholder: "title" });
  card(s, 0.6, 1.55, 12.1, 1.55, "question card", C.text2);
  txt(s, "For which uplink bandwidths (1–100 Mbit/s) and round-trip times (5–150 ms) does offloading an intermediate activation beat full on-device inference or full raw-frame offloading, and which split point is best?",
    { x: 0.95, y: 1.75, w: 11.4, h: 1.2, fontSize: 20, color: C.background1, italic: true, valign: "middle" });
  const stats = [
    ["1", "CNN backbone", "ResNet-50, 224 × 224, pretrained, no compression"],
    ["6", "configurations", "full local, full offload, 4 split points"],
    ["4", "network profiles", "10 / 100 Mbit/s × 20 / 100 ms one-way delay"],
    ["4,800", "measured requests", "N = 200 per cell after 20 warm-up"],
  ];
  stats.forEach((st, i) => {
    const x = 0.6 + i * 3.1;
    txt(s, st[0], { x, y: 3.55, w: 2.9, h: 1.0, fontSize: 54, bold: true, color: C.accent1, fontFace: "Cambria" });
    txt(s, st[1], { x, y: 4.6, w: 2.9, h: 0.4, fontSize: 18, bold: true });
    txt(s, st[2], { x, y: 5.05, w: 2.8, h: 0.9, fontSize: 14, color: MUTED });
  });
  s.addNotes(
    "Here is the research question, unchanged from my proposal. For which bandwidths and round-trip times does sending an intermediate activation beat both running locally and sending the raw frame, and which split point is best? " +
    "The scope is deliberately small: one model, ResNet-50, with no compression; six configurations; a two-by-two network matrix; and 200 measured requests per cell, so 4,800 requests in total. " +
    "Following the instructor's feedback, I prioritized a working testbed and reliable baselines before widening the matrix. (About 45 seconds.)"
  );

  // ---------- 4. Testbed ----------
  pres.addSection({ title: "Method" });
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Method" });
  s.addText("Testbed: two Windows laptops on one subnet", { placeholder: "title" });
  // edge box
  card(s, 0.6, 1.6, 4.0, 2.6, "edge card");
  iconCircle(s, ic.laptop, 0.9, 1.85, 0.85, C.accent1, "edge");
  txt(s, "Edge laptop", { x: 1.95, y: 1.95, w: 2.5, h: 0.6, fontSize: 22, bold: true, fontFace: "Cambria", valign: "middle" });
  txt(s, "Intel CPU only, on Wi-Fi\nRuns layers up to the split\nApp-level link shaper", { x: 0.9, y: 2.9, w: 3.5, h: 1.2, fontSize: 16, color: C.text2 });
  // server box
  card(s, 8.7, 1.6, 4.0, 2.6, "server card");
  iconCircle(s, ic.server, 9.0, 1.85, 0.85, C.accent4, "server");
  txt(s, "Server laptop", { x: 10.05, y: 1.95, w: 2.5, h: 0.6, fontSize: 22, bold: true, fontFace: "Cambria", valign: "middle" });
  txt(s, "RTX 4060, wired\nRuns the remaining layers\nCUDA-event timing", { x: 9.0, y: 2.9, w: 3.5, h: 1.2, fontSize: 16, color: C.text2 });
  // link
  s.addShape(pres.shapes.LINE, { x: 4.8, y: 2.9, w: 3.7, h: 0, line: { color: C.accent2, width: 3, beginArrowType: "triangle", endArrowType: "triangle" }, objectName: "link arrow" });
  txt(s, "TCP, length-prefixed tensors", { x: 4.8, y: 2.35, w: 3.7, h: 0.4, fontSize: 14, color: C.text2, align: "center" });
  txt(s, "rate cap + one-way delay each way", { x: 4.8, y: 3.05, w: 3.7, h: 0.4, fontSize: 14, color: C.accent2, bold: true, align: "center" });
  // bottom points
  const tb = [
    [ic.check, "Correct by construction", "Unit test: edge half + server half = full model output, for every split point."],
    [ic.stopwatch, "Per-stage timing", "Edge compute, serialize, network, server time logged for every request."],
    [ic.route, "Three shaping back ends", "App-level (used here), Windows QoS, Linux tc/netem via Ubuntu USB."],
  ];
  tb.forEach((t, i) => {
    const x = 0.6 + i * 4.1;
    iconCircle(s, t[0], x, 4.75, 0.6, C.text2, t[1]);
    txt(s, t[1], { x: x + 0.8, y: 4.75, w: 3.1, h: 0.45, fontSize: 17, bold: true });
    txt(s, t[2], { x: x + 0.8, y: 5.25, w: 3.1, h: 1.2, fontSize: 14, color: MUTED });
  });
  s.addNotes(
    "The testbed is two Windows laptops on the same subnet. The edge is a CPU-only Intel laptop on Wi-Fi; the server is an RTX 4060 laptop on a wired connection. " +
    "The client runs the model up to the cut, serializes the tensor in a simple length-prefixed binary format, and sends it over TCP. The server finishes the model and returns the result. " +
    "Because Windows has no netem, the link is shaped at the application level: a token-bucket rate cap plus a fixed delay applied in each direction. " +
    "A unit test checks that the two halves together give exactly the full model's output, and every request logs the time spent in each stage. (About 50 seconds.)"
  );

  // ---------- 5. Matrix + RTT convention ----------
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Method" });
  s.addText("Experiment matrix and the delay convention", { placeholder: "title" });
  const hdr = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 } } });
  const rows = [
    [hdr("Configuration"), hdr("Edge runs"), hdr("Sends"), hdr("Bytes")],
    ["Full local", "everything", "nothing", "0"],
    ["Full offload", "nothing", "uint8 frame 3×224×224", "151 KB"],
    ["Split A", "stem + layer1", "256×56×56 fp32", "3.2 MB"],
    ["Split B", "through layer2", "512×28×28 fp32", "1.6 MB"],
    ["Split C", "through layer3", "1024×14×14 fp32", "803 KB"],
    ["Split D", "through layer4", "2048×7×7 fp32", "402 KB"],
  ];
  s.addTable(rows, { x: 0.6, y: 1.6, w: 7.2, colW: [1.6, 1.8, 2.6, 1.2], fontSize: 14, color: C.text1, border: { type: "solid", pt: 0.5, color: "D5DEE3" }, rowH: 0.56, valign: "middle", margin: [0, 0.1, 0, 0.1] });
  txt(s, "× 4 profiles: 10 or 100 Mbit/s, 20 or 100 ms one-way", { x: 0.6, y: 5.75, w: 7.2, h: 0.4, fontSize: 16, bold: true, color: C.accent2 });
  txt(s, "Each cell: 20 warm-up + 200 measured requests. Median is the main statistic.", { x: 0.6, y: 6.2, w: 7.2, h: 0.4, fontSize: 14, color: MUTED });
  // RTT callout
  card(s, 8.3, 1.6, 4.4, 4.95, "RTT convention card");
  txt(s, "One-way delay vs RTT", { x: 8.6, y: 1.85, w: 3.8, h: 0.5, fontSize: 20, bold: true, fontFace: "Cambria" });
  txt(s, [
    { text: "Delay is one-way, applied on uplink and downlink.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 8 } },
    { text: "RTT = 2 × delay + physical RTT", options: { bold: true, color: C.accent2, breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 8 } },
    { text: "20 ms → 40 ms emulated RTT", options: { breakLine: true } },
    { text: "100 ms → 200 ms emulated RTT", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 8 } },
    { text: "Physical path adds ≈ 3–4 ms, derived from the data (ICMP is blocked on Windows).", options: { color: MUTED, fontSize: 14 } },
  ], { x: 8.6, y: 2.45, w: 3.8, h: 3.6, fontSize: 16 });
  s.addNotes(
    "This is the matrix. Six configurations: full local, full offload, and four split points after each ResNet stage. I added split D after layer4 because the first three all send more than the raw frame. " +
    "Each runs under four network profiles. One point the instructor asked me to be precise about: the delay in a profile is one-way, applied in both directions, so 20 ms means a 40 ms emulated round trip and 100 ms means 200 ms. " +
    "On top of that, the real Wi-Fi path adds about 3 to 4 ms. I couldn't ping the server because Windows blocks ICMP, so I derived it from the data: network time minus the emulated RTT and the transfer time. (About 60 seconds.)"
  );

  // ---------- 6. Headline result ----------
  pres.addSection({ title: "Results" });
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Results" });
  s.addText("Full local wins every profile", { placeholder: "title" });
  const prof = ["10 Mbit/s\n40 ms RTT", "10 Mbit/s\n200 ms RTT", "100 Mbit/s\n40 ms RTT", "100 Mbit/s\n200 ms RTT"];
  const med = [
    ["Full local", 46.1, 37.4, 37.2, 37.0],
    ["Full offload", 199.8, 360.5, 91.4, 252.5],
    ["Split A", 2668.2, 2823.8, 353.0, 513.4],
    ["Split B", 1377.8, 1536.6, 221.0, 383.3],
    ["Split C", 735.3, 896.2, 156.8, 318.9],
    ["Split D", 409.2, 569.7, 118.6, 279.7],
  ];
  const fmt = (v) => v.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  const trows = [[hdr("Median e2e (ms)"), ...prof.map((p) => ({ text: p, options: { bold: true, color: C.background1, fill: { color: C.text2 }, align: "center" } }))]];
  med.forEach((r, i) => {
    const win = i === 0;
    trows.push([
      { text: r[0], options: { bold: win, color: win ? C.background1 : C.text1, fill: { color: win ? C.accent1 : C.background1 } } },
      ...r.slice(1).map((v) => ({ text: fmt(v), options: { align: "center", bold: win, color: win ? C.background1 : C.text1, fill: { color: win ? C.accent1 : C.background1 } } })),
    ]);
  });
  s.addTable(trows, { x: 0.6, y: 1.6, w: 7.9, colW: [1.9, 1.5, 1.5, 1.5, 1.5], fontSize: 15, border: { type: "solid", pt: 0.5, color: "D5DEE3" }, rowH: [0.8, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6], valign: "middle", margin: [0, 0.1, 0, 0.1] });
  // callouts
  const calls = [
    ["37–46 ms", "full local, every profile"],
    ["91 ms", "best offload: raw frame at 100 Mbit/s, 40 ms RTT"],
    ["4 / 4", "winners predicted by the additive latency model"],
  ];
  calls.forEach((c, i) => {
    const y = 1.6 + i * 1.6;
    txt(s, c[0], { x: 9.0, y, w: 3.7, h: 0.75, fontSize: 40, bold: true, fontFace: "Cambria", color: i === 0 ? C.accent1 : C.text2 });
    txt(s, c[1], { x: 9.0, y: y + 0.75, w: 3.7, h: 0.6, fontSize: 14, color: MUTED });
  });
  txt(s, "Model: edge + server + RTT + bytes × 8 / bandwidth, fitted from measured medians.", { x: 0.6, y: 6.2, w: 7.9, h: 0.4, fontSize: 14, color: MUTED });
  s.addNotes(
    "Here's the headline. Each number is the median end-to-end latency over 200 requests. Full local, highlighted, wins every one of the four profiles at 37 to 46 ms. " +
    "The best any offloading strategy does is 91 ms: sending the raw frame at 100 Mbit/s and a 40 ms round trip. Every split is worse than raw offload, and split A at 10 Mbit/s takes over two and a half seconds. " +
    "I also fitted a simple additive model, edge time plus server time plus RTT plus transfer time, from the measured medians. It predicts the winner in all four cells, which matters because it's what I'll use to choose where to measure next. " +
    "The 46 ms in the first column is likely warm-up or CPU frequency ramp on the edge, not a network effect, since full local never touches the network. (About 60 seconds.)"
  );

  // ---------- 7. Payload ----------
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Results" });
  s.addText("Why: every split sends more bytes than the image", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [{ name: "KB sent", labels: ["Full offload (raw frame)", "Split A (layer1)", "Split B (layer2)", "Split C (layer3)", "Split D (layer4)"], values: [151, 3211, 1606, 803, 402] }], {
    x: 0.6, y: 1.5, w: 8.0, h: 5.2, barDir: "bar", catAxisOrientation: "maxMin",
    chartColors: [HEX.accent2, HEX.accent3, HEX.accent3, HEX.accent3, HEX.accent3], varyColors: true,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "#,##0\" KB\"", dataLabelFontSize: 13, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt",
    catAxisLabelColor: HEX.dk2, catAxisLabelFontSize: 14, catAxisLabelFontFace: "+mn-lt",
    valAxisLabelColor: MUTED, valAxisLabelFontSize: 12, valAxisLabelFontFace: "+mn-lt", valAxisMaxVal: 4000, valAxisLabelFormatCode: "#,##0",
    valGridLine: { color: "E1E7EA", size: 0.75 }, catGridLine: { style: "none" }, showLegend: false,
    showTitle: true, title: "Bytes sent per request (KB)", titleFontSize: 14, titleColor: HEX.dk2, titleFontFace: "+mn-lt",
    barGapWidthPct: 60,
  });
  card(s, 9.0, 1.6, 3.7, 4.9, "payload takeaway card");
  txt(s, "2.7–21×", { x: 9.3, y: 1.85, w: 3.2, h: 0.9, fontSize: 48, bold: true, fontFace: "Cambria", color: C.accent3 });
  txt(s, "larger than the 151 KB raw frame", { x: 9.3, y: 2.75, w: 3.2, h: 0.5, fontSize: 16, color: C.text2 });
  txt(s, [
    { text: "Lossless fp32 activations vs a uint8 image: 4 bytes per value vs 1.", options: { bullet: true, breakLine: true } },
    { text: "Later split = fewer bytes, so the ranking is always D < C < B < A.", options: { bullet: true, breakLine: true } },
    { text: "No uncompressed split can beat raw offload.", options: { bullet: true, bold: true } },
  ], { x: 9.3, y: 3.45, w: 3.2, h: 2.9, fontSize: 15, color: C.text1, paraSpaceAfter: 8 });
  s.addNotes(
    "Why do splits lose so badly? Payload. The raw frame is 151 KB as uint8. The activations are lossless fp32, four bytes per value, and the early feature maps are big: 3.2 MB after layer1, still 402 KB after layer4. " +
    "So every split sends between 2.7 and 21 times more bytes than just sending the image. That also explains the ranking: later splits send less, so D beats C beats B beats A, in every profile. " +
    "Without compression or quantization, no split point in ResNet-50 can beat raw offloading. That's consistent with the split computing literature, which relies on learned compression at the cut. (About 50 seconds.)"
  );

  // ---------- 8. Breakdown ----------
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Results" });
  s.addText("Where the time goes: the network dominates", { placeholder: "title" });
  s.addImage({ path: REPO + "/report/fig_stages_real.png", x: 0.6, y: 1.45, w: 12.1, h: 12.1 * 550 / 1672, altText: "Stacked bars of median latency by stage (edge compute, serialize, network, server) for each configuration at 10 and 100 Mbit/s with 40 ms RTT. Network time dominates every offloaded configuration." , objectName: "stage breakdown figure" });
  const bk = [
    ["82–98 %", "of offloaded latency is network at 10 Mbit/s", C.accent2],
    ["61–90 %", "at 100 Mbit/s", C.accent2],
    ["≤ 2.3 ms", "serialization, even for the 3.2 MB tensor", C.text2],
  ];
  bk.forEach((b, i) => {
    const x = 0.6 + i * 4.1;
    txt(s, b[0], { x, y: 5.6, w: 3.8, h: 0.7, fontSize: 34, bold: true, fontFace: "Cambria", color: b[2] });
    txt(s, b[1], { x, y: 6.3, w: 3.8, h: 0.5, fontSize: 14, color: MUTED });
  });
  s.addNotes(
    "This breaks each median into stages, at the 40 ms RTT profiles. Note the two panels have different scales. Green is network time, which includes the round trip and the transfer. " +
    "For every offloaded configuration, network time is 82 to 98 percent of latency at 10 Mbit/s and 61 to 90 percent at 100 Mbit/s. " +
    "Serialization, in orange, is basically invisible: at most 2.3 ms even for the biggest tensor, so it's not a bottleneck. " +
    "The 200 ms RTT profiles look the same with about 160 ms more green on every bar. (About 45 seconds.)"
  );

  // ---------- 9. Crossover ----------
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Results" });
  s.addText("No crossover inside the studied range, with this server", { placeholder: "title" });
  // budget bars (ms scale)
  const sx = 2.9, scale = 0.115; // inches per ms
  const bars = [
    { l: "Full local", segs: [[37, HEX.accent1, "edge 37"]] },
    { l: "Offload, best case", segs: [[36, HEX.accent4, "server 36"], [5, HEX.accent2, "RTT 5"], [3.5, "F2A58E", ""], [12, HEX.accent2, "transfer 12"]] },
    { l: "Split D, best case", segs: [[41, HEX.accent1, "edge 41"], [2.4, HEX.accent4, ""], [5, HEX.accent2, ""], [32, HEX.accent2, "transfer 32"]] },
  ];
  txt(s, "Latency budget at 100 Mbit/s and the smallest RTT in the question (5 ms), from measured stage times", { x: 0.6, y: 1.5, w: 12.1, h: 0.4, fontSize: 15, color: MUTED });
  bars.forEach((b, i) => {
    const y = 2.1 + i * 0.85;
    txt(s, b.l, { x: 0.6, y, w: 2.2, h: 0.6, fontSize: 15, bold: true, valign: "middle" });
    let x = sx, tot = 0;
    b.segs.forEach((g, j) => {
      const w = g[0] * scale;
      s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.6, fill: { color: g[1] }, line: { color: "FFFFFF", width: 1 }, objectName: b.l + " seg " + j });
      if (g[2]) s.addText(g[2], { isTextBox: true, x, y, w, h: 0.6, fontSize: 12, color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0 });
      x += w; tot += g[0];
    });
    txt(s, "≈ " + Math.round(tot) + " ms", { x: x + 0.15, y, w: 1.4, h: 0.6, fontSize: 16, bold: true, valign: "middle", color: i === 0 ? C.accent1 : C.text1 });
  });
  s.addShape(pres.shapes.LINE, { x: sx + 37 * scale, y: 1.95, w: 0, h: 2.6, line: { color: HEX.accent1, width: 1.5, dashType: "dash" }, objectName: "local threshold line" });
  txt(s, "Physical path ≈ 3–4 ms (light segment). Transfer = bytes × 8 / 100 Mbit/s.", { x: 0.6, y: 4.65, w: 12.1, h: 0.35, fontSize: 13, color: MUTED });
  // takeaways
  card(s, 0.6, 5.15, 12.1, 1.55, "crossover takeaway card", C.background2);
  txt(s, [
    { text: "Server time alone (36 ms) + any RTT ≥ 5 ms already exceeds full local (37 ms).", options: { bullet: true, breakLine: true } },
    { text: "To win at 100 Mbit/s, 5 ms RTT, the server would need to finish ResNet-50 in under ≈ 16 ms.", options: { bullet: true, breakLine: true } },
    { text: "So the next measurements go where a boundary can appear: GPU-verified server, high bandwidth, low RTT.", options: { bullet: true, bold: true } },
  ], { x: 0.9, y: 5.3, w: 11.6, h: 1.3, fontSize: 16, paraSpaceAfter: 4, valign: "middle" });
  s.addNotes(
    "The deliverable I promised was a crossover map. With these numbers the map has no boundary in it: the additive model says full local wins everywhere from 1 to 100 Mbit/s and 5 to 150 ms RTT. " +
    "This budget view shows why. Take the most favourable case in the question: 100 Mbit/s and a 5 ms round trip. Full local is 37 ms. Offload needs 36 ms of server time before any network at all, so it's already over. Split D needs 41 ms of edge compute alone. " +
    "Working backwards, with the 3 to 4 ms physical path, offload would only win if the server ran ResNet-50 in under about 16 ms. " +
    "That's where the instructor's advice about densifying near the crossover comes in: the analysis writes out the candidate boundary points, and the extended sweep will sample there, at high bandwidth and low RTT, once the server is verified. (About 60 seconds.)"
  );

  // ---------- 10. Tail ----------
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Results" });
  s.addText("Tail latency: indicative only at N = 200", { placeholder: "title" });
  const tw = 7.8, th = tw * 760 / 1500;
  s.addImage({ path: REPO + "/results/fig4_tail.png", x: 0.5, y: 1.5, w: tw, h: th, altText: "Median and p99 end-to-end latency for each configuration and profile on a log scale. Most p99 values sit close to the median; full offload at 100 Mbit/s and 40 ms RTT has the widest spread.", objectName: "tail figure" });
  card(s, 8.5, 1.6, 4.2, 4.9, "tail card");
  txt(s, "p99 rests on the 2 slowest requests", { x: 8.8, y: 1.85, w: 3.7, h: 0.8, fontSize: 18, bold: true, fontFace: "Cambria" });
  txt(s, [
    { text: "Most network-bound cells: p99 within 1.1× of the median.", options: { bullet: true, breakLine: true } },
    { text: "Full offload, 100 Mbit/s, 40 ms RTT: p99 133.6 ms (95 % CI 122–144), 1.46× median.", options: { bullet: true, breakLine: true } },
    { text: "Split C, 100 Mbit/s, 200 ms RTT: p99 340 ms, CI 334–511.", options: { bullet: true, breakLine: true } },
    { text: "Plan: N = 1,000 for cells used in tail claims.", options: { bullet: true, bold: true } },
  ], { x: 8.8, y: 2.75, w: 3.7, h: 3.6, fontSize: 15, paraSpaceAfter: 8 });
  s.addNotes(
    "The instructor cautioned about p99 with limited runs, and that's right. With 200 requests, the 99th percentile is decided by the two slowest. " +
    "So I report p99 with a 95 percent bootstrap interval. For most network-bound cells, p99 is within 10 percent of the median, which makes sense because the app-level shaper paces bytes deterministically. " +
    "The widest is full offload at 100 Mbit/s and 40 ms: p99 of 134 ms, 1.46 times the median. And split C at 200 ms RTT has an interval from 334 to 511 ms, which tells you the estimate isn't stable. " +
    "With the edge on Wi-Fi, I treat all of these as indicative, and the tail cells will be re-run with 1,000 requests. (About 50 seconds.)"
  );

  // ---------- 11. Limitations ----------
  pres.addSection({ title: "Wrap-up" });
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Wrap-up" });
  s.addText("What these results do not yet show", { placeholder: "title" });
  const lim = [
    [ic.chip, "Server looks too slow", "36 ms for ResNet-50 on an RTX 4060 is suspicious, and server time falls with later splits (34 → 2 ms), which looks like CPU or a low GPU power state. Result holds for this server, not GPUs in general.", C.accent6],
    [ic.wifi, "No real network dynamics", "App-level shaping paces bytes exactly: no router queue, congestion window or retransmission, so socket-buffer queuing isn't measured yet.", C.accent2],
    [ic.plug, "Wi-Fi edge, no ping baseline", "Wi-Fi adds jitter and ≈ 3–4 ms. ICMP blocked, so the physical RTT was derived, not measured.", C.accent3],
    [ic.laptop, "Edge noise", "Full local was 46 ms in the first profile and 37 ms after, consistent with warm-up or CPU frequency ramp.", C.accent5],
  ];
  lim.forEach((l, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 6.15, y = 1.55 + row * 2.6;
    card(s, x, y, 5.95, 2.35, "limitation card " + (i + 1));
    iconCircle(s, l[0], x + 0.3, y + 0.3, 0.75, l[3], l[1]);
    txt(s, l[1], { x: x + 1.25, y: y + 0.3, w: 4.5, h: 0.75, fontSize: 19, bold: true, valign: "middle" });
    txt(s, l[2], { x: x + 0.3, y: y + 1.15, w: 5.4, h: 1.1, fontSize: 14, color: C.text2 });
  });
  s.addNotes(
    "Before drawing conclusions, here's what these results don't show. The biggest one: the server is suspiciously slow. 36 ms for ResNet-50 on an RTX 4060 is much slower than expected, and server time drops steadily as more of the model moves to the edge, which looks more like CPU execution or a GPU in a low power state. Until I confirm CUDA, the no-offload result is about this server, not GPUs in general. " +
    "Second, the shaper is idealized, with no queues or TCP dynamics. Third, the edge is on Wi-Fi and I couldn't ping, so the physical RTT is derived. And fourth, there's some edge noise from warm-up. (About 60 seconds.)"
  );

  // ---------- 12. Next steps + takeaway ----------
  s = pres.addSlide({ masterName: "Closing dark", sectionTitle: "Wrap-up" });
  s.addText("Next steps", { placeholder: "title" });
  const steps = [
    ["Nov 21–23", "Fix the baseline", "Confirm CUDA on the server (nvidia-smi, max GPU power); re-run full local and full offload on a direct cable with ping and iperf3."],
    ["Nov 24–28", "Repeat the matrix", "GPU-verified server plus Windows QoS shaping; packet captures at 10 Mbit/s; N = 1,000 for tail cells."],
    ["Nov 28–30", "Densify the boundary", "Measure the bandwidth/RTT points the model flags near the crossover, instead of a uniform grid."],
    ["Dec 1", "Final figures", "Payload profile, crossover map, stage and p99 analysis."],
  ];
  steps.forEach((st, i) => {
    const x = 0.6 + i * 3.1;
    s.addShape(pres.shapes.OVAL, { x, y: 1.6, w: 0.55, h: 0.55, fill: { color: C.accent1 }, line: { type: "none" }, objectName: "step " + (i + 1) + " marker" });
    s.addText(String(i + 1), { isTextBox: true, x, y: 1.6, w: 0.55, h: 0.55, fontSize: 18, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
    if (i < 3) s.addShape(pres.shapes.LINE, { x: x + 0.65, y: 1.875, w: 2.35, h: 0, line: { color: "4F6A7C", width: 1.5 }, objectName: "step connector " + (i + 1) });
    txt(s, st[0], { x, y: 2.35, w: 2.9, h: 0.35, fontSize: 14, color: "9FB3C0" });
    txt(s, st[1], { x, y: 2.7, w: 2.9, h: 0.45, fontSize: 19, bold: true, color: C.background1 });
    txt(s, st[2], { x, y: 3.2, w: 2.85, h: 1.6, fontSize: 14, color: "C9D6DE" });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.1, w: 12.1, h: 1.55, rectRadius: 0.12, fill: { color: C.text2 }, line: { type: "none" }, objectName: "takeaway card" });
  txt(s, [
    { text: "Takeaway  ", options: { bold: true, color: "7FD3C4" } },
    { text: "On this testbed, uncompressed split computing never pays off: activations are bigger than the image and the network dominates. Whether offloading can win at all depends on a server that is fast enough, which is the first thing to verify.", options: { color: C.background1 } },
  ], { x: 0.9, y: 5.25, w: 11.5, h: 1.25, fontSize: 17, valign: "middle" });
  txt(s, "Questions?   ·   github.com/KevinCKHo/split-computing-testbed", { x: 0.6, y: 6.95, w: 9, h: 0.35, fontSize: 12, color: "9FB3C0" });
  s.addNotes(
    "Next steps, in order. First, fix the baseline: confirm the server is really running on CUDA, set maximum GPU performance, and re-run the two baselines on a direct cable where I can ping and check bandwidth with iperf3. " +
    "Then repeat the full matrix with the verified server and with Windows QoS shaping for real TCP pacing, plus packet captures and more runs for the tail cells. " +
    "Then densify measurements near wherever the model now places the crossover, and produce the final figures for the presentation and report. " +
    "The takeaway: on this testbed, uncompressed split computing never pays off, because the activations are bigger than the image and the network dominates. Whether offloading can win at all comes down to the server being fast enough, and that's the first thing I'm checking. Thanks, happy to take questions. (About 60 seconds.)"
  );

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
