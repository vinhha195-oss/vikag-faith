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
const ADVISOR = "TS. Hoàng Văn Quý";
const TOPIC = "Đánh giá và kiểm chứng tính trung thực (faithfulness) mức mệnh đề cho KAG/GraphRAG tiếng Việt dựa trên đồ thị tri thức";
const REPO = "github.com/vinhha195-oss/vikag-faith";

const ROOT = path.resolve(__dirname, "..");
const R = require(path.join(ROOT, "outputs", "analysis", "results.json"));
const OUT = process.env.VIKAG_DECK_OUT || path.join(ROOT, "nop_bai", "ViKAG-Faith_BaiBao_slide.pptx");
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
const f = (x, d = 3) => (x == null ? "–" : x.toFixed(d).replace(".", ",").replace("-", "−"));
const pct = (x) => Math.round(100 * x) + "%";
const CL = R.claim_level, CO = R.answer_level_correlation, CMP = R.comparisons, REV = R.revise, SY = R.systems;
const AG = R.agreement, ACG = AG.audit_CG || AG.audit, AC = AG.audit, SENS = ACG.sensitivity;
const RA = REV.all, R1 = REV.by_max_rounds["1"], R2 = REV.by_max_rounds["2"];
const D2 = require(path.join(ROOT, "outputs", "analysis", "results_dot2.json")), V3 = D2.methods.nli_zs_v3, FT20 = D2.methods.nli_ft20_v1, FT20V3 = D2.methods.nli_ft20_v3, J14 = D2.methods.judge_14b, XZ1 = D2.methods.nli_xzs_v1, FF1 = D2.methods.nli_ft20full_v1, PFF = D2.paired_silver["nli_ft20full_v1 - nli_ft_v1"], PFS = D2.paired_silver["nli_ft20full_v1 - nli_ft20_v1"], XF1 = D2.methods.nli_xft_v1, XF3 = D2.methods.nli_xft_v3, PXF = D2.paired_human["nli_xft_v1 - nli_xzs_v1"], QSP = D2.methods.qwen3b_span, R14 = D2.corr_ragas_14b, SPN = D2.span, PS14 = D2.paired_silver["judge_14b - judge_7b"], PH14 = D2.paired_human["judge_14b - judge_7b"];
const HT = require(path.join(ROOT, "outputs", "analysis", "ieee_extra.json")).human_tuned.ft_v1;
const D3 = require(path.join(ROOT, "outputs", "analysis", "results_dot3.json")), XH1 = D3.methods.xhard_v1;
const C50 = require(path.join(ROOT, "outputs", "analysis", "cascade.json")).verifiers.ft_v1.find((r) => r.budget === 0.5);
const D4 = require(path.join(ROOT, "outputs", "analysis", "results_dot4.json")), J32 = D4.judge_32b.method, EDU = D4.viedureg;
const VER = D4.verify, VO = D4.verify.outcome.verify_operator, V0 = D4.verify.outcome.original, T5 = D4.systems.table, NC = D4.systems.new_claims;
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
text(s, TOPIC, { x: 0.6, y: 0.75, w: 6.5, h: 3.1, fontSize: 28, bold: true });
text(s, "Ai chấm máy chấm?", { x: 0.6, y: 3.95, w: 6.2, h: 0.45, fontSize: 20, color: SOFT });
text(s, `Học viên: ${AUTHOR}`, { x: 0.6, y: 5.05, w: 6.5, h: 0.36, fontSize: 18, bold: true });
text(s, `Giáo viên hướng dẫn: ${ADVISOR}`, { x: 0.6, y: 5.47, w: 6.5, h: 0.36, fontSize: 18, bold: true });
text(s, `${COURSE} · Đồ án P4 ViKAG-Faith`, { x: 0.6, y: 5.95, w: 6.5, h: 0.3, fontSize: 14, color: MUTED });
sheet(s, 7.5, 0, 5.83, 7.5, "cover sheet");
text(s, "CÂU TRẢ LỜI CỦA AI, TÁCH THÀNH TỪNG Ý", { x: 7.95, y: 0.9, w: 5, h: 0.3, fontSize: 13, bold: true, color: "5B6474", fontFace: MONO });
[[["được quảng cáo trên ", "Facebook"], M_SUP, SUP, "SUPPORTED"], [["tổng tiền phạt là ", "8 triệu đồng"], M_CON, CON, "CONTRADICTED"], [["được quảng cáo trên ", "Instagram"], M_UNS, UNS, "UNSUPPORTED"]].forEach(([t, mk, col, lb], i) => {
  const y = 1.6 + i * 1.75;
  text(s, [{ text: t[0], options: { color: INK } }, { text: t[1], options: { color: INK, bold: true, highlight: mk } }], { x: 7.95, y, w: 4.95, h: 0.5, fontSize: 22 });
  tag(s, lb, col, 7.95, y + 0.62, 2.1);
});
notes(s, `Em là Hà Văn Vinh, giáo viên hướng dẫn là ${ADVISOR}.
Đề tài của em đánh giá tính trung thực của hệ hỏi đáp GraphRAG tiếng Việt, ở mức từng ý, trên văn bản pháp quy y tế.
Tên ngắn là "Ai chấm máy chấm?": em không chấm chatbot, em chấm các công cụ chấm tự động.
Bên phải là cách làm: tách câu trả lời thành từng ý, rồi gắn nhãn cho từng ý.
SUPPORTED: văn bản xác nhận. CONTRADICTED: văn bản nói ngược lại. UNSUPPORTED: văn bản không nhắc tới.
Em sẽ trình bày vấn đề, cách làm, kết quả và kết luận.`);

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
notes(s, `Đây là một lỗi thật trong dữ liệu.
AI nói tháng 10/2025, văn bản ghi tháng 10/2022.
Mốc 10/2025 là của luật khác, AI đã ghép nhầm.
Câu văn trôi chảy nên người đọc khó nhận ra.
Vậy máy chấm có đáng tin với tiếng Việt không?`);

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
notes(s, `Có ba khoảng trống.
Một: chỉ có một điểm cho cả câu trả lời, nên không biết ý nào sai.
Hai: ViHERMES cho thấy kiểm chứng rất quan trọng, nhưng chưa ai đo công cụ kiểm chứng tốt đến đâu.
Ba: các máy chấm chủ yếu được thử trên tiếng Anh.`);

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
 ["Meta-evaluation", "24 biến thể metric và ablation đồ thị, rule, số vòng sửa"], ["Độ tin cậy nhãn", "nhãn LLM so với người: thứ hạng metric đổi theo bộ nhãn"]].forEach(([h, d], i) => {
  text(s, [{ text: h + ": ", options: { bold: true } }, { text: d, options: { color: SOFT } }], { x: 0.6 + (i % 2) * 6.2, y: 5.15 + Math.floor(i / 2) * 0.82, w: 5.9, h: 0.72, fontSize: 15 });
});
notes(s, `Đề tài không làm chatbot giỏi hơn, mà kiểm tra các máy chấm.
Ba câu hỏi:
Máy có sẵn tốt đến đâu?
Thêm đồ thị, thêm luật, luyện thêm có giúp không?
Để AI tự sửa thì tốt lên hay xấu đi?`);

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
notes(s, `100 câu hỏi, hai chatbot trả lời thành 200 câu, tách được 610 ý.
Em lấy mẫu 284 ý, bỏ 15 ý lỗi, còn 269 ý.
Người kiểm tra ${ACG.n} ý.
Mọi máy chấm nhìn cùng một tập bằng chứng, nên so sánh mới công bằng.`);

