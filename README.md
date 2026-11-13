# ViKAG-Faith (pilot)

Đánh giá tính trung thực (faithfulness) mức claim cho hệ hỏi đáp GraphRAG tiếng Việt trên dữ liệu
[ViHERMES](https://github.com/ura-hcmut/ViHERMES) (văn bản pháp quy y tế).

**Sản phẩm nộp (thư mục [nop_bai/](nop_bai/)):** bài báo Word, slide PowerPoint, slide PDF · số liệu gốc:
[outputs/analysis/results.json](outputs/analysis/results.json) · đề cương:
https://claude.ai/artifact/Ek3Puhkwvimrrbj97ojenf

## Kết quả chính

| Câu hỏi | Kết quả |
|---|---|
| RQ1, mức claim | Đợt 1, trong các metric có sẵn, LLM-judge Qwen2.5-7B tốt nhất: macro-F1 0,476 (silver), 0,528 (nhãn người); SelfCheckGPT 0,409; judge 7B bắt được 41/64 claim sai. Đợt 2 judge 14B đạt 0,541 (silver), 0,439 (nhãn người), bắt được 45/65; chênh với 7B không có ý nghĩa ở cả hai bộ nhãn |
| RQ1, mức câu trả lời | RAGAS faithfulness tương quan cao nhất với GGF chuẩn: Spearman 0,484 với 7B, 0,644 với 14B (61 câu trả lời, chưa kiểm định chênh lệch) |
| RQ2 | Verifier fine-tune (ViNLI + cặp tổng hợp) 0,521 > zero-shot 0,404 (silver, có ý nghĩa); ablation chỉ ViNLI 0,405; nhưng trên mẫu người fine-tune chỉ 0,381 < judge-7B 0,528. Graph trong NLI và rule số/ngày không giúp; triple nối theo claim (V3, zero-shot) đạt 0,423 theo silver, 0,328 theo nhãn người. Đợt 2 fine-tune với khoảng 20.000 cặp tổng hợp không tốt hơn: V1 0,441, V3 0,501 theo silver, 0,371 và 0,404 theo nhãn người; AUROC 0,753 so với 0,738 của đợt 1, không khác có ý nghĩa (premise 450 ký tự, 200 token do GPU 4 GB). Huấn luyện lại với 900 ký tự, 320 token: V1 0,572 theo silver, cao nhất, không hơn đợt 1 có ý nghĩa, 0,356 theo nhãn người. XLM-R zero-shot V1 đạt 0,532 theo silver, 0,354 theo nhãn người; XLM-R fine-tune V1 đạt 0,500 và 0,463 (hơn zero-shot theo nhãn người, KTC 0,02–0,20, nhưng báo nhầm 64/153), V3 có AUROC 0,821; Qwen 3B trả span đạt 0,361 và 0,399, 130/263 nhãn kèm span chép đúng từ bằng chứng |
| RQ3 | Verify-then-revise: GGF theo judge 7B 0,755 → 0,830 (p = 0,014) nhưng token F1 0,595 → 0,563; câu trả lời chủ yếu ngắn đi. Vòng 1 cho phần lớn mức tăng (GGF 0,801); vòng 2 không có ý nghĩa thống kê (p = 0,312). EM = 0 ở mọi cấu hình (đáp án ViHERMES dài ~115 từ) |
| Đợt 3 | XLM-R luyện thêm 2.946 cặp lỗi sát thực tế (đổi cơ quan, chèn mục vào danh sách, phủ nhận sai): 0,643 theo silver, cao nhất và hơn judge 7B có ý nghĩa, nhưng 0,450 theo nhãn người, không hơn XLM-R đợt 2. Máy chấm hai tầng (fine-tune V1 tự quyết nửa số claim chắc nhất, nửa còn lại gửi judge 7B): 0,530 theo nhãn người, ngang judge chấm toàn bộ; tỉ lệ 50% chọn sau khi xem kết quả |
| Đợt 4 | Judge Qwen2.5-32B (Kaggle): 0,571 theo silver, 0,377 theo nhãn người, kém judge 7B có ý nghĩa (−0,151, KTC −0,26 đến −0,03); lần thứ tư lặp lại khuôn mẫu "silver tăng, người không tăng". ViEduReg bản thử (30 câu về văn bản kiểm định chất lượng giáo dục đại học, 77 claim silver): judge 7B 0,527, XLM-R đợt 3 chỉ 0,269 vì báo nhầm 34/55 claim đúng |
| Toán tử Verify kiểu KAG | XLM-R kiểm từng claim, claim chưa chắc chuyển judge 7B (27 lần gọi cho 284 claim), kiểm số hiệu văn bản, rồi sửa một lần hoặc từ chối. Theo nhãn người 0,479, không khác judge 7B có ý nghĩa. Chấm lại bằng judge 14B: GGF 0,691 → 0,805, ngang cách sửa cũ (0,806), nhưng từ chối 31/80 câu, trong đó 13 câu vốn đúng hết |
| Hai hệ | Naive RAG và GraphRAG ngang nhau (GGF 0,694 và 0,638, p = 0,191); câu 4–5 hop giảm mạnh |
| Năm hệ (đợt 4) | Thêm BM25, vector, Naive RAG với Qwen 7B trên cùng 40 câu, 413 claim nhãn silver (`outputs/dot4_silver.json`, Claude gán trên câu trích ngắn, không phải nhãn người). GGF silver: Naive 0,694 > GraphRAG 0,638 > Naive 7B 0,616 > BM25 0,575 > vector 0,532; judge 7B xếp gần ngược (ρ = −0,60 trên 5 hệ). Trên claim mới: XLM-R đợt 3 0,563, judge 7B 0,525 |
| Độ tin cậy nhãn | Năm lượt kiểm định mù do người gán (C: 60 claim phân tầng; G–J: 4 × 30 claim ngẫu nhiên, còn 105): gộp 165 claim (58% bộ dữ liệu), Claude trùng người 65%, κ = 0,29, tương quan thứ hạng metric 0,46. Theo nhãn người, judge-7B tốt nhất (0,528); verifier fine-tune (0,381) không hơn zero-shot (0,409) |

**Demo:** `demo/vikag_faith_demo.html`, một file duy nhất, mở bằng trình duyệt, không cần mạng (5 tab: đề tài là gì, 4 ví dụ đã được người kiểm tra, tra cứu 80 câu trả lời, kết quả đợt 1–4, thử trực tiếp với 8 câu chatbot chạy sẵn). Bản đăng: https://claude.ai/artifact/Hav1SviyP3Q9rQcBY8dGHG ·
**Dữ liệu:** `dataset/ViFaithKAG/` (sinh bởi `make_dataset.py`).

Lưu ý: các lần fine-tune trước 28/10/2026 trên Colab bị loss = NaN (checkpoint fp16), nên kết luận cũ "fine-tune không giúp ích" là sai.

## Tiến trình (cập nhật 13/11/2026)

| Hạng mục trong đề cương | Trạng thái |
|---|---|
| Quy trình đánh giá mức claim trên ViHERMES, 284 claim có nhãn | Xong (đợt 1) |
| So sánh RAGAS, LLM-judge, SelfCheckGPT, NLI, rule | Xong (đợt 1–2) |
| Judge lớn: 14B, 32B | Xong (đợt 2, đợt 4) |
| Verifier fine-tune, dữ liệu tổng hợp, dữ liệu lỗi sát thực tế | Xong (đợt 1–3) |
| Verify-then-revise, toán tử Verify kiểu KAG | Xong (đợt 1, đợt 4) |
| 5 hệ hỏi đáp | Xong, nhưng 3 hệ mới chỉ có nhãn silver (đợt 4) |
| ViEduReg | Bản thử 30 câu, nhãn silver (đợt 4) |
| Khoảng 3.000 claim | Chưa: 697 claim (284 + 413) |
| Nhãn người | 165 claim, một người gán; người thứ hai (lượt K, `outputs/annotation/annotate_K.html`) chưa làm |
| Bài Word 14 trang, slide 14 trang + PDF, demo | Xong, đã cập nhật đợt 4 |
| Bản IEEE | Mã nguồn đã cập nhật đợt 4; cần biên dịch lại trên Overleaf (PDF trong `nop_bai/` là bản 06/11) |

## Nguồn nhãn

- Mọi phép đo dùng **nhãn silver do Claude gán** cho 284 claim (`outputs/prelabels.json`); 413 claim của ba hệ đợt 4 (`outputs/dot4_silver.json`) và 77 claim ViEduReg (`outputs/viedureg/silver_labels.json`) cũng là nhãn silver.
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
| `src/s4_judges.py` | RAGAS (tái hiện 2 prompt gốc) và LLM-judge mức claim, Qwen2.5 3B/7B/14B, verifier Qwen trả span |
| `src/s5_verifier.py` | Dữ liệu tổng hợp + ViNLI, fine-tune và chấm mDeBERTa-v3-base-xnli (V1/V2) |
| `src/rules.py` | Rule kiểm tra số, ngày, số hiệu văn bản |
| `src/s6_annotation.py` | Trang gán nhãn HTML ngoại tuyến, mù hệ thống (`--blank`, `--audit`) |
| `src/s7_analysis.py` | Meta-evaluation, kiểm định mù, độ nhạy, verify-then-revise → `outputs/analysis/results.json` |
| `src/s8_revise.py` | RQ3 verify-then-revise: judge 7B gắn cờ claim sai, generator 3B viết lại (tối đa 2 vòng) → `revise.jsonl` |
| `src/s9_selfcheck.py` | Baseline SelfCheckGPT-NLI: 3 mẫu temperature 0,7, mDeBERTa chấm claim → `selfcheck_scores.jsonl` |
| `make_colab.py` | Sinh `colab/ViKAG_Faith_Colab.ipynb` (bước 1–5, 8, 9 và ablation verifier trên Colab T4, kết quả lưu Drive) |
| `make_paper.py` | Bài báo (A4, lề 2,5 cm, Times New Roman 12, công thức Office): `nop_bai/ViKAG-Faith_BaiBao.docx` |
| `slides/build_paper_deck.js` | Slide thuyết trình cho bài báo, thiết kế riêng (14 trang): `nop_bai/ViKAG-Faith_BaiBao_slide.pptx` (PDF xuất từ PowerPoint) |
| `src/s13_cascade.py`, `src/s14_hardneg.py`, `src/s18_dot3.py`, `make_colab_dot3.py` | Đợt 3: máy chấm hai tầng, dữ liệu lỗi sát thực tế, notebook Colab (luyện XLM-R, chatbot kiểm chứng trực tiếp `src/s16_live.py`), phân tích (`results_dot3.json`) |
| `src/s19_dot4.py`, `src/s20_viedureg.py`, `src/s21_dot4.py`, `src/s22_record.py` | Đợt 4: ba hệ mới, ViEduReg (`outputs/viedureg/`), toán tử Verify, phân tích (`results_dot4.json`), ghi sẵn 8 câu chatbot cho demo (`dot4_live.jsonl`) |
| `make_colab_dot4.py`, `make_kaggle_32b.py`, `make_kaggle_dot4.py` | Notebook đợt 4: Colab (`colab/ViKAG_Faith_Dot4.ipynb`), Kaggle 2 × T4 cho judge 32B (`kaggle/ViKAG_Judge32B.ipynb`) và phần B–D khi Colab hết GPU (`kaggle/ViKAG_Dot4.ipynb`) |
| `src/s6_second.py`, `src/s17_check_app.py` | Trang gán nhãn cho người thứ hai (pass K, 57 claim bất đồng trộn 23 claim đồng thuận); app kiểm chứng chạy trên máy, không cần LLM |
| `make_paper_ieee.py`, `ieee/` | Bản tiếng Anh theo mẫu IEEE (IEEEtran); tải `ieee/ViKAG-Faith_IEEE_Overleaf.zip` lên Overleaf để biên dịch |
| `src/s3b_triples.py`, `src/s10_dot2.py`, `make_colab_dot2.py` | Đợt 2: triple + mutual index, phân tích riêng (`results_dot2.json`), notebook Colab cho judge 14B, Qwen span, XLM-R và fine-tune 900 ký tự |
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
