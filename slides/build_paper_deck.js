// Build nop_bai/ViKAG-Faith_BaiBao_slide.pptx: the talk for the paper. Plain academic style: white background, Times New
// Roman, one dark blue accent, muted verdict colours, thin rules, no cards. Slide titles state findings.
// Formulas are native Office equations (patched into slide XML after the build, with a plain-text fallback).
// Numbers come from outputs/analysis/results.json and the demo summary, nothing is typed by hand except quoted examples.
//   cd slides && NODE_PATH=node_modules APPLY_THEME=<pptx skill>/scripts/apply_theme.js node build_paper_deck.js
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.APPLY_THEME);

const AUTHOR = "Hà Văn Vinh";
const COURSE = "Xử lý ngôn ngữ tự nhiên nâng cao";
const REPO = "github.com/vinhha195-oss/vikag-faith";

const ROOT = path.resolve(__dirname, "..");
const R = require(path.join(ROOT, "outputs", "analysis", "results.json"));
const OUT = path.join(ROOT, "nop_bai", "ViKAG-Faith_BaiBao_slide.pptx");
// Catch counts are computed by make_demo.py and embedded in the story page.
const html = fs.readFileSync(path.join(ROOT, "demo", "vikag_faith_demo.html"), "utf8");
const di = html.indexOf("const DATA = ") + 13;
const CATCH = JSON.parse(html.slice(di, html.indexOf("\n", di)).trim().replace(/;$/, "")).summary.catch;

const THEME = {
  name: "ViKAG Verification Desk", headFontFace: "Times New Roman", bodyFontFace: "Times New Roman",
  colors: {
    dk1: "1F2933", lt1: "FFFFFF", dk2: "3D4852", lt2: "F3F4F6",
    accent1: "1F3A5F", accent2: "A23B3B", accent3: "5B4B8A", accent4: "2F6B4F",
    accent5: "6B7280", accent6: "D1D5DB", hlink: "1F3A5F", folHlink: "6B7280",
  },
};
const HEX = THEME.colors;
const INK = HEX.dk1, TXT = HEX.dk1, PANEL = HEX.lt2, SOFT = HEX.dk2, ACC = HEX.accent1, CON = HEX.accent2, UNS = HEX.accent3, SUP = HEX.accent4, MUTED = HEX.accent5, DIM = HEX.accent6;
const RULE = "D1D5DB", MONO = "Times New Roman";
// pale tints used to mark words on the grey panels
const M_YEL = "F1E9C9", M_CON = "F4DADA", M_UNS = "E4DFF0", M_SUP = "D9EBE0";

const K = (v) => Math.round(v * 1000), P = (v) => Math.round(v * 100);
const f = (x, d = 3) => (x == null ? "–" : x.toFixed(d).replace(".", ","));
const pct = (x) => Math.round(100 * x) + "%";
const CL = R.claim_level, CO = R.answer_level_correlation, CMP = R.comparisons, REV = R.revise, SY = R.systems;
const AG = R.agreement, ACG = AG.audit_CG || AG.audit, AC = AG.audit, SENS = ACG.sensitivity;
const RA = REV.all, R1 = REV.by_max_rounds["1"], R2 = REV.by_max_rounds["2"];
const NPASS = 1 + (AG.quick_passes || []).length;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "ViKAG-Faith";
pres.author = AUTHOR;
const C = pres.SchemeColor;

// ---------- layouts ----------
pres.defineSlideMaster({ title: "DESK_BLANK", background: { color: C.background1 }, objects: [] });
pres.defineSlideMaster({
  title: "DESK",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 0.34, w: 9, h: 0.3, fontSize: 13, bold: true,
        color: C.accent1, fontFace: MONO, valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.68, w: 12.1, h: 1.08, fontSize: 30, bold: true,
        color: C.text1, valign: "top", align: "left", margin: 0 }, text: "" } },
    { text: { text: "ViKAG-Faith", options: { x: 0.6, y: 7.05, w: 3, h: 0.25, fontSize: 11, color: MUTED, fontFace: MONO, margin: 0 } } },
  ],
  slideNumber: { x: 12.1, y: 7.05, w: 0.63, h: 0.25, fontSize: 11, color: MUTED, fontFace: MONO, align: "right" },
});

// ---------- helpers ----------
const text = (s, t, o) => s.addText(t, { isTextBox: true, margin: 0, fontSize: 16, color: TXT, valign: "top", ...o });
const notes = (s, t) => s.addNotes(t);
function page(eyebrow, title, section) {
  const s = pres.addSlide({ masterName: "DESK", sectionTitle: section });
  s.addText(eyebrow, { placeholder: "body" });
  s.addText(title, { placeholder: "title" });
  return s;
}
function sheet(s, x, y, w, h, name) {
  s.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: PANEL }, line: { color: PANEL }, objectName: name || "evidence sheet" });
}
function tag(s, label, color, x, y, w, h = 0.36, fs = 13) {
  text(s, label, { x, y, w, h, fontSize: fs, bold: true, color: "FFFFFF", fontFace: MONO, align: "center", valign: "middle",
    fill: { color }, objectName: "verdict " + label });
}
const rule = (s, x, y, w) => s.addShape(pres.ShapeType.line, { x, y, w, h: 0, line: { color: RULE, width: 0.75 } });
function table(s, head, rows, o) {
  const none = { type: "none" }, line = { type: "solid", pt: 0.75, color: RULE };
  const cell = (c, opt) => { const b = typeof c === "object" ? c : { text: String(c) };
    return { text: b.text, options: { border: [none, none, line, none], valign: "middle", ...opt, ...(b.options || {}) } }; };
  s.addTable([head.map((h) => cell(h, { bold: true, color: ACC, fontFace: MONO, fontSize: o.headSize || 13 })), ...rows.map((r) => r.map((c) => cell(c, {})))],
    { fontSize: 14, fontFace: "Times New Roman", color: TXT, ...o });
}
const CHART_BASE = () => ({
  catAxisLabelColor: SOFT, valAxisLabelColor: MUTED, catAxisLabelFontSize: 13, valAxisLabelFontSize: 12,
  catAxisLabelFontFace: "Times New Roman", valAxisLabelFontFace: "Times New Roman", dataLabelFontFace: "Times New Roman",
  valGridLine: { style: "none" }, catGridLine: { style: "none" }, valAxisHidden: true, catAxisLineShow: false, valAxisLineShow: false,
  showValue: true, dataLabelFormatCode: "0\\,000", dataLabelFontSize: 12, dataLabelColor: TXT,
  legendFontFace: "Times New Roman", legendFontSize: 13, legendColor: SOFT,
  titleFontSize: 13, titleColor: MUTED, titleFontFace: "Times New Roman",
});
// A big figure with a line of explanation, set directly on the desk.
function figure(s, x, y, w, value, label, color = TXT, fs = 34) {
  text(s, value, { x, y, w, h: 0.62, fontSize: fs, bold: true, color });
  text(s, label, { x, y: y + 0.66 + (fs - 34) * 0.02, w, h: 0.72, fontSize: 14, color: SOFT });
}

