# ViKAG-Faith (pilot)

Đánh giá tính trung thực (faithfulness) mức claim cho hệ hỏi đáp GraphRAG tiếng Việt trên dữ liệu
[ViHERMES](https://github.com/ura-hcmut/ViHERMES) (văn bản pháp quy y tế).

**Sản phẩm nộp (thư mục [nop_bai/](nop_bai/)):** bài báo Word, slide PowerPoint, slide PDF · số liệu gốc:
[outputs/analysis/results.json](outputs/analysis/results.json) · đề cương:
https://claude.ai/artifact/Ek3Puhkwvimrrbj97ojenf

## Kết quả chính

| Câu hỏi | Kết quả |
|---|---|
| RQ1, mức claim | Trong các metric có sẵn, LLM-judge Qwen2.5-7B tốt nhất: macro-F1 0,476 (silver), 0,528 (nhãn người); SelfCheckGPT 0,409; judge 7B bắt được 41/64 claim sai |
| RQ1, mức câu trả lời | RAGAS faithfulness 7B tương quan cao nhất với GGF chuẩn: Spearman 0,484 |
| RQ2 | Verifier fine-tune (ViNLI + cặp tổng hợp) 0,521 > zero-shot 0,404 (silver, có ý nghĩa); ablation chỉ ViNLI 0,405; nhưng trên mẫu người fine-tune chỉ 0,381 < judge-7B 0,528. Graph trong NLI và rule số/ngày không giúp; triple nối theo claim (V3, zero-shot) đạt 0,423 theo silver, 0,328 theo nhãn người |
| RQ3 | Verify-then-revise: GGF theo judge 7B 0,755 → 0,830 (p = 0,014) nhưng token F1 0,595 → 0,563; câu trả lời chủ yếu ngắn đi. Vòng 1 cho phần lớn mức tăng (GGF 0,801); vòng 2 không có ý nghĩa thống kê (p = 0,312). EM = 0 ở mọi cấu hình (đáp án ViHERMES dài ~115 từ) |
| Hai hệ | Naive RAG và GraphRAG ngang nhau (GGF 0,694 và 0,638, p = 0,191); câu 4–5 hop giảm mạnh |
| Độ tin cậy nhãn | Năm lượt kiểm định mù do người gán (C: 60 claim phân tầng; G–J: 4 × 30 claim ngẫu nhiên, còn 105): gộp 165 claim (58% bộ dữ liệu), Claude trùng người 65%, κ = 0,29, tương quan thứ hạng metric 0,46. Theo nhãn người, judge-7B tốt nhất (0,528); verifier fine-tune (0,381) không hơn zero-shot (0,409) |

**Demo:** `demo/vikag_faith_demo.html`, một file duy nhất, mở bằng trình duyệt, không cần mạng (4 tab: đề tài là gì, 4 ví dụ đã được người kiểm tra, tra cứu 80 câu trả lời, kết quả). Bản đăng: https://claude.ai/artifact/Hav1SviyP3Q9rQcBY8dGHG ·
**Dữ liệu:** `dataset/ViFaithKAG/` (sinh bởi `make_dataset.py`).

Lưu ý: các lần fine-tune trước 28/10/2026 trên Colab bị loss = NaN (checkpoint fp16), nên kết luận cũ "fine-tune không giúp ích" là sai.

## Nguồn nhãn

- Mọi phép đo dùng **nhãn silver do Claude gán** cho 284 claim (`outputs/prelabels.json`).
- Lượt duyệt A (`vifaith_labels_A.json`): 284 nhãn được xác nhận mà không sửa nhãn nào trong khoảng 10 phút, nên **không dùng làm nhãn người**.
- Lượt kiểm định mù C (`vifaith_labels_C.json`): 60 claim, gán từ đầu, không có gợi ý. Dùng để đo độ tin cậy của nhãn silver.
- Lượt kiểm định nhanh G, H, I, J (`vifaith_labels_{G,H,I,J}.json`, trang `src/s6_quick.py G|H|I|J`): mỗi lượt 30 claim ngẫu nhiên không trùng lượt trước, mỗi màn hình một claim với 4 câu bằng chứng; 15 claim bị bỏ qua.
- Lượt D, E, F **không dùng**: file xuất của D không được tạo qua trang gán nhãn, E chỉ chép lại D, F chưa làm.

## Cấu trúc

| Đường dẫn | Nội dung |
|---|---|
| `src/common.py` | Đường dẫn, Ollama helper; mặc định chạy CPU (`VIKAG_CPU=1`) vì GPU máy này làm treo máy |
| `src/s1_answer.py` | 2 hệ (naive / graph) trả lời 100 câu ViHERMES |
| `src/s2_claims.py` | Tách claim |
| `src/s3_pool.py` | Tập bằng chứng (truy xuất ∪ đoạn vàng) + thông tin graph; chọn mẫu 40 câu × 2 hệ |
| `src/s4_judges.py` | RAGAS (tái hiện 2 prompt gốc) và LLM-judge mức claim, Qwen2.5 3B/7B |
| `src/s5_verifier.py` | Dữ liệu tổng hợp + ViNLI, fine-tune và chấm mDeBERTa-v3-base-xnli (V1/V2) |
| `src/rules.py` | Rule kiểm tra số, ngày, số hiệu văn bản |
| `src/s6_annotation.py` | Trang gán nhãn HTML ngoại tuyến, mù hệ thống (`--blank`, `--audit`) |
| `src/s7_analysis.py` | Meta-evaluation, kiểm định mù, độ nhạy, verify-then-revise → `outputs/analysis/results.json` |
| `src/s8_revise.py` | RQ3 verify-then-revise: judge 7B gắn cờ claim sai, generator 3B viết lại (tối đa 2 vòng) → `revise.jsonl` |
| `src/s9_selfcheck.py` | Baseline SelfCheckGPT-NLI: 3 mẫu temperature 0,7, mDeBERTa chấm claim → `selfcheck_scores.jsonl` |
| `make_colab.py` | Sinh `colab/ViKAG_Faith_Colab.ipynb` (bước 1–5, 8, 9 và ablation verifier trên Colab T4, kết quả lưu Drive) |
| `make_paper.py` | Bài báo (A4, lề 2,5 cm, Times New Roman 12, công thức Office): `nop_bai/ViKAG-Faith_BaiBao.docx` |
| `slides/build_paper_deck.js` | Slide thuyết trình cho bài báo, thiết kế riêng (14 trang): `nop_bai/ViKAG-Faith_BaiBao_slide.pptx` (PDF xuất từ PowerPoint) |
| `src/s3b_triples.py`, `src/s10_dot2.py`, `make_colab_dot2.py` | Đợt 2: triple + mutual index, phân tích riêng (`results_dot2.json`), notebook cho phần cần GPU |
| `make_demo.py` | Cập nhật số liệu thẳng vào `demo/vikag_faith_demo.html` (không có file khuôn riêng) |
| `make_dataset.py` | Đóng gói `dataset/ViFaithKAG` (claims/answers/passages JSONL + README, ghi nguồn ViHERMES MIT) |
| `prelabel/` | Nhãn Claude theo từng nhóm (nguồn của `outputs/prelabels.json`) |
| `external/ViHERMES` | Mã và dữ liệu ViHERMES (MIT) |

## Chạy lại

Repo không kèm `external/` và `data/`. Cần tải ViHERMES trước:

```bash
git clone https://github.com/ura-hcmut/ViHERMES.git external/ViHERMES
```

`data/` được dựng lại ở các ô cài đặt của notebook Colab.

```bash
source .venv/Scripts/activate
# Bước 1–5 (cần GPU): python make_colab.py, upload colab/ViKAG_Faith_Colab.ipynb lên Colab, Run all,
# rồi tải MyDrive/vikag-faith/vikag_outputs.zip về và giải nén vào thư mục này.
python src/s6_annotation.py --audit     # trang kiểm định mù (tùy chọn)
python src/s7_analysis.py               # phân tích
python make_paper.py                    # bài báo Word
python make_demo.py && python make_dataset.py
```

Ablation verifier: `VIKAG_NO_SYNTH=1 VIKAG_FT_TAG=nosynth python src/s5_verifier.py train|predict`
(chỉ ViNLI, không dùng cặp tổng hợp; điểm được gộp vào `verifier_scores.jsonl` dưới tên `nosynth_v1/v2`).

**Không chạy LLM trên máy này, kể cả chế độ CPU:** ngày 28/10/2026 máy tắt đột ngột (Kernel-Power 41)
khi đang chạy thử qwen2.5:7b bằng CPU. Mọi bước dùng mô hình chạy trên Colab.

Seed 42. Môi trường: Python 3.12, torch 2.6, transformers 4.46, Ollama (qwen2.5:3b, qwen2.5:7b, bge-m3).