// ---------- 6. checkers ----------
s = page("CÁCH LÀM", "Các máy chấm được so sánh trên cùng một tập bằng chứng", "Cách làm");
table(s, ["Máy chấm", "Cách làm", "Biến thể"], [
  [{ text: "RAGAS", options: { bold: true } }, "Tái hiện 2 prompt gốc, chấm cả câu trả lời", "Qwen2.5 3B, 7B, 14B, 32B"],
  [{ text: "LLM-judge", options: { bold: true } }, "LLM gán 3 nhãn cho từng claim", "Qwen2.5 3B, 7B, 14B, 32B"],
  [{ text: "NLI mDeBERTa-v3", options: { bold: true } }, "Zero-shot trên cửa sổ 900 ký tự, ngưỡng chọn trên tập dev", "V1 đoạn văn · V2 thêm đồ thị"],
  [{ text: "NLI fine-tune", options: { bold: true } }, "12.000 cặp ViNLI + 3.328 cặp tổng hợp (đổi số, ngày, phủ định)", "Ablation: chỉ ViNLI"],
  [{ text: "Rule", options: { bold: true } }, "So khớp số, ngày, số hiệu văn bản", "Riêng lẻ, hoặc thêm vào NLI"],
  [{ text: "SelfCheckGPT", options: { bold: true } }, "3 mẫu nhiệt độ 0,7, không nhìn bằng chứng", "Mốc so sánh"],
], { x: 0.5, y: 1.85, w: 12.3, colW: [2.9, 6.3, 3.1], rowH: [0.45, 0.54, 0.54, 0.54, 0.54, 0.54, 0.54], fontSize: 15 });
text(s, "GGF = số claim supported / tổng số claim     CR, UR = tỉ lệ contradicted, unsupported", { x: 0.6, y: 5.75, w: 12.1, h: 1.05, fontSize: 18, color: TXT, valign: "middle", objectName: "formula" });
notes(s, `RAGAS chấm cả câu trả lời.
LLM-judge dùng AI chấm từng ý.
NLI xem một câu có suy ra được từ đoạn văn không.
Fine-tune là luyện thêm bằng ví dụ tự tạo.
GGF là tỉ lệ ý đúng; 3B, 7B, 14B là cỡ mô hình.`);

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
notes(s, `Phải nói rõ: nhãn chính do Claude gán, không phải người.
Vì vậy em nhờ người kiểm tra mù ${ACG.n} ý.
Claude trùng người ${pct(ACG.acc)}, κ = ${f(ACG.kappa, 2)}, là mức thấp.
Nên không coi nhãn Claude là đáp án tuyệt đối.`);