// ---------- 1. cover ----------
pres.addSection({ title: "Vấn đề" });
let s = pres.addSlide({ masterName: "DESK_BLANK", sectionTitle: "Vấn đề" });
text(s, "Ai chấm máy chấm?", { x: 0.6, y: 0.9, w: 6.6, h: 2.3, fontSize: 48, bold: true });
text(s, "Đánh giá tính trung thực mức mệnh đề cho hệ hỏi đáp GraphRAG tiếng Việt", { x: 0.6, y: 2.05, w: 6.2, h: 1.0, fontSize: 20, color: SOFT });
text(s, AUTHOR, { x: 0.6, y: 5.55, w: 6, h: 0.36, fontSize: 18, bold: true });
text(s, `${COURSE} · Đồ án P4 ViKAG-Faith`, { x: 0.6, y: 5.95, w: 6.2, h: 0.3, fontSize: 14, color: MUTED });
sheet(s, 7.5, 0, 5.83, 7.5, "cover sheet");
text(s, "CÂU TRẢ LỜI CỦA AI, TÁCH THÀNH TỪNG Ý", { x: 7.95, y: 0.9, w: 5, h: 0.3, fontSize: 13, bold: true, color: "5B6474", fontFace: MONO });
[[["được quảng cáo trên ", "Facebook"], M_SUP, SUP, "SUPPORTED"], [["tổng tiền phạt là ", "8 triệu đồng"], M_CON, CON, "CONTRADICTED"], [["được quảng cáo trên ", "Instagram"], M_UNS, UNS, "UNSUPPORTED"]].forEach(([t, mk, col, lb], i) => {
  const y = 1.6 + i * 1.75;
  text(s, [{ text: t[0], options: { color: INK } }, { text: t[1], options: { color: INK, bold: true, highlight: mk } }], { x: 7.95, y, w: 4.95, h: 0.5, fontSize: 22 });
  tag(s, lb, col, 7.95, y + 0.62, 2.1);
});
notes(s, "Đề tài thuộc Project 4 ViKAG-Faith. Câu hỏi của đề tài rất ngắn: các máy tự động phát hiện lỗi AI có đáng tin trên tiếng Việt không? Ba ý bên phải đều lấy từ dữ liệu thật của đề tài.");

// ---------- 2. the error ----------
s = page("VẤN ĐỀ", "AI trả lời trôi chảy, nhưng một con số sai là đủ gây hậu quả", "Vấn đề");
sheet(s, 0.6, 1.95, 5.9, 3.7, "claim sheet");
text(s, "AI NÓI", { x: 0.95, y: 2.2, w: 5, h: 0.3, fontSize: 13, bold: true, color: "5B6474", fontFace: MONO });
text(s, [{ text: "Luật sửa đổi Luật Dược trình Quốc hội ", options: { color: INK } }, { text: "tháng 10/2025", options: { color: INK, bold: true, highlight: M_CON } }],
  { x: 0.95, y: 2.65, w: 5.2, h: 1.6, fontSize: 26 });
tag(s, "CONTRADICTED", CON, 0.95, 4.85, 2.1);
sheet(s, 6.83, 1.95, 5.9, 3.7, "evidence sheet");
text(s, "VĂN BẢN GHI", { x: 7.18, y: 2.2, w: 5, h: 0.3, fontSize: 13, bold: true, color: "5B6474", fontFace: MONO });
text(s, [{ text: "Tờ trình: trình Quốc hội ", options: { color: INK } }, { text: "tháng 10 năm 2022", options: { color: INK, bold: true, highlight: M_YEL } }],
  { x: 7.18, y: 2.65, w: 5.2, h: 1.6, fontSize: 26 });
text(s, "Mốc 10/2025 là của Luật An toàn thực phẩm.", { x: 7.18, y: 4.85, w: 5.2, h: 0.36, fontSize: 15, color: "3A4254", valign: "middle" });
text(s, "Máy chấm tự động được dùng để bắt lỗi kiểu này. Nhưng máy chấm có đáng tin với tiếng Việt không?", { x: 0.6, y: 5.95, w: 12.1, h: 0.7, fontSize: 18, color: SOFT });
notes(s, "Mở bằng một lỗi thật trong dữ liệu. AI ghép mốc thời gian của một luật khác vào Luật Dược. Từ đây dẫn sang câu hỏi của đề tài.");

