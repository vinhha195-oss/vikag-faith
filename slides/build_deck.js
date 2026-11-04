// Build slides/ViKAG-Faith_slides.pptx from outputs/analysis/results.json (same numbers as the report).
//   cd slides && NODE_PATH=node_modules node build_deck.js
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.APPLY_THEME);

const ROOT = path.resolve(__dirname, "..");
const R = require(path.join(ROOT, "outputs", "analysis", "results.json"));
const OUT = path.join(__dirname, "ViKAG-Faith_slides.pptx");

const THEME = {
  name: "ViKAG Faith", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2631", lt1: "FFFFFF", dk2: "0B3C49", lt2: "EEF4F4",
    accent1: "0E5E6F", accent2: "C8553D", accent3: "D9A21B", accent4: "2E7D5B",
    accent5: "6B7A8F", accent6: "9CC9C9", hlink: "0E5E6F", folHlink: "6B7A8F",
  },
};
const HEX = THEME.colors;
const SUP = HEX.accent4, CON = HEX.accent2, UNS = HEX.accent3, TEAL = HEX.accent1, SLATE = HEX.accent5, PALE = HEX.accent6;
const MUTED = "5B6670", GRID = "E3E7EA";

// Vietnamese number format: comma as decimal separator. Chart values are scaled (K: x1000, P: x100) and drawn
// with a literal comma in the number format, because PowerPoint would otherwise print the viewer's locale (0.476).
const K = (v) => Math.round(v * 1000), P = (v) => Math.round(v * 100);
const f = (x, d = 3) => (x == null ? "–" : x.toFixed(d).replace(".", ","));
const CL = R.claim_level, CO = R.answer_level_correlation, AUD = R.agreement.audit_CG || R.agreement.audit, REV = R.revise;

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "ViKAG-Faith";
const C = pres.SchemeColor;

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.35, w: 8.8, h: 1.3, fontSize: 44, bold: true,
        color: C.background1, valign: "bottom", align: "left", fontFace: "+mj-lt" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 2.8, w: 8.8, h: 1.6, fontSize: 18,
        color: C.background1, valign: "top", align: "left" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CLOSING_DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.4, w: 8.8, h: 0.8, fontSize: 36, bold: true,
        color: C.background1, valign: "middle", align: "left", fontFace: "+mj-lt" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 1.4, w: 8.8, h: 3.6, fontSize: 17,
        color: C.background1, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  margin: [0.5, 0.5, 0.5, 0.5],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.28, w: 9.0, h: 0.75, fontSize: 28, bold: true,
        color: C.text2, valign: "middle", align: "left", fontFace: "+mj-lt" }, text: "" } },
    { text: { text: "ViKAG-Faith · pilot ViHERMES", options: { x: 0.5, y: 5.2, w: 5, h: 0.3, fontSize: 10, color: MUTED } } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: MUTED, align: "right" },
});

// ---------- helpers ----------
const text = (slide, t, o) => slide.addText(t, { isTextBox: true, margin: 0, fontSize: 15, color: C.text1, valign: "top", ...o });

function badge(slide, x, y, label, fill, size = 0.5) { // the deck's motif: a filled circle with a short label
  slide.addShape(pres.ShapeType.ellipse, { x, y, w: size, h: size, fill: { color: fill }, line: { color: fill }, objectName: "badge " + label });
  text(slide, label, { x, y, w: size, h: size, fontSize: size > 0.45 ? 16 : 12, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
}

function card(slide, x, y, w, h, fill = HEX.lt2) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: fill } });
}

function stat(slide, x, y, w, value, label, color = TEAL) {
  text(slide, value, { x, y, w, h: 0.7, fontSize: 34, bold: true, color, fontFace: "+mj-lt" });
  text(slide, label, { x, y: y + 0.72, w, h: 0.5, fontSize: 13, color: MUTED });
}

const CHART_BASE = () => ({
  catAxisLabelColor: "3A4550", valAxisLabelColor: MUTED, catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  valGridLine: { style: "none" }, catGridLine: { style: "none" }, valAxisHidden: true,
  showValue: true, dataLabelFormatCode: "0\\,000", dataLabelFontSize: 10, dataLabelColor: "3A4550",
  legendFontFace: "+mn-lt", legendFontSize: 11, legendColor: "3A4550",
});