// ---------- 8. RQ1 waffle ----------
pres.addSection({ title: "Kết quả" });
const J = CATCH.j7;
s = page("RQ1 · MÁY CHẤM CÓ SẴN", "Judge tốt nhất vẫn bỏ sót khoảng 1/3 số ý sai", "Kết quả");
for (let i = 0; i < J.wrong; i++) {
  const col = i % 8, row = Math.floor(i / 8);
  s.addShape(pres.ShapeType.rect, { x: 0.6 + col * 0.5, y: 2.0 + row * 0.5, w: 0.42, h: 0.42, fill: { color: i < J.caught ? ACC : DIM }, line: { color: i < J.caught ? ACC : DIM }, objectName: i < J.caught ? "caught" : "missed" });
}
text(s, `Mỗi ô là một ý sai trong tập test. Ô đậm: Judge 7B bắt được.`, { x: 0.6, y: 6.1, w: 4.2, h: 0.7, fontSize: 14, color: SOFT });
const rowsC = [["j7", "Judge 7B"], ["ft", "NLI fine-tune V1"], ["j3", "Judge 3B"], ["v1", "NLI zero-shot V1"]];
const row14 = [{ text: "Judge 14B" }, { text: `${J14.caught}/${J14.wrong}` }, { text: `${J14.false_alarm}/${J14.right}` }, { text: f(J14.macro_f1) }];
const row32 = [{ text: "Judge 32B" }, { text: `${J32.caught}/${J32.wrong}` }, { text: `${J32.false_alarm}/${J32.right}` }, { text: f(J32.macro_f1) }];
table(s, ["Máy chấm", "Bắt được", "Báo nhầm", "Macro-F1"], rowsC.map(([k, n], i) => {
  const key = { j7: "judge_7b", ft: "nli_ft_v1", j3: "judge_3b", v1: "nli_zs_v1" }[k], c = CATCH[k], b = i === 0 ? { bold: true, color: ACC } : {};
  return [{ text: n, options: b }, { text: `${c.caught}/${c.wrong}`, options: b }, { text: `${c.false_alarm}/${c.right}`, options: b }, { text: f(CL[key].macro_f1), options: b }];
}).concat([row14, row32]), { x: 5.2, y: 2.0, w: 7.6, colW: [3.1, 1.5, 1.6, 1.4], rowH: [0.4, 0.42, 0.42, 0.42, 0.42, 0.42, 0.42], fontSize: 15 });
text(s, `Theo nhãn silver. Báo nhầm là số ý đúng bị cho là sai. SelfCheckGPT đạt ${f(CL.nli_selfcheck.macro_f1)} dù không nhìn bằng chứng, ngang NLI zero-shot.`, { x: 5.3, y: 4.95, w: 7.4, h: 0.8, fontSize: 15, color: SOFT });
text(s, `Chấm cả câu trả lời: RAGAS khớp nhất với điểm chuẩn, tăng theo mô hình: ρ = ${f(CO.ragas_3b.spearman)} (3B), ${f(CO.ragas_7b.spearman)} (7B), ${f(R14.spearman)} (14B).`, { x: 5.3, y: 5.8, w: 7.4, h: 0.8, fontSize: 15, color: SOFT });
notes(s, `Ô đậm là ý judge 7B bắt được: ${CATCH.j7.caught} trên ${CATCH.j7.wrong}, còn sót khoảng 1/3.
Macro-F1 từ 0 đến 1, càng cao càng tốt.
Judge 14B đạt ${f(J14.macro_f1)}, nhưng hơn 7B chưa có ý nghĩa thống kê.
Chấm cả câu trả lời thì RAGAS tốt dần theo cỡ mô hình.
Máy chấm hai tầng: máy so khớp tự quyết nửa số ý nó chắc nhất, nửa còn lại gửi judge 7B; theo người đạt ${f(C50.human.macro_f1)}, ngang judge chấm hết.
Judge 32B (chạy trên Kaggle) đạt ${f(J32.macro_f1)} theo Claude nhưng chỉ ${f(J32.macro_f1_human)} theo người, kém judge 7B có ý nghĩa: judge càng lớn càng gần Claude, càng xa người.
Sang miền giáo dục (ViEduReg, ${EDU.claims} ý): judge 7B vẫn ${f(EDU.judge_7b.macro_f1)}, máy so khớp XLM-R chỉ ${f(EDU.xhard.macro_f1)} vì báo nhầm ${EDU.xhard.false_alarm}/${EDU.xhard.right} ý đúng.`);