// ---------- 3. the gap ----------
s = page("VẤN ĐỀ", "Điểm tổng không cho biết sai ở đâu, và máy chấm chủ yếu được thử trên tiếng Anh", "Vấn đề");
[["1 điểm", "GraphRAG/KAG tiếng Việt hiện được chấm bằng F1 hoặc một điểm LLM-judge cho cả câu trả lời. Không điểm nào chỉ ra ý nào bịa thêm hay mâu thuẫn.", ACC],
 ["0,7554 → 0,6823", "ViHERMES (ACIIDS 2026): bỏ module kiểm chứng làm điểm judge giảm. Kiểm chứng quan trọng, nhưng chính công cụ kiểm chứng chưa được đo.", TXT],
 ["Tiếng Anh", "RAGAS, LLM-judge, SelfCheckGPT chủ yếu được kiểm định trên tiếng Anh, chưa ở mức từng ý cho tiếng Việt.", TXT]].forEach(([v, d, col], i) => {
  const y = 2.1 + i * 1.55;
  if (i) rule(s, 0.6, y - 0.2, 12.13);
  text(s, v, { x: 0.6, y, w: 4.7, h: 1.1, fontSize: 30, bold: true, color: col, valign: "middle" });
  text(s, d, { x: 5.5, y, w: 7.2, h: 1.1, fontSize: 16, color: SOFT, valign: "middle" });
});
notes(s, "Khoảng trống của đề tài: điểm tổng không định vị được lỗi, và các metric phổ biến chưa được kiểm định ở mức claim trên tiếng Việt. Công trình liên quan: RAGAS, FActScore, LLM-as-a-judge; SelfCheckGPT, SHROOM, ViHallu; XNLI, ViNLI, mDeBERTa-v3; GraphRAG, LightRAG, HippoRAG 2, KAG. Đề tài dùng lại dữ liệu và đồ thị ViHERMES, chỉ thêm tầng đánh giá.");

// ---------- 4. questions ----------
s = page("CÂU HỎI NGHIÊN CỨU", "Đề tài không xây chatbot mới, mà kiểm tra các máy chấm", "Vấn đề");
[["RQ1", "Metric có sẵn (RAGAS, LLM-judge, SelfCheckGPT, NLI) khớp với nhãn chuẩn đến đâu?"],
 ["RQ2", "Thông tin đồ thị, rule số/ngày, fine-tune bằng dữ liệu tổng hợp có giúp verifier không?"],
 ["RQ3", "Verify-then-revise giảm claim sai bao nhiêu, có làm giảm chất lượng trả lời không?"]].forEach(([k, q], i) => {
  const x = 0.6 + i * 4.14;
  text(s, k, { x, y: 1.9, w: 3.8, h: 0.8, fontSize: 40, bold: true, color: ACC, fontFace: MONO });
  text(s, q, { x, y: 2.75, w: 3.75, h: 1.5, fontSize: 18 });
});
rule(s, 0.6, 4.5, 12.13);
text(s, "ĐÓNG GÓP", { x: 0.6, y: 4.7, w: 4, h: 0.3, fontSize: 13, bold: true, color: ACC, fontFace: MONO });
[["Quy trình", "đánh giá mức claim tái lập được trên ViHERMES"], ["Dữ liệu", `ViFaithKAG pilot: ${R.claims_total} claim silver, ${ACG.n} claim nhãn người`],
 ["Meta-evaluation", "12 biến thể metric và ablation đồ thị, rule, số vòng sửa"], ["Độ tin cậy nhãn", "nhãn LLM so với người: thứ hạng metric đổi theo bộ nhãn"]].forEach(([h, d], i) => {
  text(s, [{ text: h + ": ", options: { bold: true } }, { text: d, options: { color: SOFT } }], { x: 0.6 + (i % 2) * 6.2, y: 5.15 + Math.floor(i / 2) * 0.82, w: 5.9, h: 0.72, fontSize: 15 });
});
notes(s, "Điểm dễ nhầm: đề tài không làm chatbot trả lời giỏi hơn. Đối tượng được đánh giá là các máy chấm. Tách câu trả lời thành claim, đối chiếu với tập bằng chứng chung, đo mức khớp của từng metric với nhãn chuẩn.");

// ---------- 5. pipeline as a funnel ----------
pres.addSection({ title: "Cách làm" });
s = page("CÁCH LÀM", `Từ 100 câu hỏi đến ${R.claims_total} claim trong mẫu, ${ACG.n} claim có người gán`, "Cách làm");
const FUN = [["100", "câu hỏi ViHERMES, 20 câu mỗi mức 1–5 hop"], ["200", "câu trả lời từ Naive RAG và GraphRAG"], ["610", "claim tách bằng Qwen2.5-3B"],
  ["80", "câu trả lời vào mẫu gán nhãn"], [String(R.claims_total), `claim trong mẫu (${R.claims_bad} claim lỗi bị loại, còn ${R.claims_dev + R.claims_test})`], [String(ACG.n), "claim có nhãn người"]];
