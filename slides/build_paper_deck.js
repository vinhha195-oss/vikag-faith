// Build slides/ViKAG-Faith_BaiBao_slide.pptx: the paper as a ~21-slide talk in the course template's structure
// (dark title, Tóm tắt with 4 stat cards, Bối cảnh, RQ + đóng góp, related work, architecture, method, data,
// results per RQ, error analysis, 6 limitation cards, conclusion, thank-you). Numbers come from results.json.
//   cd slides && NODE_PATH=node_modules APPLY_THEME=<pptx skill>/scripts/apply_theme.js node build_paper_deck.js
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.APPLY_THEME);

const AUTHOR = "Hà Văn Vinh";   // điền họ tên tác giả
const COURSE = "Xử lý ngôn ngữ tự nhiên nâng cao";     // điền tên môn học
const SHORT_TITLE = "Đánh giá faithfulness mức mệnh đề cho GraphRAG tiếng Việt";

const ROOT = path.resolve(__dirname, "..");
const R = require(path.join(ROOT, "outputs", "analysis", "results.json"));
const FIG1 = path.join(ROOT, "report", "paper_figs", "fig1_architecture.png");
const OUT = path.join(__dirname, "ViKAG-Faith_BaiBao_slide.pptx");

const THEME = {
  name: "ViKAG Faith Paper", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2631", lt1: "FFFFFF", dk2: "0B3C49", lt2: "EEF4F4",
    accent1: "0E5E6F", accent2: "C8553D", accent3: "D9A21B", accent4: "2E7D5B",
    accent5: "6B7A8F", accent6: "9CC9C9", hlink: "0E5E6F", folHlink: "6B7A8F",
  },
};
const HEX = THEME.colors;
const TEAL = HEX.accent1, CON = HEX.accent2, UNS = HEX.accent3, SUP = HEX.accent4, SLATE = HEX.accent5, PALE = HEX.accent6;
const GREEN = "15907A", ORANGE = "E0703A", MUTED = "5B6670", INK = "1B2631", GRID = "E3E7EA";

const K = (v) => Math.round(v * 1000), P = (v) => Math.round(v * 100);
const f = (x, d = 3) => (x == null ? "–" : x.toFixed(d).replace(".", ","));
const pct = (x) => Math.round(100 * x) + "%";
const CL = R.claim_level, CO = R.answer_level_correlation, CMP = R.comparisons, REV = R.revise, SY = R.systems;
const AG = R.agreement, ACG = AG.audit_CG || AG.audit, AC = AG.audit, SENS = ACG.sensitivity;
const RA = REV.all, R1 = REV.by_max_rounds["1"], R2 = REV.by_max_rounds["2"];
const NPASS = 1 + (AG.quick_passes || []).length;

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "ViKAG-Faith";
const C = pres.SchemeColor;

// ---------- layouts ----------
pres.defineSlideMaster({ title: "TITLE_DARK", background: { color: C.text2 }, objects: [] });
pres.defineSlideMaster({ title: "PLAIN", background: { color: C.background1 }, objects: [] });
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.45, y: 0.2, w: 9.1, h: 0.6, fontSize: 26, bold: true,
        color: C.text2, valign: "middle", align: "left", fontFace: "+mj-lt" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.45, y: 0.78, w: 9.1, h: 0.35, fontSize: 12.5, italic: true,
        color: GREEN, valign: "top", align: "left" }, text: "" } },
    { text: { text: `${AUTHOR} · ${SHORT_TITLE}`, options: { x: 0.45, y: 5.28, w: 7, h: 0.22, fontSize: 8, color: MUTED } } },
  ],
  slideNumber: { x: 9.05, y: 5.28, w: 0.5, h: 0.22, fontSize: 8, color: MUTED, align: "right" },
});