function notes(slide, t) { slide.addNotes(t); }

// ---------- 1. title ----------
pres.addSection({ title: "Mở đầu" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Mở đầu" });
s.addText("ViKAG-Faith", { placeholder: "title" });
s.addText([
  { text: "Đánh giá tính trung thực mức mệnh đề cho hỏi đáp GraphRAG tiếng Việt", options: { breakLine: true } },
  { text: "Pilot trên ViHERMES (văn bản pháp quy y tế) · 10/2026", options: { fontSize: 14, color: PALE } },
], { placeholder: "body" });
notes(s, "Đề tài là bản pilot của Project 4 (ViKAG-Faith): đo xem các metric faithfulness tự động có đáng tin trên tiếng Việt hay không, ở mức từng mệnh đề của câu trả lời.");

// ---------- 2. problem ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Mở đầu" });
s.addText("Một con số sai là đủ gây hậu quả", { placeholder: "title" });
text(s, [
  { text: "Hệ GraphRAG/KAG tiếng Việt hiện được chấm bằng F1 hoặc một điểm LLM-judge cho cả câu trả lời.", options: { breakLine: true, paraSpaceAfter: 10 } },
  { text: "Không điểm nào cho biết mệnh đề nào bịa thêm hay mâu thuẫn với bằng chứng.", options: { breakLine: true, paraSpaceAfter: 10 } },
  { text: "Đề tài tách câu trả lời thành claim và chấm từng claim: supported, contradicted, unsupported.", options: { bold: true } },
], { x: 0.5, y: 1.3, w: 4.2, h: 3.4, fontSize: 16 });
card(s, 5.1, 1.3, 4.4, 3.5);
text(s, "Ví dụ từ dữ liệu", { x: 5.35, y: 1.45, w: 4, h: 0.3, fontSize: 12, bold: true, color: MUTED });
text(s, "Claim", { x: 5.35, y: 1.85, w: 4, h: 0.3, fontSize: 12, color: MUTED });
text(s, "“Luật sửa đổi Luật Dược trình Quốc hội tháng 10/2025”", { x: 5.35, y: 2.12, w: 3.95, h: 0.7, fontSize: 15, bold: true });
text(s, "Bằng chứng", { x: 5.35, y: 2.9, w: 4, h: 0.3, fontSize: 12, color: MUTED });
text(s, "Tờ trình ghi “trình Quốc hội vào tháng 10 năm 2022”; mốc 10/2025 là của Luật An toàn thực phẩm.", { x: 5.35, y: 3.17, w: 3.95, h: 0.8, fontSize: 14 });
s.addShape(pres.ShapeType.roundRect, { x: 5.35, y: 4.1, w: 1.6, h: 0.42, rectRadius: 0.2, fill: { color: CON }, line: { color: CON } });
text(s, "contradicted", { x: 5.35, y: 4.1, w: 1.6, h: 0.42, fontSize: 13, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
notes(s, "Với văn bản pháp quy, chỉ một ngày hiệu lực hay một con số sai cũng làm câu trả lời nguy hiểm. Điểm F1 hay một điểm judge chung không chỉ ra lỗi nằm ở đâu.");

// ---------- 3. research questions ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Mở đầu" });
s.addText("Ba câu hỏi nghiên cứu", { placeholder: "title" });
const rqs = [
  ["RQ1", "Metric có sẵn khớp với nhãn chuẩn đến đâu?", "RAGAS, LLM-judge, SelfCheckGPT, NLI zero-shot trên tiếng Việt"],
  ["RQ2", "Graph, rule và fine-tune có giúp verifier?", "Bằng chứng graph (V2) so với chỉ đoạn văn (V1); rule số/ngày; fine-tune với dữ liệu tổng hợp"],
  ["RQ3", "Kiểm chứng rồi sửa có đáng không?", "Judge gắn cờ claim sai, bộ sinh viết lại; claim sai giảm bao nhiêu, F1 mất bao nhiêu"],
];
rqs.forEach(([k, q, d], i) => {
  const x = 0.5 + i * 3.1;
  card(s, x, 1.35, 2.85, 3.4);
  badge(s, x + 0.25, 1.6, k, TEAL, 0.75);
  text(s, q, { x: x + 0.25, y: 2.55, w: 2.4, h: 0.95, fontSize: 16, bold: true, color: C.text2 });
  text(s, d, { x: x + 0.25, y: 3.5, w: 2.4, h: 1.1, fontSize: 13, color: "3A4550" });
});
notes(s, "Ba câu hỏi bám đúng đề cương Project 4. Ngoài ra đề tài so sánh Naive RAG với GraphRAG theo số hop.");

// ---------- 4. pipeline ----------
pres.addSection({ title: "Phương pháp" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Phương pháp" });
s.addText("Pipeline đánh giá", { placeholder: "title" });
const steps = [
  ["1", "Trả lời", "2 hệ × 100 câu ViHERMES, Qwen2.5-3B"],
  ["2", "Tách claim", "Mỗi claim một vị từ, tự hiểu được"],
  ["3", "Bằng chứng", "Đoạn truy xuất ∪ đoạn vàng + graph"],
  ["4", "Gán nhãn", "supported / contradicted / unsupported"],
  ["5", "Metric", "GGF, CR, UR; so metric với nhãn"],
];
steps.forEach(([n, h, d], i) => {
  const x = 0.5 + i * 1.83;
  badge(s, x + 0.55, 1.35, n, TEAL, 0.55);
  if (i < steps.length - 1) s.addShape(pres.ShapeType.line, { x: x + 1.2, y: 1.625, w: 1.1, h: 0, line: { color: PALE, width: 2, endArrowType: "triangle" } });
  text(s, h, { x, y: 2.05, w: 1.65, h: 0.4, fontSize: 15, bold: true, color: C.text2, align: "center" });
  text(s, d, { x, y: 2.45, w: 1.65, h: 0.85, fontSize: 12, color: "3A4550", align: "center" });
});
card(s, 0.5, 3.5, 4.35, 1.4);
card(s, 5.15, 3.5, 4.35, 1.4);
text(s, "Naive RAG", { x: 0.75, y: 3.62, w: 4, h: 0.35, fontSize: 15, bold: true, color: C.text2 });
text(s, "BM25 + bge-m3, 8 đoạn tốt nhất, ngân sách 6.000 ký tự", { x: 0.75, y: 4.0, w: 3.9, h: 0.8, fontSize: 13 });
text(s, "GraphRAG", { x: 5.4, y: 3.62, w: 4, h: 0.35, fontSize: 15, bold: true, color: C.text2 });
text(s, "4 đoạn hạt giống, lan truyền trên graph pháp lý ViHERMES (sửa đổi, thay thế, dẫn chiếu)", { x: 5.4, y: 4.0, w: 3.9, h: 0.8, fontSize: 13 });
notes(s, "Hai hệ dùng chung corpus, bộ truy xuất, ngân sách ngữ cảnh và bộ sinh, nên khác biệt chỉ đến từ cách lấy ngữ cảnh. Mọi metric và người gán nhãn dùng cùng một tập bằng chứng.");

// ---------- 5. data and labels ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Phương pháp" });
s.addText("Dữ liệu và nguồn nhãn", { placeholder: "title" });
const gd = R.gold_distribution;
stat(s, 0.5, 1.3, 2.1, "100", "câu hỏi (20/hop)");
stat(s, 2.7, 1.3, 2.1, "80", "câu trả lời gán nhãn");
stat(s, 4.9, 1.3, 2.1, String(R.claims_total), `claim (${R.claims_bad} claim lỗi)`);
stat(s, 7.1, 1.3, 2.4, String(AUD.n), "claim người kiểm tra mù", CON);
s.addChart(pres.ChartType.bar, [
  { name: "supported", labels: ["Nhãn"], values: [gd.supported] },
  { name: "contradicted", labels: ["Nhãn"], values: [gd.contradicted] },
  { name: "unsupported", labels: ["Nhãn"], values: [gd.unsupported] },
], { ...CHART_BASE(), x: 0.4, y: 2.75, w: 4.6, h: 1.4, barDir: "bar", barGrouping: "stacked", chartColors: [SUP, CON, UNS],
  dataLabelFormatCode: "0", dataLabelPosition: "ctr", dataLabelColor: "FFFFFF", catAxisHidden: true, valAxisHidden: true,
  valGridLine: { style: "none" }, showLegend: true, legendPos: "b", objectName: "label distribution" });
card(s, 5.3, 2.8, 4.2, 2.1);
text(s, [
  { text: "Nhãn chính: silver do Claude gán", options: { bold: true, breakLine: true, paraSpaceAfter: 6 } },
  { text: `Kiểm định mù ${AUD.n} claim do người gán (3 lượt): trùng ${Math.round(AUD.acc * 100)}%, κ = ${f(AUD.kappa, 2)}.`, options: { breakLine: true, paraSpaceAfter: 6 } },
  { text: "Lượt duyệt có gợi ý (284 claim, 0 thay đổi, ~10 phút) bị loại.", options: {} },
], { x: 5.55, y: 2.98, w: 3.8, h: 1.8, fontSize: 14 });
notes(s, "Điểm cần nói rõ khi bảo vệ: mọi phép đo dùng nhãn silver của Claude. Độ tin cậy được đo bằng một mẫu kiểm định mù 60 claim, người gán không thấy gợi ý và không biết hệ.");

// ---------- 6. RQ1 claim level ----------
pres.addSection({ title: "Kết quả" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Kết quả" });
s.addText("RQ1: judge 7B tốt nhất ở mức claim", { placeholder: "title" });
const rq1 = [["majority_supported", "Luôn đoán supported"], ["nli_zs_v2", "NLI zero-shot V2"], ["nli_zs_v1", "NLI zero-shot V1"],
  ["nli_selfcheck", "SelfCheckGPT-NLI"], ["judge_3b", "LLM-judge 3B"], ["judge_7b", "LLM-judge 7B"]];
s.addChart(pres.ChartType.bar, [{ name: "Macro-F1", labels: rq1.map((x) => x[1]), values: rq1.map((x) => K(CL[x[0]].macro_f1)) }],
  { ...CHART_BASE(), x: 0.4, y: 1.15, w: 5.6, h: 3.9, barDir: "bar", chartColors: [SLATE, PALE, PALE, SLATE, TEAL, TEAL],
    valAxisMinVal: 0, valAxisMaxVal: 600, dataLabelPosition: "outEnd", showLegend: false,
    showTitle: true, title: "Macro-F1 mức claim (tập test, nhãn silver)", titleFontSize: 12, titleColor: MUTED, titleFontFace: "+mn-lt",
    objectName: "rq1 claim-level macro-F1" });
card(s, 6.3, 1.25, 3.2, 3.7);
text(s, [
  { text: f(CL.judge_7b.macro_f1), options: { fontSize: 34, bold: true, color: TEAL, fontFace: "+mj-lt", breakLine: true } },
  { text: "macro-F1 của judge 7B", options: { fontSize: 13, color: MUTED, breakLine: true, paraSpaceAfter: 12 } },
  { text: "7B tốt hơn 3B.", options: { breakLine: true, paraSpaceAfter: 6 } },
  { text: `SelfCheckGPT (${f(CL.nli_selfcheck.macro_f1)}) không nhìn bằng chứng, chỉ ngang NLI zero-shot.`, options: { breakLine: true, paraSpaceAfter: 6 } },
  { text: "F1 của nhãn contradicted và unsupported đều dưới 0,45.", options: {} },
], { x: 6.55, y: 1.45, w: 2.75, h: 3.4, fontSize: 14 });
notes(s, `Trên ${R.claims_test} claim test. Khoảng tin cậy 95% của judge 7B là ${f(CL.judge_7b.ci95[0], 2)}–${f(CL.judge_7b.ci95[1], 2)}. Verifier fine-tune nằm ở RQ2.`);

// ---------- 7. RQ1 answer level ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Kết quả" });
s.addText("RQ1: RAGAS 7B tốt nhất ở mức câu trả lời", { placeholder: "title" });
const rq1b = [["nli_zs_v1", "NLI zero-shot V1"], ["nli_zs_v2", "NLI zero-shot V2"], ["ragas_3b", "RAGAS 3B"],
  ["nli_selfcheck", "SelfCheckGPT-NLI"], ["judge_3b", "LLM-judge 3B"], ["judge_7b", "LLM-judge 7B"], ["ragas_7b", "RAGAS 7B"]];
s.addChart(pres.ChartType.bar, [{ name: "Spearman", labels: rq1b.map((x) => x[1]), values: rq1b.map((x) => K(CO[x[0]].spearman)) }],
  { ...CHART_BASE(), x: 0.4, y: 1.15, w: 5.6, h: 3.9, barDir: "bar", chartColors: [PALE, PALE, SLATE, SLATE, TEAL, TEAL, TEAL],
    valAxisMinVal: 0, valAxisMaxVal: 600, dataLabelPosition: "outEnd", showLegend: false,
    showTitle: true, title: "Spearman ρ với GGF chuẩn (63 câu trả lời test)", titleFontSize: 12, titleColor: MUTED, titleFontFace: "+mn-lt",
    objectName: "rq1 answer-level spearman" });
card(s, 6.3, 1.25, 3.2, 3.7);
text(s, [
  { text: "ρ = " + f(CO.ragas_7b.spearman), options: { fontSize: 34, bold: true, color: TEAL, fontFace: "+mj-lt", breakLine: true } },
  { text: "RAGAS faithfulness với Qwen2.5-7B", options: { fontSize: 13, color: MUTED, breakLine: true, paraSpaceAfter: 12 } },
  { text: `RAGAS 3B chỉ đạt ${f(CO.ragas_3b.spearman)}: kích thước judge quan trọng.`, options: { breakLine: true, paraSpaceAfter: 6 } },
  { text: "NLI zero-shot gần như không tương quan.", options: {} },
], { x: 6.55, y: 1.45, w: 2.75, h: 3.4, fontSize: 14 });
notes(s, "Tương quan ở mức trung bình, đúng giả thuyết của đề cương: RAGAS với LLM mở tương quan mức trung bình trên tiếng Việt.");

// ---------- 8. RQ2 ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Kết quả" });
s.addText("RQ2: dữ liệu tổng hợp giúp, graph thì không", { placeholder: "title" });
s.addChart(pres.ChartType.bar, [
  { name: "Zero-shot", labels: ["V1: chỉ đoạn văn", "V2: + thông tin graph"], values: [K(CL.nli_zs_v1.macro_f1), K(CL.nli_zs_v2.macro_f1)] },
  { name: "Fine-tune chỉ ViNLI", labels: ["V1: chỉ đoạn văn", "V2: + thông tin graph"], values: [K(CL.nli_nosynth_v1.macro_f1), K(CL.nli_nosynth_v2.macro_f1)] },
  { name: "Fine-tune ViNLI + tổng hợp", labels: ["V1: chỉ đoạn văn", "V2: + thông tin graph"], values: [K(CL.nli_ft_v1.macro_f1), K(CL.nli_ft_v2.macro_f1)] },
], { ...CHART_BASE(), x: 0.4, y: 1.15, w: 5.6, h: 3.9, barDir: "col", barGrouping: "clustered", chartColors: [PALE, SLATE, TEAL],
  valAxisMinVal: 0, valAxisMaxVal: 600, dataLabelPosition: "outEnd", showLegend: true, legendPos: "b",
  showTitle: true, title: "Macro-F1 của verifier mDeBERTa (tập test, nhãn silver)", titleFontSize: 12, titleColor: MUTED, titleFontFace: "+mn-lt",
  objectName: "rq2 verifier variants" });
const c1 = R.comparisons["nli_ft_v1 - nli_zs_v1"], c2 = R.comparisons["nli_nosynth_v1 - nli_zs_v1"];
card(s, 6.3, 1.25, 3.2, 3.7);
text(s, [
  { text: "+" + f(c1.diff), options: { fontSize: 34, bold: true, color: TEAL, fontFace: "+mj-lt", breakLine: true } },
  { text: `fine-tune so với zero-shot (KTC ${f(c1.ci95[0], 2)}–${f(c1.ci95[1], 2)})`, options: { fontSize: 13, color: MUTED, breakLine: true, paraSpaceAfter: 12 } },
  { text: `Bỏ dữ liệu tổng hợp: +${f(c2.diff)}, không cải thiện.`, options: { breakLine: true, paraSpaceAfter: 6 } },
  { text: "Thêm graph (V2) làm giảm kết quả; rule số/ngày gần như không đổi.", options: {} },
], { x: 6.55, y: 1.45, w: 2.75, h: 3.4, fontSize: 14 });
notes(s, "Cặp tổng hợp được tạo từ corpus (đổi số/ngày, phủ định, câu khác cùng văn bản), chỉ từ các đoạn không thuộc mẫu đánh giá. Lưu ý: các lần fine-tune đầu bị loss NaN do checkpoint fp16; kết quả ở đây là sau khi sửa, huấn luyện bằng float32.");

// ---------- 9. blind audit ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Kết quả" });
s.addText("Kiểm định mù: nhãn người đổi thứ hạng", { placeholder: "title" });
const au = [["judge_3b", "Judge 3B"], ["nli_ft_v1", "Fine-tune V1"], ["nli_zs_v1", "Zero-shot V1"], ["judge_7b", "Judge 7B"]];
s.addChart(pres.ChartType.bar, [
  { name: "Theo nhãn Claude", labels: au.map((x) => x[1]), values: au.map((x) => K(AUD.sensitivity[x[0]].macro_f1_vs_claude)) },
  { name: "Theo nhãn người", labels: au.map((x) => x[1]), values: au.map((x) => K(AUD.sensitivity[x[0]].macro_f1_vs_human)) },
], { ...CHART_BASE(), x: 0.4, y: 1.15, w: 5.6, h: 3.9, barDir: "bar", barGrouping: "clustered", chartColors: [PALE, CON],
  valAxisMinVal: 0, valAxisMaxVal: 700, dataLabelPosition: "outEnd", showLegend: true, legendPos: "b",
  showTitle: true, title: `Macro-F1 trên ${AUD.n} claim kiểm định mù`, titleFontSize: 12, titleColor: MUTED, titleFontFace: "+mn-lt",
  objectName: "audit human vs claude" });
card(s, 6.3, 1.25, 3.2, 3.7);
text(s, [
  { text: "κ = " + f(AUD.kappa, 2), options: { fontSize: 34, bold: true, color: CON, fontFace: "+mj-lt", breakLine: true } },
  { text: `Claude–người, trùng ${Math.round(AUD.acc * 100)}%; Claude khắt khe hơn`, options: { fontSize: 13, color: MUTED, breakLine: true, paraSpaceAfter: 12 } },
  { text: "Fine-tune V1 đứng đầu theo nhãn Claude nhưng tụt dưới judge 7B theo nhãn người.", options: { breakLine: true, paraSpaceAfter: 6 } },
  { text: `Tương quan thứ hạng metric chỉ ρ = ${f(AUD.rank_spearman, 2)}.`, options: {} },
], { x: 6.55, y: 1.45, w: 2.75, h: 3.4, fontSize: 14 });
notes(s, "Ngưỡng của verifier được chọn theo nhãn Claude, nên mô hình fine-tune có thể đã học cả cách gán nhãn khắt khe của Claude. 60 claim đủ để cảnh báo nhưng chưa đủ để xếp hạng lại chắc chắn.");

// ---------- 10. RQ3 ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Kết quả" });
s.addText("RQ3: sửa xong trung thực hơn vì ngắn hơn", { placeholder: "title" });
const A = REV.all, B1 = REV.by_max_rounds["1"];
const pairs = [["GGF", A.GGF_before, A.GGF_after, TEAL], ["Tỉ lệ contradicted", A.CR_before, A.CR_after, CON],
  ["Token F1", A.answer_f1_before, A.answer_f1_after, SLATE], ["Claim mỗi câu", A.claims_before, A.claims_after, SLATE]];
pairs.forEach(([lab, b, a, col], i) => {
  const x = 0.5 + i * 2.3;
  card(s, x, 1.25, 2.1, 1.55);
  text(s, lab, { x: x + 0.2, y: 1.38, w: 1.8, h: 0.3, fontSize: 13, color: MUTED });
  const d = lab === "Claim mỗi câu" ? 2 : 3;  // big value = after revising, small line = before
  text(s, f(a, d), { x: x + 0.2, y: 1.68, w: 1.8, h: 0.6, fontSize: 28, bold: true, color: col, fontFace: "+mj-lt" });
  text(s, "từ " + f(b, d), { x: x + 0.2, y: 2.3, w: 1.8, h: 0.3, fontSize: 13, color: MUTED });
});
text(s, `${A.revised}/${A.answers} câu được sửa · p (GGF) = ${f(A.wilcoxon_GGF_p)} · p (F1) = ${f(A.wilcoxon_F1_p)} · ${A.abstained_after} câu chuyển thành “không tìm thấy thông tin”`,
  { x: 0.5, y: 2.92, w: 9, h: 0.3, fontSize: 12, color: MUTED });
const hdr = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: TEAL } } });
s.addTable([
  [hdr("Số vòng sửa tối đa"), hdr("GGF"), hdr("Contradicted"), hdr("Token F1"), hdr("Token recall"), hdr("EM")],
  ["0 (không sửa)", f(A.GGF_before), f(A.CR_before), f(A.answer_f1_before), f(A.answer_recall_before), f(A.answer_em_before)],
  ["1 vòng", f(B1.GGF_after), f(B1.CR_after), f(B1.answer_f1_after), f(B1.answer_recall_after), f(B1.answer_em_after)],
  ["2 vòng", f(A.GGF_after), f(A.CR_after), f(A.answer_f1_after), f(A.answer_recall_after), f(A.answer_em_after)],
], { x: 0.5, y: 3.35, w: 9, colW: [2.4, 1.32, 1.32, 1.32, 1.32, 1.32], fontSize: 13, fontFace: "+mn-lt", color: "1B2631",
  border: { type: "solid", pt: 0.5, color: "D5DBDF" }, rowH: 0.36, align: "center", objectName: "revise rounds" });
notes(s, "GGF trước và sau đều do chính judge 7B chấm, nên mức tăng là giới hạn trên. Vòng 1 cho phần lớn mức tăng; vòng 2 không có ý nghĩa thống kê. EM bằng 0 vì đáp án ViHERMES dài khoảng 115 từ; token recall cho thấy mức mất nội dung.");

// ---------- 11. systems by hop ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Kết quả" });
s.addText("Hai hệ ngang nhau; câu 4–5 hop khó hơn rõ", { placeholder: "title" });
const hops = ["1", "2", "3", "4", "5"];
s.addChart(pres.ChartType.line, [
  { name: "Naive RAG", labels: hops.map((h) => h + " hop"), values: hops.map((h) => P(R.systems.by_hop.naive[h].GGF)) },
  { name: "GraphRAG", labels: hops.map((h) => h + " hop"), values: hops.map((h) => P(R.systems.by_hop.graph[h].GGF)) },
], { ...CHART_BASE(), x: 0.4, y: 1.15, w: 5.6, h: 3.9, chartColors: [SLATE, TEAL], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 7,
  valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 20, showValue: false, valAxisHidden: false,
  valAxisLabelFormatCode: "0\\,00", valGridLine: { color: GRID, size: 0.5 }, showLegend: true, legendPos: "b",
  showTitle: true, title: "GGF trung bình theo số hop (8 câu mỗi mức)", titleFontSize: 12, titleColor: MUTED, titleFontFace: "+mn-lt",
  objectName: "ggf by hop" });
card(s, 6.3, 1.25, 3.2, 3.7);
text(s, [
  { text: `${f(R.systems.naive.GGF, 2)} vs ${f(R.systems.graph.GGF, 2)}`, options: { fontSize: 30, bold: true, color: TEAL, fontFace: "+mj-lt", breakLine: true } },
  { text: `GGF Naive RAG vs GraphRAG, Wilcoxon p = ${f(R.systems.wilcoxon_GGF_p, 2)}`, options: { fontSize: 13, color: MUTED, breakLine: true, paraSpaceAfter: 12 } },
  { text: "Graph phát hành của ViHERMES khá thô nên lan truyền thêm được ít đoạn vàng.", options: { breakLine: true, paraSpaceAfter: 6 } },
  { text: "Độ trung thực giảm còn khoảng 0,4–0,5 ở câu 4–5 hop.", options: {} },
], { x: 6.55, y: 1.45, w: 2.75, h: 3.4, fontSize: 14 });
notes(s, `Token F1 so với đáp án: Naive ${f(R.qa.naive.answer_f1)}, GraphRAG ${f(R.qa.graph.answer_f1)}. Recall đoạn vàng gần như bằng nhau (khoảng 47%).`);

// ---------- 12. error analysis ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Kết quả" });
s.addText("Lỗi thường gặp", { placeholder: "title" });
const errs = [
  ["!", CON, "Sai mốc thời gian", "Ghép mốc 10/2025 của luật khác vào Luật Dược"],
  ["?", UNS, "Gán sai chủ thể", "Nhiệm vụ của Văn phòng Bộ gán cho Viện Chiến lược và Chính sách y tế"],
  ["Σ", CON, "Sai phép tổng hợp", "“Tổng mức phạt 8 triệu” trong khi một phòng khám đã bị phạt 30 triệu"],
  ["∅", SLATE, "Từ chối sai", "“Không có thông tin” dù bằng chứng ghi rõ hiệu lực 01/01/2026"],
];
errs.forEach(([g, col, h, d], i) => {
  const x = 0.5 + (i % 2) * 4.6, y = 1.3 + Math.floor(i / 2) * 1.85;
  card(s, x, y, 4.4, 1.65);
  badge(s, x + 0.25, y + 0.3, g, col, 0.6);
  text(s, h, { x: x + 1.1, y: y + 0.25, w: 3.1, h: 0.4, fontSize: 16, bold: true, color: C.text2 });
  text(s, d, { x: x + 1.1, y: y + 0.68, w: 3.1, h: 0.85, fontSize: 13, color: "3A4550" });
});
notes(s, `Nhiều lỗi không nằm ở con số mà ở việc gán sai chủ thể, nên rule số/ngày giúp ít. Ngoài ra có ${R.claims_bad} claim bị tách lỗi.`);

// ---------- 13. requirement check ----------
pres.addSection({ title: "Kết luận" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Kết luận" });
s.addText("Đối chiếu với đề cương Project 4", { placeholder: "title" });
stat(s, 0.5, 1.3, 2.0, "20", "hạng mục đạt", SUP);
stat(s, 0.5, 2.45, 2.0, "14", "làm một phần / thu nhỏ", UNS);
stat(s, 0.5, 3.6, 2.0, "5", "chưa làm", CON);
card(s, 2.9, 1.3, 6.6, 3.6);
text(s, [
  { text: "Đã đủ phần lõi", options: { bold: true, color: C.text2, breakLine: true } },
  { text: "Tách claim, verifier fine-tune, rule, GGF/CR/UR, verify-then-revise, baseline RAGAS/judge/SelfCheckGPT/NLI, các ablation, dataset và demo.", options: { breakLine: true, paraSpaceAfter: 10 } },
  { text: "Thu nhỏ theo quy mô pilot", options: { bold: true, color: C.text2, breakLine: true } },
  { text: `2 hệ thay vì 5, 284 claim thay vì ~3.000 (${AUD.n} có nhãn người), 1 người gán, judge 7B thay vì 32B, graph đưa vào dạng văn bản.`, options: { breakLine: true, paraSpaceAfter: 10 } },
  { text: "Chưa làm", options: { bold: true, color: C.text2, breakLine: true } },
  { text: "ViEduReg, verifier Qwen trả span, baseline ViHallu, toán tử Verify trong KAG, chatbot quy chế.", options: {} },
], { x: 3.15, y: 1.45, w: 6.15, h: 3.35, fontSize: 14 });
notes(s, "Bảng đối chiếu đầy đủ 39 hạng mục nằm ở Phụ lục A của báo cáo.");

// ---------- 14. conclusion ----------
s = pres.addSlide({ masterName: "CLOSING_DARK", sectionTitle: "Kết luận" });
s.addText("Kết luận", { placeholder: "title" });
s.addText([
  { text: "RQ1: judge 7B và RAGAS 7B tốt nhất, nhưng chỉ khớp mức trung bình với nhãn chuẩn.", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } },
  { text: "RQ2: dữ liệu tổng hợp trong miền là thay đổi duy nhất có ích; graph dạng văn bản và rule không giúp.", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } },
  { text: "RQ3: sửa giảm claim sai nhưng làm câu trả lời kém đầy đủ: đánh đổi, chưa phải cải thiện thuần.", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } },
  { text: "Tiếp theo: thêm nhãn người (2 người, κ), judge ≥14B, verifier đọc triple, thêm hệ LightRAG/KAG.", options: { bullet: true, color: PALE } },
], { placeholder: "body" });
notes(s, "Demo: https://claude.ai/artifact/WpaWPBgdzeQgxe9jmwVeQ4 (cần chia sẻ trước khi gửi cho người khác). Dữ liệu: dataset/ViFaithKAG. Báo cáo: report/bao_cao_ViKAG-Faith.pdf.");

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log(OUT);
})();