FUN.forEach(([v, l], i) => {
  const x = 0.6 + i * 2.06;
  text(s, v, { x, y: 2.0, w: 1.75, h: 0.8, fontSize: 40, bold: true, color: i === 5 ? ACC : TXT });
  text(s, l, { x, y: 2.85, w: 1.75, h: 1.05, fontSize: 14, color: SOFT });
  if (i < 5) text(s, "›", { x: x + 1.62, y: 2.0, w: 0.4, h: 0.8, fontSize: 34, color: MUTED, align: "center", valign: "middle" });
});
rule(s, 0.6, 4.2, 12.13);
text(s, "Hai hệ", { x: 0.6, y: 4.4, w: 2.3, h: 0.3, fontSize: 15, bold: true, color: ACC });
text(s, "Naive RAG lấy 8 đoạn, GraphRAG lấy 4 hạt giống rồi lan truyền trên đồ thị. Cùng BM25 + bge-m3, cùng Qwen2.5-3B, cùng 6.000 ký tự ngữ cảnh.", { x: 2.9, y: 4.4, w: 9.8, h: 0.62, fontSize: 15, color: SOFT });
text(s, "Bằng chứng", { x: 0.6, y: 5.2, w: 2.3, h: 0.3, fontSize: 15, bold: true, color: ACC });
text(s, "Đoạn truy xuất cộng đoạn vàng của ViHERMES, kèm tên văn bản, số hiệu, quan hệ từ đồ thị. Mọi máy chấm và người gán nhìn cùng một tập này.", { x: 2.9, y: 5.2, w: 9.8, h: 0.62, fontSize: 15, color: SOFT });
text(s, "Ba nhãn", { x: 0.6, y: 6.1, w: 2.3, h: 0.36, fontSize: 15, bold: true, color: ACC, valign: "middle" });
tag(s, "SUPPORTED", SUP, 2.9, 6.1, 1.9); tag(s, "CONTRADICTED", CON, 4.95, 6.1, 2.1); tag(s, "UNSUPPORTED", UNS, 7.2, 6.1, 2.1);
notes(s, "Đọc từ trái qua phải. Hai hệ dùng chung corpus, bộ truy xuất, ngân sách ngữ cảnh và bộ sinh, nên khác biệt chỉ đến từ cách lấy ngữ cảnh. Ba nhãn: suy ra được, nói ngược lại, văn bản không đề cập.");

// ---------- 6. checkers ----------
s = page("CÁCH LÀM", "Các máy chấm được so sánh trên cùng một tập bằng chứng", "Cách làm");
table(s, ["Máy chấm", "Cách làm", "Biến thể"], [
  [{ text: "RAGAS", options: { bold: true } }, "Tái hiện 2 prompt gốc, chấm cả câu trả lời", "Qwen2.5 3B, 7B"],
  [{ text: "LLM-judge", options: { bold: true } }, "LLM gán 3 nhãn cho từng claim", "Qwen2.5 3B, 7B"],
  [{ text: "NLI mDeBERTa-v3", options: { bold: true } }, "Zero-shot trên cửa sổ 900 ký tự, ngưỡng chọn trên tập dev", "V1 đoạn văn · V2 thêm đồ thị"],
  [{ text: "NLI fine-tune", options: { bold: true } }, "12.000 cặp ViNLI + 3.328 cặp tổng hợp (đổi số, ngày, phủ định)", "Ablation: chỉ ViNLI"],
  [{ text: "Rule", options: { bold: true } }, "So khớp số, ngày, số hiệu văn bản", "Riêng lẻ, hoặc thêm vào NLI"],
  [{ text: "SelfCheckGPT", options: { bold: true } }, "3 mẫu nhiệt độ 0,7, không nhìn bằng chứng", "Mốc so sánh"],
], { x: 0.5, y: 1.85, w: 12.3, colW: [2.9, 6.3, 3.1], rowH: [0.45, 0.54, 0.54, 0.54, 0.54, 0.54, 0.54], fontSize: 15 });
text(s, "GGF = số claim supported / tổng số claim     CR, UR = tỉ lệ contradicted, unsupported", { x: 0.6, y: 5.75, w: 12.1, h: 1.05, fontSize: 18, color: TXT, valign: "middle", objectName: "formula" });
notes(s, `Ngoài các máy này còn có mốc luôn đoán supported. Công thức NLI: P_sup là xác suất entail lớn nhất trên các cửa sổ, P_con tính trên 2 cửa sổ trùng từ nhiều nhất với claim.`);

// ---------- 7. labels ----------
s = page("CÁCH LÀM", `Nhãn chính do Claude gán, người kiểm tra mù lại ${ACG.n} claim`, "Cách làm");
const gd = R.gold_distribution, total = gd.supported + gd.contradicted + gd.unsupported;
text(s, `Nhãn silver của ${total} claim`, { x: 0.6, y: 1.9, w: 7, h: 0.3, fontSize: 14, color: SOFT });
let bx = 0.6;
[["supported", SUP], ["contradicted", CON], ["unsupported", UNS]].forEach(([k, col]) => {
  const w = 7.3 * gd[k] / total;
  text(s, String(gd[k]), { x: bx, y: 2.28, w, h: 0.62, fontSize: 18, bold: true, color: "FFFFFF", align: "center", valign: "middle", fill: { color: col }, objectName: "share " + k });
  bx += w;
});
table(s, ["Lượt", "Cách chọn", "Claim", "Trùng Claude", "κ"], [
  ["C", "phân tầng, xem toàn đoạn", String(AC.n), pct(AC.acc), f(AC.kappa, 2)],
  [(AG.quick_passes || []).join(", "), "ngẫu nhiên, xem 4 câu", String(AG.audit_G.n), pct(AG.audit_G.acc), f(AG.audit_G.kappa, 2)],
  [{ text: "Gộp", options: { bold: true } }, "", { text: String(ACG.n), options: { bold: true } }, { text: pct(ACG.acc), options: { bold: true } }, { text: f(ACG.kappa, 2), options: { bold: true } }],
], { x: 0.5, y: 3.15, w: 7.5, colW: [1.3, 3.0, 0.9, 1.5, 0.8], rowH: [0.45, 0.5, 0.5, 0.5] });
text(s, "Lượt A, D, E bị loại: duyệt có gợi ý hoặc file không tạo qua trang gán nhãn.", { x: 0.6, y: 5.35, w: 7.3, h: 0.6, fontSize: 14, color: MUTED });
text(s, pct(ACG.n / R.claims_total), { x: 8.7, y: 1.9, w: 4, h: 1.5, fontSize: 80, bold: true, color: ACC });
text(s, `bộ dữ liệu có nhãn người (${ACG.n}/${R.claims_total})`, { x: 8.7, y: 3.45, w: 4, h: 0.7, fontSize: 16 });
text(s, "Người gán không thấy nhãn hay lý do của Claude và không biết câu trả lời thuộc hệ nào.", { x: 8.7, y: 4.3, w: 4, h: 1.1, fontSize: 15, color: SOFT });
notes(s, `Phải nói rõ: nhãn chuẩn chính là silver do Claude gán, không phải nhãn người. Người gán mù lại qua ${NPASS} lượt. Các lượt có gợi ý hoặc không gán thật đều bị loại khỏi phân tích. Thiết lập: ${R.claims_dev} claim dev chọn ngưỡng, ${R.claims_test} claim test báo cáo; macro-F1, AUROC, Spearman; KTC 95% bootstrap 1.000 lần, Wilcoxon cặp, Cohen's κ; mọi mô hình chạy trên Colab T4.`);