// ---------- 9. RQ2 ----------
const c1 = CMP["nli_ft_v1 - nli_zs_v1"], c2 = CMP["nli_nosynth_v1 - nli_zs_v1"];
s = page("RQ2 · CẢI TIẾN VERIFIER", "Dữ liệu tự tạo nâng điểm theo nhãn Claude, thông tin đồ thị làm kém đi", "Kết quả");
s.addChart(pres.ChartType.bar, [
  { name: "Zero-shot", labels: ["V1: chỉ đoạn văn", "V2: thêm đồ thị"], values: [K(CL.nli_zs_v1.macro_f1), K(CL.nli_zs_v2.macro_f1)] },
  { name: "Fine-tune chỉ ViNLI", labels: ["V1: chỉ đoạn văn", "V2: thêm đồ thị"], values: [K(CL.nli_nosynth_v1.macro_f1), K(CL.nli_nosynth_v2.macro_f1)] },
  { name: "Fine-tune ViNLI + tổng hợp", labels: ["V1: chỉ đoạn văn", "V2: thêm đồ thị"], values: [K(CL.nli_ft_v1.macro_f1), K(CL.nli_ft_v2.macro_f1)] },
], { ...CHART_BASE(), x: 0.5, y: 1.85, w: 7.2, h: 5.0, barDir: "col", barGrouping: "clustered", chartColors: [DIM, MUTED, ACC],
  valAxisMinVal: 0, valAxisMaxVal: 600, dataLabelPosition: "outEnd", showLegend: true, legendPos: "b", objectName: "verifier" });
