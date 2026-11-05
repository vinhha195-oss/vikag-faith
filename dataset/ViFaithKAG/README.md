# ViFaithKAG (pilot)

Bộ dữ liệu đánh giá tính trung thực mức mệnh đề (claim) cho hỏi đáp RAG/GraphRAG tiếng Việt trên văn bản pháp quy
y tế, xây trong đề tài ViKAG-Faith. Quy mô pilot: 40 câu hỏi ViHERMES (8 câu mỗi mức 1–5 hop) × 2 hệ
(Naive RAG, GraphRAG) = 80 câu trả lời, 284 claim, 187 đoạn bằng chứng.

## Nguồn nhãn (đọc trước khi dùng)

- `silver_label`: do **Claude (Anthropic) gán** cho mọi claim, kèm lý do `silver_note`. Đây **không phải nhãn người**.
- `human_label`: có ở **165 claim** hợp lệ (thêm 4 claim tách hỏng cũng có nhãn nhưng không tính) của các lượt kiểm định mù do 1 người gán, không thấy nhãn Claude, không biết hệ
  (`human_pass`: `C` = 60 claim phân tầng, xem toàn đoạn văn; `G`, `H`, `I`, `J` = mỗi lượt 30 claim ngẫu nhiên, xem câu trích, một số bị bỏ qua).
  Gộp các lượt, Claude trùng với người 65%, Cohen's κ = 0,29: Claude khắt khe hơn người.
- `malformed = true`: claim bị tách hỏng, đã loại khỏi mọi phép đo.

## Tệp

| Tệp | Nội dung |
|---|---|
| `claims.jsonl` | Một dòng mỗi claim: nhãn silver/người, nhãn LLM-judge Qwen2.5-7B/3B, xác suất NLI (`zs_*` zero-shot, `ft_*` fine-tune, `nosynth_*` fine-tune chỉ ViNLI; `v1` đoạn văn, `v2` + thông tin graph), điểm SelfCheckGPT |
| `answers.jsonl` | Câu hỏi, đáp án ViHERMES, câu trả lời của hệ, id đoạn truy xuất / bằng chứng, điểm RAGAS, các vòng verify-then-revise |
| `passages.jsonl` | Đoạn bằng chứng (văn bản ViHERMES) kèm thông tin lấy từ graph |
| `thresholds.json` | Ngưỡng entail/contra của từng biến thể NLI, chọn trên tập dev theo nhãn silver |

`split`: 20% câu hỏi là `dev` (chọn ngưỡng), còn lại là `test`. Nhãn: `supported`, `contradicted`, `unsupported`.

## Giấy phép và ghi nguồn

- Câu hỏi, đáp án, đoạn văn bản và graph lấy từ **ViHERMES** (Nguyen và cs., ACIIDS 2026; github.com/ura-hcmut/ViHERMES),
  giấy phép **MIT**. Bản quyền của phần đó thuộc các tác giả ViHERMES; văn bản quy phạm pháp luật gốc thuộc phạm vi công cộng.
- Câu trả lời do Qwen2.5-3B-Instruct sinh; nhãn silver do Claude gán; các điểm tự động do Qwen2.5 và mDeBERTa-v3-base-xnli tính.
- Phần do đề tài tạo ra (claim, nhãn, điểm) phát hành theo MIT, giữ nguyên thông báo bản quyền của ViHERMES.

Chi tiết phương pháp và kết quả: `nop_bai/ViKAG-Faith_BaiBao.docx`.