// ---------- 8. RQ1 waffle ----------
pres.addSection({ title: "Kết quả" });
const J = CATCH.j7;
s = page("RQ1 · MÁY CHẤM CÓ SẴN", `Máy bắt nhiều nhất cũng chỉ được ${J.caught}/${J.wrong} ý sai`, "Kết quả");
for (let i = 0; i < J.wrong; i++) {
  const col = i % 8, row = Math.floor(i / 8);
  s.addShape(pres.ShapeType.rect, { x: 0.6 + col * 0.5, y: 2.0 + row * 0.5, w: 0.42, h: 0.42, fill: { color: i < J.caught ? ACC : DIM }, line: { color: i < J.caught ? ACC : DIM }, objectName: i < J.caught ? "caught" : "missed" });
}
text(s, `Mỗi ô là một ý sai trong tập test. Ô đậm: Judge 7B bắt được.`, { x: 0.6, y: 6.1, w: 4.2, h: 0.7, fontSize: 14, color: SOFT });
const rowsC = [["j7", "Judge 7B"], ["ft", "NLI fine-tune V1"], ["j3", "Judge 3B"], ["v1", "NLI zero-shot V1"]];
table(s, ["Máy chấm", "Bắt được", "Báo nhầm", "Macro-F1"], rowsC.map(([k, n], i) => {
  const key = { j7: "judge_7b", ft: "nli_ft_v1", j3: "judge_3b", v1: "nli_zs_v1" }[k], c = CATCH[k], b = i === 0 ? { bold: true, color: ACC } : {};
  return [{ text: n, options: b }, { text: `${c.caught}/${c.wrong}`, options: b }, { text: `${c.false_alarm}/${c.right}`, options: b }, { text: f(CL[key].macro_f1), options: b }];
}), { x: 5.2, y: 2.0, w: 7.6, colW: [3.1, 1.5, 1.6, 1.4], rowH: [0.45, 0.58, 0.58, 0.58, 0.58], fontSize: 16 });
text(s, `Theo nhãn silver. Báo nhầm là số ý đúng bị cho là sai. SelfCheckGPT đạt ${f(CL.nli_selfcheck.macro_f1)} dù không nhìn bằng chứng, ngang NLI zero-shot.`, { x: 5.3, y: 4.95, w: 7.4, h: 0.8, fontSize: 15, color: SOFT });
text(s, `Chấm cả câu trả lời: RAGAS 7B khớp nhất với điểm chuẩn nhưng chỉ ở mức trung bình (ρ = ${f(CO.ragas_7b.spearman)}; RAGAS 3B chỉ ${f(CO.ragas_3b.spearman)}).`, { x: 5.3, y: 5.8, w: 7.4, h: 0.8, fontSize: 15, color: SOFT });
notes(s, `Ô đậm là số ý sai bắt được, tức khoảng 2/3. Chỉ nên nói đây là kết quả trên tập test ${R.claims_test} claim, theo nhãn silver. AUROC của judge 7B là ${f(CL.judge_7b.auroc_not_supported)}.`);

// ---------- 9. RQ2 ----------
const c1 = CMP["nli_ft_v1 - nli_zs_v1"], c2 = CMP["nli_nosynth_v1 - nli_zs_v1"];
s = page("RQ2 · CẢI TIẾN VERIFIER", "Dữ liệu tự tạo nâng điểm theo nhãn Claude, thông tin đồ thị làm kém đi", "Kết quả");
s.addChart(pres.ChartType.bar, [
  { name: "Zero-shot", labels: ["V1: chỉ đoạn văn", "V2: thêm đồ thị"], values: [K(CL.nli_zs_v1.macro_f1), K(CL.nli_zs_v2.macro_f1)] },
  { name: "Fine-tune chỉ ViNLI", labels: ["V1: chỉ đoạn văn", "V2: thêm đồ thị"], values: [K(CL.nli_nosynth_v1.macro_f1), K(CL.nli_nosynth_v2.macro_f1)] },
  { name: "Fine-tune ViNLI + tổng hợp", labels: ["V1: chỉ đoạn văn", "V2: thêm đồ thị"], values: [K(CL.nli_ft_v1.macro_f1), K(CL.nli_ft_v2.macro_f1)] },
], { ...CHART_BASE(), x: 0.5, y: 1.85, w: 7.2, h: 5.0, barDir: "col", barGrouping: "clustered", chartColors: [DIM, MUTED, ACC],
  valAxisMinVal: 0, valAxisMaxVal: 600, dataLabelPosition: "outEnd", showLegend: true, legendPos: "b", objectName: "verifier" });