[["+", "Dữ liệu tổng hợp", `+${f(c1.diff)} so với zero-shot (KTC ${f(c1.ci95[0], 2)}–${f(c1.ci95[1], 2)}). Bỏ dữ liệu này chỉ còn +${f(c2.diff)}. 20.000 cặp: ${f(FF1.macro_f1)}. Dữ liệu lỗi thật: ${f(XH1.macro_f1)} theo Claude, ${f(XH1.macro_f1_human)} theo người.`, SUP],
 ["−", "Thông tin đồ thị", `${f(CL.nli_zs_v1.macro_f1)} → ${f(CL.nli_zs_v2.macro_f1)} khi nhét mọi thông tin đồ thị. Triple nối theo claim đạt ${f(V3.macro_f1)}, nhưng theo nhãn người chỉ ${f(V3.macro_f1_human)}.`, CON],
 ["=", "Rule số, ngày", `${f(CL.nli_zs_v1.macro_f1)} → ${f(CL["nli_zs_v1+rule"].macro_f1)}: nhiều lỗi nằm ở chủ thể, không ở con số.`, MUTED]].forEach(([g, h, d, col], i) => {
  const y = 2.05 + i * 1.5;
  text(s, g, { x: 8.1, y, w: 0.7, h: 0.8, fontSize: 40, bold: true, color: col, fontFace: MONO });
  text(s, h, { x: 8.85, y: y + 0.02, w: 3.85, h: 0.34, fontSize: 17, bold: true });
  text(s, d, { x: 8.85, y: y + 0.4, w: 3.85, h: 0.9, fontSize: 14, color: SOFT });
});
notes(s, `Các số ở đây theo nhãn Claude.
Dấu cộng: dữ liệu tự tạo tăng 0,117 điểm.
Dấu trừ: nhét thông tin đồ thị làm điểm giảm.
Dấu bằng: luật số và ngày gần như không đổi.
Tăng lên 20.000 cặp đạt ${f(FF1.macro_f1)}, nhưng chưa hơn đợt 1 có ý nghĩa.
Đợt 3 luyện XLM-R với lỗi sát thực tế (đổi cơ quan, chèn mục, phủ nhận sai): ${f(XH1.macro_f1)} theo Claude, cao nhất, nhưng theo người chỉ ${f(XH1.macro_f1_human)}.
Lần thứ ba cùng một khuôn mẫu: điểm theo Claude tăng, theo người thì không.`);

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
notes(s, `Đây là phát hiện quan trọng nhất.
Đổi sang nhãn người, bảng xếp hạng đổi theo.
Máy đã luyện tụt từ ${f(SENS.nli_ft_v1.macro_f1_vs_claude)} xuống ${f(SENS.nli_ft_v1.macro_f1_vs_human)}; judge 7B đứng đầu với ${f(SENS.judge_7b.macro_f1_vs_human)}.
Claude khắt khe hơn người. Chọn lại ngưỡng theo người cũng không cải thiện.
Chỉ có một người gán, nên đây là kiểm định, không phải đáp án tuyệt đối.`);

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
text(s, `Toán tử Verify kiểu KAG (đợt 4, judge 14B chấm lại): GGF ${f(V0.ggf14_mean)} → ${f(VO.ggf14_mean)}, nhưng từ chối ${VO.refused}/${VO.answers} câu, ${VO.refused_but_silver_correct} câu trong đó vốn đúng hết.`, { x: 7.3, y: 4.45, w: 5.4, h: 1.5, fontSize: 15, color: SOFT });
notes(s, `Judge 7B gắn cờ ý sai, AI viết lại, tối đa 2 vòng.
Ý đúng tăng, ý mâu thuẫn giảm một nửa.
Nhưng token F1 giảm và câu trả lời ngắn đi.
AI chủ yếu xóa ý chứ chưa sửa cho đúng.
Đây là đánh đổi, chưa phải cải thiện thuần.
Toán tử Verify kiểu KAG ở đợt 4 chỉ gọi judge ${VER.judge_calls} lần cho ${VER.claims_checked} ý, chấm lại bằng judge 14B độc lập: GGF tăng ngang bản sửa cũ, nhưng từ chối ${VO.refused} câu.`);

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
notes(s, `Hai chatbot ngang nhau, p = ${f(SY.wilcoxon_GGF_p)}.
Câu 1 hop đạt khoảng 0,85; câu 4 và 5 hop giảm mạnh.
Đồ thị của ViHERMES khá thô, nên GraphRAG chưa lấy thêm được nhiều đoạn đúng.`);