// ---------- helpers ----------
const text = (slide, t, o) => slide.addText(t, { isTextBox: true, margin: 0, fontSize: 13, color: INK, valign: "top", ...o });
function card(slide, x, y, w, h, fill = HEX.lt2) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.06, fill: { color: fill }, line: { color: fill } });
}
function badge(slide, x, y, label, fill, size = 0.42, fs = 11) {
  slide.addShape(pres.ShapeType.ellipse, { x, y, w: size, h: size, fill: { color: fill }, line: { color: fill }, objectName: "badge " + label });
  text(slide, label, { x, y, w: size, h: size, fontSize: fs, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
}
function content(title, sub, section) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  s.addText(sub, { placeholder: "body" });
  return s;
}
function statCard(s, x, y, w, h, value, label, color = TEAL, icon = null, iconColor = TEAL) {
  card(s, x, y, w, h);
  text(s, value, { x: x + 0.2, y: y + 0.15, w: w - 0.9, h: 0.6, fontSize: 28, bold: true, color, fontFace: "+mj-lt" });
  if (icon) badge(s, x + w - 0.62, y + 0.17, icon, iconColor, 0.42, 12);
  text(s, label, { x: x + 0.2, y: y + 0.8, w: w - 0.4, h: h - 0.9, fontSize: 10.5, color: "3A4550" });
}
const CHART_BASE = () => ({
  catAxisLabelColor: "3A4550", valAxisLabelColor: MUTED, catAxisLabelFontSize: 9.5, valAxisLabelFontSize: 9,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  valGridLine: { style: "none" }, catGridLine: { style: "none" }, valAxisHidden: true,
  showValue: true, dataLabelFormatCode: "0\\,000", dataLabelFontSize: 9, dataLabelColor: "3A4550",
  legendFontFace: "+mn-lt", legendFontSize: 9.5, legendColor: "3A4550",
  titleFontSize: 10.5, titleColor: MUTED, titleFontFace: "+mn-lt",
});
const notes = (s, t) => s.addNotes(t);

// ---------- 1. title ----------
pres.addSection({ title: "Mở đầu" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Mở đầu" });
text(s, `ĐỒ ÁN P4 · ${COURSE.toUpperCase()}`, { x: 0.6, y: 0.45, w: 8, h: 0.3, fontSize: 10, bold: true, color: ORANGE, charSpacing: 2 });
text(s, "Đánh giá tính trung thực mức mệnh đề cho hệ hỏi đáp GraphRAG tiếng Việt", { x: 0.6, y: 0.95, w: 6.4, h: 1.9, fontSize: 30, bold: true, color: "FFFFFF", fontFace: "+mj-lt" });
text(s, "ViKAG-Faith: Graph-Grounded Claim-Level Faithfulness Evaluation and Verification for Vietnamese Knowledge-Augmented Generation",
  { x: 0.6, y: 3.15, w: 6.2, h: 0.6, fontSize: 11, italic: true, color: "D6E4E7" });
text(s, AUTHOR, { x: 0.6, y: 4.2, w: 6, h: 0.3, fontSize: 14, bold: true, color: "FFFFFF" });
text(s, `Học viên cao học · ${COURSE}`, { x: 0.6, y: 4.5, w: 6, h: 0.3, fontSize: 11, color: "D6E4E7" });
// motif: three claim chips checked against evidence
[["supported", SUP], ["contradicted", CON], ["unsupported", UNS]].forEach(([t, col], i) => {
  s.addShape(pres.ShapeType.roundRect, { x: 7.25, y: 1.45 + i * 0.75, w: 2.15, h: 0.5, rectRadius: 0.25, fill: { color: col }, line: { color: col } });
  text(s, t, { x: 7.25, y: 1.45 + i * 0.75, w: 2.15, h: 0.5, fontSize: 13, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
});
notes(s, "Đề tài thuộc Project 4 (ViKAG-Faith): đo xem các công cụ phát hiện lỗi của AI có đáng tin trên tiếng Việt hay không, ở mức từng mệnh đề của câu trả lời.");

// ---------- 2. summary ----------
s = content("Tóm tắt", "Máy kiểm tra giúp được, nhưng chưa thay được người kiểm tra", "Mở đầu");
statCard(s, 0.45, 1.25, 4.4, 1.75, f(SENS.judge_7b.macro_f1_vs_human), `macro-F1 của LLM-judge 7B theo nhãn người (${ACG.n} claim): metric đáng tin nhất; RAGAS 7B tốt nhất ở mức câu trả lời (ρ = ${f(CO.ragas_7b.spearman)}) (RQ1)`, TEAL, "1");
statCard(s, 5.15, 1.25, 4.4, 1.75, `${f(CL.nli_zs_v1.macro_f1)} → ${f(CL.nli_ft_v1.macro_f1)}`, `fine-tune verifier bằng dữ liệu tổng hợp theo nhãn silver; theo nhãn người chỉ ${f(SENS.nli_ft_v1.macro_f1_vs_human)} so với ${f(SENS.nli_zs_v1.macro_f1_vs_human)} (RQ2)`, ORANGE, "2", ORANGE);
statCard(s, 0.45, 3.2, 4.4, 1.75, `${f(100 * RA.CR_before, 1)}% → ${f(100 * RA.CR_after, 1)}%`, `claim mâu thuẫn sau verify-then-revise; nhưng token F1 giảm ${f(RA.answer_f1_before)} → ${f(RA.answer_f1_after)}: AI xóa ý thay vì sửa (RQ3)`, GREEN, "3", GREEN);
statCard(s, 5.15, 3.2, 4.4, 1.75, `${pct(ACG.acc)} · κ = ${f(ACG.kappa, 2)}`, `mức trùng giữa nhãn Claude (silver) và ${ACG.n} nhãn người qua ${NPASS} lượt gán mù; Claude khắt khe hơn người`, CON, "!", CON);
notes(s, "Bốn con số chính của đề tài. Mọi số liệu theo nhãn silver nên là ước lượng; cột nhãn người là phần kiểm chứng.");

// ---------- 3. context ----------
s = content("Bối cảnh", "Một con số hay một ngày sai là đủ gây hậu quả với văn bản pháp quy", "Mở đầu");
text(s, [
  { text: "GraphRAG/KAG tiếng Việt hiện được chấm bằng F1 hoặc một điểm LLM-judge cho cả câu trả lời.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
  { text: "Không điểm nào chỉ ra mệnh đề nào bịa thêm hay mâu thuẫn với bằng chứng.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
  { text: "ViHERMES (ACIIDS 2026): bỏ module kiểm chứng làm điểm judge giảm 0,7554 → 0,6823.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
  { text: "Các metric faithfulness (RAGAS, LLM-judge, SelfCheckGPT) chủ yếu được kiểm định trên tiếng Anh.", options: { bullet: true } },
], { x: 0.45, y: 1.3, w: 4.4, h: 3.6, fontSize: 13.5 });
card(s, 5.15, 1.3, 4.4, 3.6);
text(s, "Ví dụ từ dữ liệu", { x: 5.4, y: 1.45, w: 4, h: 0.3, fontSize: 11, bold: true, color: MUTED });
text(s, "Claim", { x: 5.4, y: 1.85, w: 4, h: 0.25, fontSize: 10.5, color: MUTED });
text(s, "“Luật sửa đổi Luật Dược trình Quốc hội tháng 10/2025”", { x: 5.4, y: 2.1, w: 3.95, h: 0.65, fontSize: 14, bold: true });
text(s, "Bằng chứng", { x: 5.4, y: 2.85, w: 4, h: 0.25, fontSize: 10.5, color: MUTED });
text(s, "Tờ trình ghi “trình Quốc hội vào tháng 10 năm 2022”; mốc 10/2025 là của Luật An toàn thực phẩm.", { x: 5.4, y: 3.1, w: 3.95, h: 0.8, fontSize: 12.5 });
s.addShape(pres.ShapeType.roundRect, { x: 5.4, y: 4.1, w: 1.6, h: 0.42, rectRadius: 0.2, fill: { color: CON }, line: { color: CON } });
text(s, "contradicted", { x: 5.4, y: 4.1, w: 1.6, h: 0.42, fontSize: 12, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
notes(s, "Vấn đề: điểm tổng không chỉ ra lỗi nằm ở đâu. Đề tài tách câu trả lời thành từng mệnh đề và chấm từng mệnh đề.");

// ---------- 4. RQ + contributions ----------
s = content("Câu hỏi nghiên cứu và đóng góp", "Không xây hệ hỏi đáp mới: đánh giá các công cụ kiểm chứng trên tiếng Việt", "Mở đầu");
text(s, "Câu hỏi nghiên cứu", { x: 0.45, y: 1.25, w: 4.3, h: 0.3, fontSize: 12.5, bold: true, color: C.text2 });
[["RQ1", "Metric có sẵn (RAGAS, LLM-judge, SelfCheckGPT, NLI) khớp với nhãn chuẩn đến đâu?"],
 ["RQ2", "Thông tin đồ thị, rule số/ngày, fine-tune bằng dữ liệu tổng hợp có giúp verifier không?"],
 ["RQ3", "Verify-then-revise giảm claim sai bao nhiêu, có làm giảm chất lượng trả lời không?"]].forEach(([k, q], i) => {
  badge(s, 0.45, 1.68 + i * 0.75, k, GREEN, 0.5, 10);
  text(s, q, { x: 1.1, y: 1.7 + i * 0.75, w: 3.7, h: 0.6, fontSize: 11.5 });
});
card(s, 0.45, 4.05, 4.3, 0.95, C.text2);
text(s, [{ text: "Hướng tiếp cận: ", options: { bold: true } }, { text: "tách câu trả lời thành claim, đối chiếu với tập bằng chứng chung, đo mức khớp của từng metric với nhãn chuẩn (meta-evaluation)." }],
  { x: 0.62, y: 4.15, w: 4.0, h: 0.8, fontSize: 11, color: "FFFFFF", valign: "middle" });
text(s, "Đóng góp", { x: 5.15, y: 1.25, w: 4.3, h: 0.3, fontSize: 12.5, bold: true, color: C.text2 });
[["C1 · Quy trình:", "đánh giá mức claim tái lập được trên ViHERMES (7 bước, Colab T4)"],
 ["C2 · Dữ liệu:", `ViFaithKAG pilot: ${R.claims_total} claim nhãn silver, ${ACG.n} claim nhãn người`],
 ["C3 · Meta-evaluation:", "12 biến thể metric + ablation đồ thị, rule, dữ liệu tổng hợp, số vòng sửa"],
 ["C4 · Độ tin cậy nhãn:", "nhãn LLM so với người: thứ hạng metric đổi khi đổi bộ nhãn"]].forEach(([k, d], i) => {
  card(s, 5.15, 1.62 + i * 0.84, 4.4, 0.72);
  text(s, [{ text: k + " ", options: { bold: true, color: GREEN } }, { text: d }], { x: 5.3, y: 1.7 + i * 0.84, w: 4.1, h: 0.6, fontSize: 11, valign: "middle" });
});

// ---------- 5. related work ----------
s = content("Công trình liên quan", "Các metric hiện có chưa được kiểm định ở mức claim cho tiếng Việt", "Mở đầu");
[["Đo faithfulness của RAG", "RAGAS: tỉ lệ statement suy ra được từ ngữ cảnh. FActScore: chấm từng atomic fact. LLM-as-a-judge.", "Kiểm định chủ yếu trên tiếng Anh."],
 ["Phát hiện hallucination", "SelfCheckGPT (không cần bằng chứng), SemEval SHROOM/Mu-SHROOM, DSC2025 ViHallu.", "ViHallu không gắn với đồ thị hay bằng chứng truy xuất."],
 ["NLI tiếng Việt", "XNLI, ViNLI; mDeBERTa-v3 huấn luyện NLI đa ngôn ngữ làm verifier encoder.", "Chưa có dữ liệu claim–bằng chứng pháp quy."],
 ["Graph RAG và KAG", "GraphRAG, LightRAG, HippoRAG 2, KAG; ViHERMES dựng đồ thị Văn bản–Điều–Khoản.", "Nền dữ liệu và đồ thị mà đề tài dùng lại."]].forEach(([h, d, n], i) => {
  const x = 0.45 + (i % 2) * 4.7, y = 1.25 + Math.floor(i / 2) * 1.55;
  card(s, x, y, 4.4, 1.38);
  badge(s, x + 0.18, y + 0.18, String(i + 1), TEAL, 0.4, 11);
  text(s, h, { x: x + 0.72, y: y + 0.2, w: 3.5, h: 0.35, fontSize: 12.5, bold: true, color: C.text2 });
  text(s, d, { x: x + 0.2, y: y + 0.62, w: 4.0, h: 0.45, fontSize: 10.5 });
  text(s, "→ " + n, { x: x + 0.2, y: y + 1.05, w: 4.0, h: 0.28, fontSize: 10, italic: true, color: ORANGE });
});
card(s, 0.45, 4.43, 9.1, 0.6, C.text2);
text(s, [{ text: "Vị trí của đề tài: ", options: { bold: true } }, { text: "đánh giá các metric kiểm chứng ở mức claim, có so với nhãn người; giữ nguyên dữ liệu và đồ thị ViHERMES, chỉ thêm tầng đánh giá." }],
  { x: 0.62, y: 4.48, w: 8.8, h: 0.5, fontSize: 11, color: "FFFFFF", valign: "middle" });

// ---------- 6. architecture ----------
pres.addSection({ title: "Phương pháp" });
s = content("Kiến trúc hệ thống", "Hai hệ sinh câu trả lời → tách claim → tập bằng chứng chung → metric → so với nhãn chuẩn", "Phương pháp");
s.addImage({ path: FIG1, x: 0.75, y: 1.2, w: 8.5, h: 8.5 * 4.6 / 9.0 * 0.93, objectName: "architecture" });
notes(s, "Hai hệ dùng chung corpus, bộ truy xuất, ngân sách ngữ cảnh và bộ sinh, nên khác biệt chỉ đến từ cách lấy ngữ cảnh. Mọi metric và người gán dùng cùng một tập bằng chứng.");

// ---------- 7. claims and evidence ----------
s = content("Tách claim và tập bằng chứng", "Mọi metric và người gán nhìn cùng một tập bằng chứng", "Phương pháp");
[["Hai hệ hỏi đáp", "Naive RAG (8 đoạn) và GraphRAG (4 hạt giống + lan truyền đồ thị ViHERMES); cùng BM25 + bge-m3, Qwen2.5-3B, 6.000 ký tự."],
 ["Tách claim", "Qwen2.5-3B, prompt tiếng Việt có ví dụ: một vị từ chính, tự hiểu được, giữ nguyên số, ngày, số hiệu."],
 ["Tập bằng chứng", "Đoạn truy xuất ∪ đoạn vàng của ViHERMES, kèm tên văn bản, số hiệu và quan hệ lấy từ đồ thị."],
 ["Ba nhãn", "supported: suy ra được · contradicted: nói ngược lại · unsupported: không đề cập. Claim tách hỏng bị loại."]].forEach(([h, d], i) => {
  const x = 0.45 + (i % 2) * 3.05, y = 1.25 + Math.floor(i / 2) * 1.85;
  card(s, x, y, 2.85, 1.7);
  badge(s, x + 0.18, y + 0.18, String(i + 1), TEAL, 0.38, 10);
  text(s, h, { x: x + 0.66, y: y + 0.2, w: 2.1, h: 0.35, fontSize: 12, bold: true, color: C.text2 });
  text(s, d, { x: x + 0.2, y: y + 0.65, w: 2.5, h: 1.0, fontSize: 10.5 });
});
card(s, 6.6, 1.25, 2.95, 3.6, C.text2);
text(s, "610", { x: 6.85, y: 1.45, w: 2.5, h: 0.65, fontSize: 36, bold: true, color: "FFFFFF", fontFace: "+mj-lt" });
text(s, "claim tách từ 200 câu trả lời (100 câu hỏi × 2 hệ)", { x: 6.85, y: 2.1, w: 2.5, h: 0.6, fontSize: 11, color: "D6E4E7" });
text(s, String(R.claims_total), { x: 6.85, y: 2.95, w: 2.5, h: 0.65, fontSize: 36, bold: true, color: "FFFFFF", fontFace: "+mj-lt" });
text(s, `claim trong mẫu 80 câu trả lời được gán nhãn (${R.claims_bad} claim lỗi bị loại)`, { x: 6.85, y: 3.6, w: 2.5, h: 0.8, fontSize: 11, color: "D6E4E7" });

// ---------- 8. metrics and verifier ----------
s = content("Metric và verifier", "Từ LLM làm giám khảo đến verifier NLI có luyện thêm", "Phương pháp");
card(s, 0.45, 1.2, 9.1, 1.12);
text(s, [
  { text: "GGF = |claim supported| / |claim|          P_sup(c) = max_w P(entail | w, c)", options: { breakLine: true } },
  { text: "P_con(c) = max P(contra | w, c) trên 2 cửa sổ w trùng từ nhiều nhất với claim" },
], { x: 0.65, y: 1.27, w: 8.7, h: 0.62, fontSize: 13, italic: true, fontFace: "Cambria", color: C.text2 });
text(s, "CR, UR: tỉ lệ contradicted, unsupported. Cửa sổ 900 ký tự; ngưỡng (τ_s, τ_c) chọn trên tập dev.",
  { x: 0.65, y: 1.95, w: 8.7, h: 0.3, fontSize: 10.5, color: MUTED });
[["RAGAS & LLM-judge", "RAGAS tái hiện 2 prompt gốc; judge gán 3 nhãn cho từng claim. Qwen2.5-3B và 7B."],
 ["NLI V1 / V2", "mDeBERTa-v3 zero-shot. V1: chỉ đoạn văn; V2: thêm tên văn bản, số hiệu, quan hệ đồ thị."],
 ["Fine-tune", "12.000 cặp ViNLI + 3.328 cặp tổng hợp (đổi số, ngày, phủ định). Ablation: chỉ ViNLI."],
 ["Rule & SelfCheckGPT", "Rule so khớp số/ngày/số hiệu. SelfCheckGPT: 3 mẫu nhiệt độ 0,7, không nhìn bằng chứng."]].forEach(([h, d], i) => {
  const x = 0.45 + i * 2.31;
  card(s, x, 2.55, 2.15, 1.75);
  text(s, h, { x: x + 0.15, y: 2.68, w: 1.85, h: 0.4, fontSize: 12.5, bold: true, color: C.text2 });
  text(s, d, { x: x + 0.15, y: 3.12, w: 1.85, h: 1.1, fontSize: 11 });
});

// ---------- 9. data and labels ----------
s = content("Dữ liệu và nhãn", `Nhãn chính là silver; ${ACG.n} claim được người gán mù qua ${NPASS} lượt`, "Phương pháp");
const gd = R.gold_distribution;
const tH = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: TEAL } } });
s.addTable([
  [tH("Lượt"), tH("Cách chọn · hiển thị"), tH("Claim"), tH("Trùng Claude"), tH("κ")],
  ["C", "phân tầng 30/15/15 · toàn đoạn văn", String(AC.n), pct(AC.acc), f(AC.kappa, 2)],
  [(AG.quick_passes || []).join(", "), "ngẫu nhiên · 4 câu bằng chứng", String(AG.audit_G.n), pct(AG.audit_G.acc), f(AG.audit_G.kappa, 2)],
  [{ text: "Gộp", options: { bold: true } }, "", { text: String(ACG.n), options: { bold: true } }, { text: pct(ACG.acc), options: { bold: true } }, { text: f(ACG.kappa, 2), options: { bold: true } }],
  ["Bị loại", "duyệt có gợi ý; file không tạo qua trang", "–", "–", "–"],
], { x: 0.45, y: 1.3, w: 5.6, colW: [0.8, 2.6, 0.7, 0.9, 0.6], fontSize: 10.5, fontFace: "+mn-lt", color: INK,
  border: { type: "solid", pt: 0.5, color: "D5DBDF" }, rowH: 0.36, objectName: "label passes" });
text(s, "Người gán không thấy nhãn hay lý do của Claude và không biết câu trả lời thuộc hệ nào.", { x: 0.45, y: 3.35, w: 5.6, h: 0.5, fontSize: 10.5, italic: true, color: MUTED });
s.addChart(pres.ChartType.bar, [
  { name: "supported", labels: ["Silver"], values: [gd.supported] },
  { name: "contradicted", labels: ["Silver"], values: [gd.contradicted] },
  { name: "unsupported", labels: ["Silver"], values: [gd.unsupported] },
], { ...CHART_BASE(), x: 0.35, y: 3.85, w: 5.8, h: 1.3, barDir: "bar", barGrouping: "stacked", chartColors: [SUP, CON, UNS],
  dataLabelFormatCode: "0", dataLabelPosition: "ctr", dataLabelColor: "FFFFFF", catAxisHidden: true, showLegend: true, legendPos: "b", objectName: "label distribution" });
[["100", "câu hỏi (20 mỗi mức hop)"], [`${R.claims_dev}/${R.claims_test}`, "claim dev / test"], [String(ACG.n), "claim có nhãn người"]].forEach(([v, l], i) => {
  card(s, 6.35, 1.3 + i * 1.22, 3.2, 1.08);
  text(s, v, { x: 6.55, y: 1.38 + i * 1.22, w: 2.8, h: 0.55, fontSize: 26, bold: true, color: i === 2 ? CON : TEAL, fontFace: "+mj-lt" });
  text(s, l, { x: 6.55, y: 1.92 + i * 1.22, w: 2.8, h: 0.35, fontSize: 10.5, color: "3A4550" });
});

// ---------- 10. setup ----------
s = content("Thiết lập thí nghiệm", "Mọi bước dùng mô hình chạy trên Colab T4; máy cá nhân chỉ phân tích", "Phương pháp");
[["Cấu hình", "Judge 3B/7B · RAGAS 3B/7B · NLI zero-shot V1/V2 · fine-tune V1/V2 · fine-tune chỉ ViNLI · mỗi NLI có/không rule · SelfCheckGPT · rule · luôn đoán supported"],
 ["Metric", "Mức claim: macro-F1 3 nhãn, AUROC phát hiện claim sai. Mức câu trả lời: Spearman/Kendall với GGF chuẩn. Revise: GGF, CR, token F1, EM, token recall"],
 ["Thống kê", "KTC 95% bootstrap 1.000 lần; bootstrap ghép cặp cho hiệu số; Wilcoxon cặp; Cohen's κ"],
 ["Phần cứng", "Google Colab T4 16GB (Ollama Q4_K_M, PyTorch float32). GPU cá nhân 4GB treo máy khi chạy mô hình"]].forEach(([h, d], i) => {
  card(s, 0.45, 1.25 + i * 0.95, 9.1, 0.82);
  text(s, h, { x: 0.65, y: 1.25 + i * 0.95, w: 1.6, h: 0.82, fontSize: 12.5, bold: true, color: C.text2, valign: "middle" });
  text(s, d, { x: 2.3, y: 1.25 + i * 0.95, w: 7.1, h: 0.82, fontSize: 11, valign: "middle" });
});

// ---------- 11. overall results ----------
pres.addSection({ title: "Kết quả" });
s = content("Kết quả tổng hợp", `Macro-F1 trên ${R.claims_test} claim test (nhãn silver) và trên ${ACG.n} claim có nhãn người`, "Kết quả");
const ov = [["majority_supported", "Luôn supported"], ["nli_zs_v2", "NLI ZS V2"], ["nli_selfcheck", "SelfCheckGPT"], ["nli_zs_v1", "NLI ZS V1"],
  ["judge_3b", "Judge 3B"], ["judge_7b", "Judge 7B"], ["nli_ft_v1", "NLI fine-tune V1"]];
s.addChart(pres.ChartType.bar, [
  { name: "Nhãn silver (test)", labels: ov.map((x) => x[1]), values: ov.map((x) => K(CL[x[0]].macro_f1)) },
  { name: "Nhãn người", labels: ov.map((x) => x[1]), values: ov.map((x) => K(SENS[x[0]].macro_f1_vs_human)) },
], { ...CHART_BASE(), x: 0.35, y: 1.2, w: 6.0, h: 3.95, barDir: "bar", barGrouping: "clustered", chartColors: [PALE, CON],
  valAxisMinVal: 0, valAxisMaxVal: 700, dataLabelPosition: "outEnd", showLegend: true, legendPos: "b", objectName: "overall" });
card(s, 6.6, 1.25, 2.95, 3.85);
text(s, [
  { text: "Đọc biểu đồ", options: { bold: true, color: C.text2, breakLine: true, paraSpaceAfter: 6 } },
  { text: "Theo nhãn silver, fine-tune V1 cao nhất.", options: { bullet: true, breakLine: true, paraSpaceAfter: 5 } },
  { text: "Theo nhãn người, judge 7B cao nhất; fine-tune tụt về mức zero-shot.", options: { bullet: true, breakLine: true, paraSpaceAfter: 5 } },
  { text: `F1 cho contradicted/unsupported của mọi metric đều dưới 0,45.`, options: { bullet: true } },
], { x: 6.8, y: 1.4, w: 2.6, h: 3.6, fontSize: 11.5 });

// ---------- 12. RQ1 ----------
s = content("RQ1: các metric có sẵn", "Judge 7B tốt nhất ở mức claim; RAGAS 7B tốt nhất ở mức câu trả lời", "Kết quả");
const rq1b = [["nli_zs_v1", "NLI ZS V1"], ["nli_zs_v2", "NLI ZS V2"], ["ragas_3b", "RAGAS 3B"], ["nli_selfcheck", "SelfCheckGPT"], ["judge_3b", "Judge 3B"], ["judge_7b", "Judge 7B"], ["ragas_7b", "RAGAS 7B"]];
s.addChart(pres.ChartType.bar, [{ name: "Spearman", labels: rq1b.map((x) => x[1]), values: rq1b.map((x) => K(CO[x[0]].spearman)) }],
  { ...CHART_BASE(), x: 0.35, y: 1.2, w: 5.6, h: 3.95, barDir: "bar", chartColors: [PALE, PALE, SLATE, SLATE, TEAL, TEAL, TEAL],
    valAxisMinVal: 0, valAxisMaxVal: 600, dataLabelPosition: "outEnd", showLegend: false, showTitle: true,
    title: "Spearman ρ giữa điểm câu trả lời và GGF chuẩn (63 câu trả lời test)", objectName: "rq1" });
[[f(CL.judge_7b.macro_f1), "macro-F1 judge 7B (silver), AUROC " + f(CL.judge_7b.auroc_not_supported)],
 [f(CO.ragas_7b.spearman), `ρ RAGAS 7B; RAGAS 3B chỉ ${f(CO.ragas_3b.spearman)}: kích thước judge quyết định`],
 [f(CL.nli_selfcheck.macro_f1), "SelfCheckGPT: ngang NLI zero-shot dù không nhìn bằng chứng"]].forEach(([v, l], i) => {
  card(s, 6.2, 1.25 + i * 1.3, 3.35, 1.16);
  text(s, v, { x: 6.4, y: 1.33 + i * 1.3, w: 3, h: 0.5, fontSize: 24, bold: true, color: TEAL, fontFace: "+mj-lt" });
  text(s, l, { x: 6.4, y: 1.85 + i * 1.3, w: 3, h: 0.5, fontSize: 10.5, color: "3A4550" });
});

// ---------- 13. RQ2 ----------
s = content("RQ2: đồ thị, rule và fine-tune", "Dữ liệu tổng hợp giúp theo nhãn silver; thông tin đồ thị làm kém đi", "Kết quả");
s.addChart(pres.ChartType.bar, [
  { name: "Zero-shot", labels: ["V1: chỉ đoạn văn", "V2: + đồ thị"], values: [K(CL.nli_zs_v1.macro_f1), K(CL.nli_zs_v2.macro_f1)] },
  { name: "Fine-tune chỉ ViNLI", labels: ["V1: chỉ đoạn văn", "V2: + đồ thị"], values: [K(CL.nli_nosynth_v1.macro_f1), K(CL.nli_nosynth_v2.macro_f1)] },
  { name: "Fine-tune ViNLI + tổng hợp", labels: ["V1: chỉ đoạn văn", "V2: + đồ thị"], values: [K(CL.nli_ft_v1.macro_f1), K(CL.nli_ft_v2.macro_f1)] },
], { ...CHART_BASE(), x: 0.35, y: 1.2, w: 5.6, h: 3.95, barDir: "col", barGrouping: "clustered", chartColors: [PALE, SLATE, TEAL],
  valAxisMinVal: 0, valAxisMaxVal: 600, dataLabelPosition: "outEnd", showLegend: true, legendPos: "b", showTitle: true,
  title: "Macro-F1 của verifier mDeBERTa (test, nhãn silver)", objectName: "rq2" });
const c1 = CMP["nli_ft_v1 - nli_zs_v1"], c2 = CMP["nli_nosynth_v1 - nli_zs_v1"];
[["+" + f(c1.diff), `fine-tune so với zero-shot (KTC ${f(c1.ci95[0], 2)}–${f(c1.ci95[1], 2)})`, TEAL],
 ["+" + f(c2.diff), "bỏ dữ liệu tổng hợp: không cải thiện", SLATE],
 [`${f(CL.nli_zs_v1.macro_f1)} → ${f(CL.nli_zs_v2.macro_f1)}`, "thêm đồ thị (V2): máy thấy tên văn bản trùng là cho supported", CON]].forEach(([v, l, col], i) => {
  card(s, 6.2, 1.25 + i * 1.3, 3.35, 1.16);
  text(s, v, { x: 6.4, y: 1.33 + i * 1.3, w: 3, h: 0.5, fontSize: 22, bold: true, color: col, fontFace: "+mj-lt" });
  text(s, l, { x: 6.4, y: 1.85 + i * 1.3, w: 3, h: 0.5, fontSize: 10.5, color: "3A4550" });
});
notes(s, "Rule số/ngày gần như không đổi kết quả vì nhiều lỗi nằm ở việc gán sai chủ thể. Lưu ý: các lần fine-tune đầu bị loss NaN do checkpoint fp16; đã sửa và huấn luyện lại bằng float32.");

// ---------- 14. blind audit ----------
s = content("Kiểm định mù: nhãn người đổi thứ hạng", `${ACG.n} claim người gán; ưu thế của fine-tune biến mất`, "Kết quả");
const au = [["judge_3b", "Judge 3B"], ["nli_ft_v1", "Fine-tune V1"], ["nli_zs_v1", "Zero-shot V1"], ["judge_7b", "Judge 7B"]];
s.addChart(pres.ChartType.bar, [
  { name: "Theo nhãn Claude", labels: au.map((x) => x[1]), values: au.map((x) => K(SENS[x[0]].macro_f1_vs_claude)) },
  { name: "Theo nhãn người", labels: au.map((x) => x[1]), values: au.map((x) => K(SENS[x[0]].macro_f1_vs_human)) },
], { ...CHART_BASE(), x: 0.35, y: 1.2, w: 5.6, h: 3.95, barDir: "bar", barGrouping: "clustered", chartColors: [PALE, CON],
  valAxisMinVal: 0, valAxisMaxVal: 700, dataLabelPosition: "outEnd", showLegend: true, legendPos: "b", objectName: "audit" });
const cm = ACG.confusion_claude_rows_human_cols;
card(s, 6.2, 1.25, 3.35, 3.85, C.text2);
text(s, `κ = ${f(ACG.kappa, 2)}`, { x: 6.4, y: 1.4, w: 3, h: 0.6, fontSize: 28, bold: true, color: "FFFFFF", fontFace: "+mj-lt" });
text(s, [
  { text: `Claude trùng người ${pct(ACG.acc)}.`, options: { breakLine: true, paraSpaceAfter: 6 } },
  { text: `Claude gán sai/không căn cứ cho ${cm[1].reduce((a, b) => a + b) + cm[2].reduce((a, b) => a + b)} claim; người gán supported ${cm[1][0] + cm[2][0]} trong số đó.`, options: { breakLine: true, paraSpaceAfter: 6 } },
  { text: `Tương quan thứ hạng metric giữa hai bộ nhãn: ρ = ${f(ACG.rank_spearman, 2)}.`, options: {} },
], { x: 6.4, y: 2.1, w: 3, h: 2.9, fontSize: 11.5, color: "FFFFFF" });

// ---------- 15. RQ3 ----------
s = content("RQ3: verify-then-revise", "Ít claim sai hơn nhưng câu trả lời ngắn và thiếu hơn", "Kết quả");
[["GGF (judge 7B)", RA.GGF_before, RA.GGF_after, TEAL, 3], ["Claim mâu thuẫn", RA.CR_before, RA.CR_after, CON, 3],
 ["Token F1", RA.answer_f1_before, RA.answer_f1_after, SLATE, 3], ["Claim mỗi câu", RA.claims_before, RA.claims_after, SLATE, 2]].forEach(([lab, b, a, col, d], i) => {
  const x = 0.45 + i * 2.31;
  card(s, x, 1.25, 2.15, 1.35);
  text(s, lab, { x: x + 0.18, y: 1.35, w: 1.8, h: 0.3, fontSize: 11, color: MUTED });
  text(s, f(a, d), { x: x + 0.18, y: 1.65, w: 1.8, h: 0.55, fontSize: 26, bold: true, color: col, fontFace: "+mj-lt" });
  text(s, "từ " + f(b, d), { x: x + 0.18, y: 2.2, w: 1.8, h: 0.3, fontSize: 11, color: MUTED });
});
text(s, `${RA.revised}/${RA.answers} câu được sửa · p(GGF) = ${f(RA.wilcoxon_GGF_p)} · p(F1) = ${f(RA.wilcoxon_F1_p)} · ${RA.abstained_after} câu thành “không tìm thấy thông tin”`,
  { x: 0.45, y: 2.72, w: 9.1, h: 0.3, fontSize: 10.5, color: MUTED });
s.addTable([
  [tH("Số vòng sửa tối đa"), tH("GGF"), tH("Mâu thuẫn"), tH("Token F1"), tH("Token recall"), tH("EM")],
  ["0 (không sửa)", f(RA.GGF_before), f(RA.CR_before), f(RA.answer_f1_before), f(RA.answer_recall_before), f(RA.answer_em_before)],
  ["1 vòng", f(R1.GGF_after), f(R1.CR_after), f(R1.answer_f1_after), f(R1.answer_recall_after), f(R1.answer_em_after)],
  ["2 vòng", f(R2.GGF_after), f(R2.CR_after), f(R2.answer_f1_after), f(R2.answer_recall_after), f(R2.answer_em_after)],
], { x: 0.45, y: 3.15, w: 9.1, colW: [2.35, 1.35, 1.35, 1.35, 1.35, 1.35], fontSize: 11, fontFace: "+mn-lt", color: INK,
  border: { type: "solid", pt: 0.5, color: "D5DBDF" }, rowH: 0.36, align: "center", objectName: "rounds" });
text(s, "EM = 0 vì đáp án ViHERMES dài (~115 từ). GGF do chính judge 7B chấm lại nên là giới hạn trên.", { x: 0.45, y: 4.75, w: 9.1, h: 0.3, fontSize: 10, italic: true, color: MUTED });

// ---------- 16. RQ3 example ----------
s = content("RQ3: AI xóa ý thay vì sửa", "Ví dụ thật: câu hỏi 3 hop, Naive RAG, sau 1 vòng sửa", "Kết quả");
card(s, 0.45, 1.25, 9.1, 0.55, C.text2);
text(s, "Câu hỏi: so sánh thời điểm trình Quốc hội Luật sửa đổi Luật Dược, ban hành Nghị định 124/2021 và bệnh viện tự chủ mua sắm thuốc theo Luật 90/2025.",
  { x: 0.6, y: 1.25, w: 8.8, h: 0.55, fontSize: 11, italic: true, color: "FFFFFF", valign: "middle" });
card(s, 0.45, 2.0, 4.45, 2.4);
text(s, [
  { text: "Trước khi sửa", options: { bold: true, color: C.text2, breakLine: true, paraSpaceAfter: 6 } },
  { text: "Dự kiến Luật sửa đổi Luật Dược sẽ được trình Quốc hội vào ", options: {} },
  { text: "tháng 10/2025", options: { bold: true, color: CON } },
  { text: ". Nghị định 124/2021/NĐ-CP … được ban hành vào tháng 12/2021. Thời điểm các bệnh viện tự chủ được tự quyết định mua sắm thuốc … là từ ngày 01/7/2025." },
], { x: 0.65, y: 2.12, w: 4.05, h: 2.2, fontSize: 11.5 });
card(s, 5.1, 2.0, 4.45, 2.4);
text(s, [
  { text: "Sau 1 vòng sửa", options: { bold: true, color: C.text2, breakLine: true, paraSpaceAfter: 6 } },
  { text: "Không tìm thấy thông tin về thời điểm dự kiến trình Quốc hội Luật sửa đổi Luật Dược. Thời điểm ban hành Nghị định 124/2021/NĐ-CP và thời điểm … mua sắm thuốc theo Luật số 90/2025/QH15 " },
  { text: "được nêu rõ trong ngữ cảnh", options: { bold: true, color: ORANGE } },
  { text: "." },
], { x: 5.3, y: 2.12, w: 4.05, h: 2.2, fontSize: 11.5 });
badge(s, 0.45, 4.55, "!", ORANGE, 0.42, 13);
text(s, "Văn bản ghi Luật Dược trình Quốc hội tháng 10/2022. Câu trả lời mới đạt GGF = 1 theo judge nhưng mất cả ba mốc thời gian, kể cả mốc 01/7/2025 đúng.",
  { x: 1.0, y: 4.5, w: 8.5, h: 0.55, fontSize: 11, color: CON, valign: "middle" });

// ---------- 17. systems by hop ----------
s = content("Hai hệ và độ khó theo hop", `GGF ${f(SY.naive.GGF, 2)} và ${f(SY.graph.GGF, 2)} (p = ${f(SY.wilcoxon_GGF_p, 2)}); câu 4–5 hop khó hơn rõ`, "Kết quả");
const hops = ["1", "2", "3", "4", "5"];
s.addChart(pres.ChartType.line, [
  { name: "Naive RAG", labels: hops.map((h) => h + " hop"), values: hops.map((h) => P(SY.by_hop.naive[h].GGF)) },
  { name: "GraphRAG", labels: hops.map((h) => h + " hop"), values: hops.map((h) => P(SY.by_hop.graph[h].GGF)) },
], { ...CHART_BASE(), x: 0.35, y: 1.2, w: 5.6, h: 3.95, chartColors: [SLATE, TEAL], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 7,
  valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 20, showValue: false, valAxisHidden: false, valAxisLabelFormatCode: "0\\,00",
  valGridLine: { color: GRID, size: 0.5 }, showLegend: true, legendPos: "b", showTitle: true, title: "GGF trung bình theo số hop (8 câu mỗi mức)", objectName: "hop" });
[[f(R.qa.naive.answer_f1), `token F1 Naive RAG (GraphRAG ${f(R.qa.graph.answer_f1)})`],
 [`${Math.round(100 * R.qa.naive.gold_passage_recall)}% · ${Math.round(100 * R.qa.graph.gold_passage_recall)}%`, "recall đoạn vàng của hai hệ: đồ thị phát hành khá thô"],
 ["~0,4–0,5", "GGF ở câu 4–5 hop, so với ~0,85 ở câu 1 hop"]].forEach(([v, l], i) => {
  card(s, 6.2, 1.25 + i * 1.3, 3.35, 1.16);
  text(s, v, { x: 6.4, y: 1.33 + i * 1.3, w: 3, h: 0.5, fontSize: 22, bold: true, color: TEAL, fontFace: "+mj-lt" });
  text(s, l, { x: 6.4, y: 1.85 + i * 1.3, w: 3, h: 0.5, fontSize: 10.5, color: "3A4550" });
});

// ---------- 18. errors ----------
s = content("Phân tích lỗi", "Nhiều lỗi nằm ở chủ thể và phép tổng hợp, không chỉ ở con số", "Kết quả");
[["Sai mốc thời gian", "Ghép mốc 10/2025 của luật khác vào Luật Dược (văn bản ghi 10/2022).", CON],
 ["Gán sai chủ thể", "Nhiệm vụ của Văn phòng Bộ gán cho Viện Chiến lược và Chính sách y tế. Rule số/ngày không bắt được.", UNS],
 ["Sai phép tổng hợp", "“Tổng phạt 8 triệu” trong khi một phòng khám đã bị phạt 30 triệu. Cả hai judge bỏ sót; NLI bắt được.", CON],
 ["Bịa thêm danh sách", "Thêm Instagram, TikTok, YouTube; văn bản chỉ ghi facebook, zalo. NLI zero-shot bị lừa.", SLATE]].forEach(([h, d, col], i) => {
  const x = 0.45 + (i % 2) * 4.7, y = 1.25 + Math.floor(i / 2) * 1.9;
  card(s, x, y, 4.4, 1.72);
  badge(s, x + 0.2, y + 0.2, String(i + 1), col, 0.48, 12);
  text(s, h, { x: x + 0.85, y: y + 0.24, w: 3.4, h: 0.4, fontSize: 13, bold: true, color: C.text2 });
  text(s, d, { x: x + 0.85, y: y + 0.7, w: 3.4, h: 0.95, fontSize: 11 });
});

// ---------- 19. limitations ----------
pres.addSection({ title: "Kết luận" });
s = content("Hạn chế và rủi ro", "Mỗi hạn chế kèm hướng giảm thiểu", "Kết luận");
[["Nhãn chuẩn là silver", `Claude trùng người ${pct(ACG.acc)}.`, "báo cáo song song theo nhãn người"],
 ["Một người gán", "Không phải chuyên gia pháp lý; lượt nhanh chỉ xem 4 câu.", "hai người gán, đo κ người–người"],
 ["Quy mô nhỏ", "2 hệ, 284 claim, judge 7B (Colab T4).", "KTC bootstrap, kiểm định ghép cặp"],
 ["Ngưỡng theo silver", "Verifier fine-tune nghiêng theo Claude.", "chọn ngưỡng trên nhãn người"],
 ["Revise tự chấm", "Judge vừa gắn cờ vừa chấm lại.", "chấm bằng người hoặc metric độc lập"],
 ["Đồ thị dạng văn bản", "Chưa dùng triple; chưa có ViEduReg, toán tử Verify KAG.", "verifier đọc triple có cấu trúc"]].forEach(([h, d, m], i) => {
  const x = 0.45 + (i % 3) * 3.07, y = 1.25 + Math.floor(i / 3) * 1.92;
  card(s, x, y, 2.9, 1.78);
  badge(s, x + 0.15, y + 0.15, String(i + 1), ORANGE, 0.38, 10);
  text(s, h, { x: x + 0.62, y: y + 0.16, w: 2.2, h: 0.4, fontSize: 11.5, bold: true, color: C.text2 });
  text(s, [{ text: d, options: { breakLine: true } }, { text: "Giảm thiểu: ", options: { bold: true, color: GREEN } }, { text: m, options: { color: GREEN } }],
    { x: x + 0.18, y: y + 0.65, w: 2.6, h: 1.05, fontSize: 10.5 });
});

// ---------- 20. conclusion ----------
s = content("Kết luận và hướng phát triển", "Công cụ kiểm tra tự động hữu ích nhưng chưa thay được người", "Kết luận");
[["RQ1", `Judge 7B (${f(SENS.judge_7b.macro_f1_vs_human)} theo người) và RAGAS 7B tốt nhất; chỉ khớp mức trung bình.`],
 ["RQ2", "Dữ liệu tổng hợp giúp theo nhãn silver, không giữ được theo người; đồ thị dạng văn bản và rule không giúp."],
 ["RQ3", "Sửa giảm claim sai bằng cách xóa nội dung: đánh đổi, chưa phải cải thiện thuần."]].forEach(([k, d], i) => {
  badge(s, 0.45, 1.3 + i * 1.1, k, GREEN, 0.62, 11);
  text(s, d, { x: 1.25, y: 1.33 + i * 1.1, w: 3.9, h: 0.75, fontSize: 12, valign: "middle" });
});
card(s, 5.4, 1.25, 4.15, 3.3, GREEN);
text(s, [
  { text: "Hướng phát triển", options: { bold: true, breakLine: true, paraSpaceAfter: 6 } },
  { text: "Nhãn người cho toàn bộ mẫu, hai người gán có chuyên môn pháp lý.", options: { bullet: { type: "number" }, breakLine: true, paraSpaceAfter: 4 } },
  { text: "Judge 14–32B; verifier Qwen trả nhãn và span.", options: { bullet: { type: "number" }, breakLine: true, paraSpaceAfter: 4 } },
  { text: "Đưa đồ thị vào verifier dạng triple; thêm LightRAG, KAG, ViEduReg.", options: { bullet: { type: "number" }, breakLine: true, paraSpaceAfter: 4 } },
  { text: "Chấm câu trả lời đã sửa bằng người; bộ sinh lớn hơn cho bước sửa.", options: { bullet: { type: "number" } } },
], { x: 5.6, y: 1.4, w: 3.8, h: 3.05, fontSize: 11.5, color: "FFFFFF" });
text(s, `Số liệu test dùng nhãn silver; nhãn người: ${ACG.n} claim, một người gán.`, { x: 0.45, y: 4.75, w: 9.1, h: 0.3, fontSize: 10, italic: true, color: MUTED });

// ---------- 21. thanks ----------
s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Kết luận" });
text(s, "Cảm ơn thầy cô và các bạn đã lắng nghe", { x: 0.6, y: 1.6, w: 8.8, h: 1.0, fontSize: 32, bold: true, color: "FFFFFF", fontFace: "+mj-lt" });
text(s, AUTHOR, { x: 0.6, y: 3.0, w: 8, h: 0.35, fontSize: 15, bold: true, color: "FFFFFF" });
text(s, "Mã nguồn: vikag-faith (ViHERMES + tầng đánh giá) · Dữ liệu: ViFaithKAG · Demo: trang tương tác ViKAG-Faith", { x: 0.6, y: 3.4, w: 8.8, h: 0.35, fontSize: 11, color: "D6E4E7" });

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log(OUT);
})();