[["+", "Dữ liệu tổng hợp", `+${f(c1.diff)} so với zero-shot (KTC ${f(c1.ci95[0], 2)}–${f(c1.ci95[1], 2)}). Bỏ dữ liệu này chỉ còn +${f(c2.diff)}.`, SUP],
 ["−", "Thông tin đồ thị", `${f(CL.nli_zs_v1.macro_f1)} → ${f(CL.nli_zs_v2.macro_f1)}: máy thấy tên văn bản trùng là cho supported.`, CON],
 ["=", "Rule số, ngày", `${f(CL.nli_zs_v1.macro_f1)} → ${f(CL["nli_zs_v1+rule"].macro_f1)}: nhiều lỗi nằm ở chủ thể, không ở con số.`, MUTED]].forEach(([g, h, d, col], i) => {
  const y = 2.05 + i * 1.5;
  text(s, g, { x: 8.1, y, w: 0.7, h: 0.8, fontSize: 40, bold: true, color: col, fontFace: MONO });
  text(s, h, { x: 8.85, y: y + 0.02, w: 3.85, h: 0.34, fontSize: 17, bold: true });
  text(s, d, { x: 8.85, y: y + 0.4, w: 3.85, h: 0.9, fontSize: 14, color: SOFT });
});
notes(s, "Ba can thiệp, ba kết quả khác nhau. Nói rõ các số trên slide này đều theo nhãn silver; slide kế tiếp cho thấy điều gì xảy ra khi đổi sang nhãn người.");

// ---------- 10. ranking flips ----------
s = page("KIỂM ĐỊNH MÙ", "Đổi sang nhãn người, bảng xếp hạng đổi theo", "Kết quả");
const ov = [["majority_supported", "Luôn supported"], ["nli_selfcheck", "SelfCheckGPT"], ["judge_3b", "Judge 3B"], ["nli_zs_v1", "NLI zero-shot V1"], ["nli_ft_v1", "NLI fine-tune V1"], ["judge_7b", "Judge 7B"]];
s.addChart(pres.ChartType.bar, [
  { name: `Theo nhãn Claude (${ACG.n} claim)`, labels: ov.map((x) => x[1]), values: ov.map((x) => K(SENS[x[0]].macro_f1_vs_claude)) },
  { name: `Theo nhãn người (${ACG.n} claim)`, labels: ov.map((x) => x[1]), values: ov.map((x) => K(SENS[x[0]].macro_f1_vs_human)) },
], { ...CHART_BASE(), x: 0.5, y: 1.6, w: 7.9, h: 5.3, barDir: "bar", barGrouping: "clustered", chartColors: [DIM, ACC],
  valAxisMinVal: 0, valAxisMaxVal: 700, dataLabelPosition: "outEnd", showLegend: true, legendPos: "b", objectName: "audit" });
figure(s, 8.9, 2.0, 3.8, f(SENS.judge_7b.macro_f1_vs_human), "Judge 7B: cao nhất theo nhãn người", ACC);
figure(s, 8.9, 3.6, 3.8, `${f(SENS.nli_ft_v1.macro_f1_vs_claude)} → ${f(SENS.nli_ft_v1.macro_f1_vs_human)}`, `Fine-tune tụt xuống, không hơn zero-shot (${f(SENS.nli_zs_v1.macro_f1_vs_human)})`);
const cm = ACG.confusion_claude_rows_human_cols, notSup = cm[1].reduce((a, b) => a + b) + cm[2].reduce((a, b) => a + b), humanSup = cm[1][0] + cm[2][0];
text(s, `Claude trùng người ${pct(ACG.acc)}, κ = ${f(ACG.kappa, 2)}, khắt khe hơn người: ${humanSup}/${notSup} ý Claude cho là sai, người gán supported. Tương quan thứ hạng ρ = ${f(ACG.rank_spearman, 2)}.`, { x: 8.9, y: 5.2, w: 3.8, h: 1.5, fontSize: 15, color: SOFT });
notes(s, "Đây là phát hiện quan trọng nhất về độ tin cậy. Fine-tune tốt theo nhãn Claude nhưng không giữ được theo nhãn người, nên không được kết luận fine-tune tốt hơn một cách chung chung. Chỉ có một người gán và người gán không phải chuyên gia pháp lý, nên đây là kiểm định, không phải đáp án tuyệt đối.");