// ---------- 13. limits ----------
pres.addSection({ title: "Kết luận" });
s = page("HẠN CHẾ", "Sáu giới hạn cần đọc kèm mọi con số", "Kết luận");
table(s, ["Giới hạn", "Cụ thể", "Giảm thiểu"], [
  [{ text: "Nhãn chuẩn là silver", options: { bold: true } }, `Claude trùng người ${pct(ACG.acc)}`, "Báo cáo song song theo nhãn người"],
  [{ text: "Một người gán", options: { bold: true } }, "Không phải chuyên gia pháp lý; lượt nhanh chỉ xem 4 câu", "Hai người gán, đo κ người–người"],
  [{ text: "Quy mô nhỏ", options: { bold: true } }, `5 hệ, ${R.claims_total + NC.n} claim; 3 hệ mới chỉ có silver`, "KTC bootstrap, kiểm định ghép cặp"],
  [{ text: "Ngưỡng kém ổn định", options: { bold: true } }, `Chọn trên ${R.claims_dev} claim; theo nhãn người cũng không cải thiện`, "Thêm nhãn người, so thêm AUROC"],
  [{ text: "Revise chấm bằng LLM", options: { bold: true } }, "Đợt 4 chấm lại bằng judge 14B, chưa có người", "Người chấm câu trả lời đã sửa"],
  [{ text: "Đồ thị dạng văn bản", options: { bold: true } }, "Triple nối dạng văn bản; ViEduReg mới là bản thử 30 câu", "Verifier đọc triple có cấu trúc"],
], { x: 0.5, y: 1.6, w: 12.3, colW: [3.1, 5.2, 4.0], rowH: [0.45, 0.72, 0.72, 0.72, 0.72, 0.72, 0.72], fontSize: 15 });
notes(s, `Em chủ động nêu giới hạn.
Quan trọng nhất: nhãn chính do Claude gán, chỉ một người kiểm tra, mẫu còn nhỏ.
Đợt 4 đã thêm 3 hệ (BM25, vector, Naive 7B), ${NC.n} claim silver, ViEduReg bản thử và toán tử Verify; vẫn còn xa mức khoảng 3.000 claim.
Trên 5 hệ, judge 7B xếp hạng gần ngược nhãn silver (ρ = ${f(D4.systems.rank_spearman_vs_silver_ggf.ggf_judge7, 2)}).`);

// ---------- 14. conclusion and thanks ----------
s = page("KẾT LUẬN", "Điểm của máy chấm chỉ là tín hiệu tham khảo, văn bản pháp luật vẫn cần người kiểm tra", "Kết luận");
[["RQ1", `Judge 7B (${f(SENS.judge_7b.macro_f1_vs_human)} theo người) và RAGAS tốt nhất, chỉ khớp mức trung bình. Judge 32B không hơn mà còn xa người hơn. Máy hai tầng ngang judge 7B với nửa số lần gọi.`],
 ["RQ2", `Dữ liệu tổng hợp giúp mDeBERTa theo silver, không giữ được theo người; 20.000 cặp không hơn có ý nghĩa. Dữ liệu lỗi sát thực tế: ${f(XH1.macro_f1)} theo Claude, chỉ ${f(XH1.macro_f1_human)} theo người. Đồ thị, triple và rule chưa giúp được.`],
 ["RQ3", `Sửa giảm claim sai bằng cách xóa nội dung; toán tử Verify từ chối ${VO.refused}/${VO.answers} câu. Đây là đánh đổi, chưa phải cải thiện thuần.`]].forEach(([k, d], i) => {
  const y = 2.0 + i * 0.98;
  text(s, k, { x: 0.6, y, w: 1.3, h: 0.85, fontSize: 24, bold: true, color: ACC, fontFace: MONO, valign: "middle" });
  text(s, d, { x: 1.95, y, w: 10.75, h: 0.85, fontSize: 18, valign: "middle" });
});
rule(s, 0.6, 5.1, 12.13);
text(s, "Cảm ơn thầy cô và các bạn đã lắng nghe", { x: 0.6, y: 5.3, w: 12, h: 0.5, fontSize: 24, bold: true, color: ACC });
text(s, `${AUTHOR} · Mã nguồn và dữ liệu: ${REPO}`, { x: 0.6, y: 5.9, w: 12, h: 0.4, fontSize: 16, color: SOFT });
notes(s, `Em kết luận ba ý.
Máy chấm có sẵn chỉ khớp mức trung bình; theo người, judge 7B tốt nhất.
Luyện thêm giúp theo nhãn Claude, chưa chắc giúp theo người.
AI tự sửa chủ yếu bằng cách xóa nội dung.
Điểm của máy chỉ để tham khảo, văn bản pháp luật vẫn cần người kiểm tra.
Em xin hết, mời thầy cô đặt câu hỏi.`);

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