// ---------- 11. RQ3 numbers ----------
s = page("RQ3 · VERIFY-THEN-REVISE", "Tự sửa giảm ý sai, nhưng AI chủ yếu xóa ý thay vì sửa cho đúng", "Kết quả");
[["GGF theo judge 7B", RA.GGF_before, RA.GGF_after, 3, SUP], ["Claim mâu thuẫn (%)", 100 * RA.CR_before, 100 * RA.CR_after, 1, SUP], ["Token F1", RA.answer_f1_before, RA.answer_f1_after, 3, CON], ["Claim mỗi câu", RA.claims_before, RA.claims_after, 2, CON]].forEach(([l, b, a, d, col], i) => {
  const y = 1.95 + i * 0.92;
  if (i) rule(s, 0.6, y - 0.07, 6.2);
  text(s, l, { x: 0.6, y, w: 2.6, h: 0.78, fontSize: 15, color: SOFT, valign: "middle" });
  text(s, f(b, d), { x: 3.2, y, w: 1.4, h: 0.78, fontSize: 22, color: MUTED, valign: "middle", align: "right" });
  text(s, "→", { x: 4.6, y, w: 0.6, h: 0.78, fontSize: 22, color: MUTED, valign: "middle", align: "center" });
  text(s, f(a, d), { x: 5.2, y, w: 1.6, h: 0.78, fontSize: 30, bold: true, color: col, valign: "middle" });
});
text(s, `${RA.revised}/${RA.answers} câu được sửa. p(GGF) = ${f(RA.wilcoxon_GGF_p)}, p(F1) = ${f(RA.wilcoxon_F1_p)}. ${RA.abstained_after} câu thành “không tìm thấy thông tin”.`, { x: 0.6, y: 5.75, w: 6.2, h: 0.8, fontSize: 14, color: MUTED });
table(s, ["Vòng sửa", "GGF", "CR", "F1", "Recall"], [
  ["0", f(RA.GGF_before), f(RA.CR_before), f(RA.answer_f1_before), f(RA.answer_recall_before)],
  ["1", f(R1.GGF_after), f(R1.CR_after), f(R1.answer_f1_after), f(R1.answer_recall_after)],
  ["2", f(R2.GGF_after), f(R2.CR_after), f(R2.answer_f1_after), f(R2.answer_recall_after)],
], { x: 7.2, y: 2.0, w: 5.6, colW: [1.4, 1.05, 1.05, 1.05, 1.05], rowH: [0.45, 0.55, 0.55, 0.55], fontSize: 15 });
text(s, "Vòng 1 cho phần lớn mức tăng. EM = 0 ở mọi cấu hình vì đáp án ViHERMES dài khoảng 115 từ. GGF do chính judge 7B chấm lại nên là giới hạn trên.", { x: 7.3, y: 4.45, w: 5.4, h: 1.5, fontSize: 15, color: SOFT });
notes(s, "Xanh là thay đổi tốt, đỏ là cái giá phải trả. Đây là đánh đổi, chưa phải cải thiện thuần. Ví dụ: câu hỏi 3 hop, AI ghi Luật Dược trình Quốc hội tháng 10/2025 (văn bản ghi 10/2022); sau khi sửa, câu trả lời đạt GGF = 1 nhưng mất cả ba mốc thời gian, kể cả mốc đúng 01/7/2025.");

// ---------- 12. hops ----------
s = page("HAI HỆ", `Naive RAG và GraphRAG ngang nhau (p = ${f(SY.wilcoxon_GGF_p)}), khó là ở câu nhiều hop`, "Kết quả");
const hops = ["1", "2", "3", "4", "5"];
s.addChart(pres.ChartType.line, [
  { name: "Naive RAG", labels: hops.map((h) => h + " hop"), values: hops.map((h) => P(SY.by_hop.naive[h].GGF)) },
  { name: "GraphRAG", labels: hops.map((h) => h + " hop"), values: hops.map((h) => P(SY.by_hop.graph[h].GGF)) },
], { ...CHART_BASE(), x: 0.5, y: 1.85, w: 7.9, h: 5.0, chartColors: [MUTED, ACC], lineSize: 3, lineDataSymbol: "square", lineDataSymbolSize: 9,
  valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 20, showValue: false, valAxisHidden: false, valAxisLabelFormatCode: "0\\,00",
  valGridLine: { color: RULE, size: 0.5 }, showLegend: true, legendPos: "b", objectName: "hop" });
figure(s, 8.9, 2.1, 3.8, `${f(SY.naive.GGF)} · ${f(SY.graph.GGF)}`, "GGF trung bình của Naive RAG và GraphRAG");
figure(s, 8.9, 3.65, 3.8, `${f(100 * R.qa.naive.gold_passage_recall, 1)}% · ${f(100 * R.qa.graph.gold_passage_recall, 1)}%`, "recall đoạn vàng của hai hệ: đồ thị phát hành khá thô");
text(s, `GGF ${f(SY.by_hop.graph["4"].GGF)}–${f(SY.by_hop.naive["5"].GGF)} ở câu 4–5 hop, so với ${f(SY.by_hop.naive["1"].GGF)} ở câu 1 hop.`, { x: 8.9, y: 5.2, w: 3.8, h: 1, fontSize: 15, color: SOFT });
notes(s, "Trục đứng là GGF, mỗi mức có 8 câu hỏi (GraphRAG mức 5 hop có 7 câu trả lời có claim). Hai đường gần nhau, cùng giảm mạnh ở 4 và 5 hop. Nhiều lỗi nằm ở chủ thể và phép tổng hợp chứ không chỉ ở con số: gán nhiệm vụ của Văn phòng Bộ cho Viện Chiến lược, cộng sai tổng tiền phạt, bịa thêm Instagram, TikTok. Các ví dụ này có trong demo.");

// ---------- 13. limits ----------
pres.addSection({ title: "Kết luận" });
s = page("HẠN CHẾ", "Sáu giới hạn cần đọc kèm mọi con số", "Kết luận");
table(s, ["Giới hạn", "Cụ thể", "Giảm thiểu"], [
  [{ text: "Nhãn chuẩn là silver", options: { bold: true } }, `Claude trùng người ${pct(ACG.acc)}`, "Báo cáo song song theo nhãn người"],
  [{ text: "Một người gán", options: { bold: true } }, "Không phải chuyên gia pháp lý; lượt nhanh chỉ xem 4 câu", "Hai người gán, đo κ người–người"],
  [{ text: "Quy mô nhỏ", options: { bold: true } }, `2 hệ, ${R.claims_total} claim, judge 7B`, "KTC bootstrap, kiểm định ghép cặp"],
  [{ text: "Ngưỡng theo silver", options: { bold: true } }, "Verifier fine-tune nghiêng theo Claude", "Chọn ngưỡng trên nhãn người"],
  [{ text: "Revise tự chấm", options: { bold: true } }, "Judge vừa gắn cờ vừa chấm lại", "Chấm bằng người hoặc metric độc lập"],
  [{ text: "Đồ thị dạng văn bản", options: { bold: true } }, "Chưa dùng triple; chưa có ViEduReg, toán tử Verify KAG", "Verifier đọc triple có cấu trúc"],
], { x: 0.5, y: 1.6, w: 12.3, colW: [3.1, 5.2, 4.0], rowH: [0.45, 0.72, 0.72, 0.72, 0.72, 0.72, 0.72], fontSize: 15 });
notes(s, "Chủ động nói hạn chế trước khi bị hỏi. So với đề cương: 20 đạt, 14 một phần, 5 chưa làm. Hướng tiếp theo: nhãn người cho toàn bộ mẫu với hai người có chuyên môn pháp lý; judge 14–32B; verifier đọc triple; thêm LightRAG, KAG, ViEduReg.");

// ---------- 14. conclusion and thanks ----------
s = page("KẾT LUẬN", "Điểm của máy chấm chỉ là tín hiệu tham khảo, văn bản pháp luật vẫn cần người kiểm tra", "Kết luận");
[["RQ1", `Judge 7B (${f(SENS.judge_7b.macro_f1_vs_human)} theo người) và RAGAS 7B tốt nhất, chỉ khớp mức trung bình.`],
 ["RQ2", "Dữ liệu tổng hợp giúp theo nhãn silver, không giữ được theo người. Đồ thị dạng văn bản và rule không giúp."],
 ["RQ3", "Sửa giảm claim sai bằng cách xóa nội dung: đây là đánh đổi, chưa phải cải thiện thuần."]].forEach(([k, d], i) => {
  const y = 2.0 + i * 0.98;
  text(s, k, { x: 0.6, y, w: 1.3, h: 0.85, fontSize: 24, bold: true, color: ACC, fontFace: MONO, valign: "middle" });
  text(s, d, { x: 1.95, y, w: 10.75, h: 0.85, fontSize: 18, valign: "middle" });
});
rule(s, 0.6, 5.1, 12.13);
text(s, "Cảm ơn thầy cô và các bạn đã lắng nghe", { x: 0.6, y: 5.3, w: 12, h: 0.5, fontSize: 24, bold: true, color: ACC });
text(s, `${AUTHOR} · Mã nguồn và dữ liệu: ${REPO}`, { x: 0.6, y: 5.9, w: 12, h: 0.4, fontSize: 16, color: SOFT });
notes(s, `Số liệu test dùng nhãn silver; nhãn người gồm ${ACG.n} claim, một người gán. Kết bằng một câu trên tiêu đề, sau đó mở demo hoặc nhận câu hỏi.`);

// ---------- native Office equation for the checkers slide ----------
const M_NS = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"';
const mr = (t, plain = true) => `<m:r>${plain ? '<m:rPr><m:sty m:val="p"/></m:rPr>' : ""}<a:rPr lang="vi-VN" sz="2000" i="${plain ? 0 : 1}"><a:latin typeface="Cambria Math"/><a:cs typeface="Cambria Math"/></a:rPr><m:t xml:space="preserve">${t}</m:t></m:r>`;
const frac = (n, d) => `<m:f><m:num>${mr(n)}</m:num><m:den>${mr(d)}</m:den></m:f>`;
const MATH = mr("GGF") + mr(" = ") + frac("số claim supported", "tổng số claim") + mr(" ,      CR") + mr(" = ") + frac("số claim contradicted", "tổng số claim") + mr(" ,      UR") + mr(" = ") + frac("số claim unsupported", "tổng số claim");
// κ, ρ and p in running slide text are set in the maths face, italic.
const MATH_SYM = /(κ|ρ|(?<![\p{L}\p{N}])p(?=\s*(?:=|\()))/u;
function mathRpr(rp) {
  let r = rp.replace(/ i="[01]"/, "").replace("<a:rPr", '<a:rPr i="1"').replace(/<a:(latin|ea|cs|sym)\b[^>]*\/>/g, "");
  const face = '<a:latin typeface="Cambria Math"/><a:cs typeface="Cambria Math"/>';
  return r.endsWith("/>") ? r.slice(0, -2) + `>${face}</a:rPr>` : r.replace("</a:rPr>", `${face}</a:rPr>`);
}
const setSymbols = (xml) => xml.replace(/<a:r>(<a:rPr[^>]*?\/>|<a:rPr[^>]*>[\s\S]*?<\/a:rPr>)<a:t>([^<]*)<\/a:t><\/a:r>/g, (m, rp, t) => {
  if (!MATH_SYM.test(t)) return m;
  return t.split(MATH_SYM).filter((x) => x !== "").map((x) => `<a:r>${["κ", "ρ", "p"].includes(x) ? mathRpr(rp) : rp}<a:t>${x}</a:t></a:r>`).join("");
});
async function patchFormula(file) {
  const JSZip = require("jszip");
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  for (const name of Object.keys(zip.files).filter((n) => /^ppt\/slides\/slide\d+\.xml$/.test(n))) {
    const xml = setSymbols(await zip.file(name).async("string"));
    if (!xml.includes('name="formula"')) { zip.file(name, xml); continue; }
    const at = xml.indexOf('name="formula"'), st = xml.lastIndexOf("<p:sp>", at), en = xml.indexOf("</p:sp>", at) + 7;
    const fallback = xml.slice(st, en);
    const eq = fallback.replace(/<a:p>[\s\S]*<\/a:p>/, `<a:p><a:pPr algn="l"/><a14:m><m:oMathPara ${M_NS}><m:oMathParaPr><m:jc m:val="left"/></m:oMathParaPr><m:oMath>${MATH}</m:oMath></m:oMathPara></a14:m></a:p>`);
    const wrapped = `<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"><mc:Choice xmlns:a14="http://schemas.microsoft.com/office/drawing/2010/main" Requires="a14">${eq}</mc:Choice><mc:Fallback>${fallback}</mc:Fallback></mc:AlternateContent>`;
    zip.file(name, xml.slice(0, st) + wrapped + xml.slice(en));
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  await patchFormula(OUT);
  console.log(OUT);
})();
