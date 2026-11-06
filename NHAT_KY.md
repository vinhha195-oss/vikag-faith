# Nhật ký dự án ViKAG-Faith

Danh sách việc đã làm, từ lúc chọn đề tài đến bản cuối (22/10 – 05/11/2026).

## Giai đoạn 1 · Chọn đề tài và đề cương (22/10)

1. Đọc file PDF 4 đề tài KAG tiếng Việt, chọn **Project 4 – ViKAG-Faith** (độ khó trung bình–thấp, ít GPU).
2. Tìm hiểu tổng quan KAG (OpenSPG/KAG).
3. Viết đề cương rút gọn (Claude Docs).
4. Chốt hình thức: bài tập/tiểu luận, file PDF, quy mô pilot.

## Giai đoạn 2 · Dựng pipeline (22–23/10)

5. Tải ViHERMES (bộ câu hỏi pháp quy y tế, giấy phép MIT), dựng graph văn bản (SQLite).
6. Viết 7 bước mã nguồn trong `src/`:
   - `s1` trả lời 100 câu hỏi (20 câu mỗi mức 1–5 hop) bằng 2 hệ: Naive RAG và GraphRAG, cùng Qwen2.5-3B
   - `s2` tách câu trả lời thành claim
   - `s3` gom tập bằng chứng (đoạn truy xuất ∪ đoạn vàng + thông tin graph), chọn mẫu 40 câu × 2 hệ = 80 câu trả lời
   - `s4` RAGAS (tái hiện 2 prompt gốc) và LLM-judge mức claim, Qwen 3B/7B
   - `s5` verifier mDeBERTa: zero-shot, V1 (chỉ đoạn văn) / V2 (+ graph), dữ liệu tổng hợp + ViNLI để fine-tune
   - `rules.py` rule kiểm tra số / ngày / số hiệu văn bản
   - `s7` phân tích: macro-F1, AUROC, Spearman/Kendall, bootstrap, Wilcoxon
7. **Sự cố máy:** GPU GTX 1650 làm treo máy khi chạy mô hình, nên chuyển sang CPU rồi sang **Google Colab** (`make_colab.py` sinh notebook, kết quả lưu Drive).
8. Chạy bước 1–5 trên Colab: 610 claim, 284 claim trong mẫu gán nhãn.

## Giai đoạn 3 · Gán nhãn và báo cáo đầu tiên (23–28/10)

9. Claude gán nhãn silver cho 284 claim (supported / contradicted / unsupported).
10. Trang gán nhãn HTML ngoại tuyến, mù hệ thống (`s6_annotation.py`).
11. **Lượt A** (duyệt có gợi ý): 284 claim xác nhận trong ~10 phút, 0 thay đổi, nên **bị loại**, không coi là nhãn người.
12. **Lượt C** (kiểm định mù): 60 claim, người gán từ đầu, không gợi ý. Claude trùng người 60%, κ = 0,29.
13. Báo cáo PDF bản 1 (HTML → PDF qua Edge), demo tra cứu bản 1.

## Giai đoạn 4 · Đối chiếu đề cương và bổ sung (28/10)

14. Đối chiếu với yêu cầu Project 4, lập danh sách hạng mục còn thiếu.
15. **RQ3 verify-then-revise** (`s8_revise.py`): judge 7B gắn cờ claim sai, bộ sinh viết lại, tối đa 2 vòng.
16. **Baseline SelfCheckGPT** (`s9_selfcheck.py`).
17. **Ablation không dữ liệu tổng hợp** cho verifier.
18. **Sự cố máy lần 2:** máy tắt đột ngột khi chạy thử 7B bằng CPU. Từ đó không chạy LLM trên máy nữa, chỉ thử logic bằng mô hình giả.
19. Chạy Colab lần 1, **phát hiện lỗi:** mọi lần fine-tune trước đều có loss = NaN (checkpoint fp16), nên kết luận cũ "fine-tune không giúp" là sai.
20. Sửa (ép float32, chặn loss NaN), chạy Colab lần 2: fine-tune V1 đạt macro-F1 0,521.
21. Viết lại báo cáo theo đúng 3 RQ của đề cương, thêm kiểm định ghép cặp.
22. Ablation số vòng sửa, EM và token recall.
23. Phụ lục A: bảng đối chiếu 39 hạng mục đề cương (20 đạt / 14 một phần / 5 chưa làm).
24. Đăng demo tra cứu, đóng gói bộ dữ liệu **ViFaithKAG** (`make_dataset.py`).

## Giai đoạn 5 · Nhãn người bổ sung (29–30/10)

25. **Lượt D** (224 claim): file xuất không được tạo qua trang gán nhãn (`confirmed = false` ở mọi claim; có file `*_D_claude.*` do Claude tạo), nên **không dùng**.
26. **Lượt E**: chép lại nhãn của D, nên **không dùng**.
27. **Lượt F** (101 claim): quá khó, chưa làm.
28. **Lượt G** (`s6_quick.py`): trang rút gọn, 30 claim ngẫu nhiên, mỗi màn hình một claim. Người gán thật trong 17,6 phút, 24 claim dùng được.
29. Gộp C + G = 84 claim nhãn người: Claude trùng 60%, κ = 0,25.
29b. **Lượt H** (31/10): thêm 30 claim ngẫu nhiên, gán thật trong 12,7 phút. Gộp C + G + H = **114 claim nhãn người**: Claude trùng 61%, κ = 0,28. Theo nhãn người, judge 7B tốt nhất (0,527); fine-tune (0,398) không hơn zero-shot (0,410).
29c. **Lượt I** (01/11): thêm 30 claim, gán thật trong 10,8 phút. Gộp C + G + H + I = **139 claim nhãn người** (49% bộ dữ liệu): Claude trùng 63%, κ = 0,28. Theo nhãn người, judge 7B tốt nhất (0,553); fine-tune (0,379) ngang zero-shot (0,377).
29d. **Lượt J** (01/11): thêm 30 claim, gán thật trong 8,8 phút. Gộp C + G + H + I + J = **165 claim nhãn người** (58% bộ dữ liệu): Claude trùng 65%, κ = 0,29. Theo nhãn người, judge 7B tốt nhất (0,528); fine-tune (0,381) không hơn zero-shot (0,409).

## Giai đoạn 6 · Sản phẩm cuối (29–31/10)

30. Báo cáo **Word** (`make_word.py`, có mục lục, 14 trang).
31. **Slide PowerPoint** 14 trang (`slides/build_deck.js`), biểu đồ gốc, có ghi chú thuyết trình.
32. Demo tra cứu: làm gọn (mặc định một nhãn mỗi claim).
33. **Demo kể chuyện** 4 tab (`story_template.html`): đề tài là gì, 4 ví dụ đã được người kiểm tra, tự khám phá 80 câu trả lời, kết quả bằng lời thường.
34b. **Bài báo theo mẫu môn học** (02–03/11): `make_paper.py` dựng `report/ViKAG-Faith_BaiBao.docx` (12 trang, 4 hình, 11 bảng, 21 tài liệu tham khảo) theo cấu trúc file mẫu; slide 21 trang theo mẫu (`slides/build_paper_deck.js`). Tên tác giả và môn học để trống `[Họ và tên]`, `[Môn học]`.
34. Đồng bộ lại toàn bộ: báo cáo, slide, demo, dataset, README.
35. **Bản nộp cuối** (05/11): slide thiết kế lại, rút còn 14 trang; bài báo Times New Roman, A4, công thức Office (13 trang). Dọn dự án: bỏ báo cáo cũ và bộ slide cũ (còn trong commit `06f8888`), gom 3 file nộp vào `nop_bai/`; gộp hai demo thành một file `demo/vikag_faith_demo.html`.

36. **Đợt 2** (05/11): 467 triple + mutual index, 19.992 cặp tổng hợp. Chạy được trên CPU: triple V3 zero-shot (0,423 theo silver, 0,328 theo nhãn người). Huấn luyện 20.000 cặp cần khoảng 17 giờ trên CPU nên chuyển sang Colab, cùng judge 14B, Qwen span, XLM-R (`colab/ViKAG_Faith_Dot2.ipynb`).

## Kết quả chính

| Câu hỏi | Kết quả |
|---|---|
| RQ1 | Judge 7B tốt nhất ở mức claim, RAGAS 7B tốt nhất ở mức câu trả lời; chỉ khớp mức trung bình. Máy bắt nhiều nhất được 41/64 ý sai (judge 7B, nhãn silver) |
| RQ2 | Dữ liệu tổng hợp giúp theo nhãn silver (0,404 → 0,521) nhưng không giữ được theo nhãn người (165 claim: 0,381 so với 0,409); thông tin graph và rule không giúp |
| RQ3 | Sửa giảm claim mâu thuẫn (8,8% → 4,1%) nhưng câu trả lời ngắn và thiếu hơn |
| Hai hệ | Naive RAG và GraphRAG ngang nhau (p = 0,191); câu 4–5 hop khó hơn rõ |

## Sản phẩm

| Loại | Vị trí |
|---|---|
| Bài báo Word | `nop_bai/ViKAG-Faith_BaiBao.docx` |
| Slide | `nop_bai/ViKAG-Faith_BaiBao_slide.pptx`, `.pdf` (14 trang) |
| Demo | `demo/vikag_faith_demo.html` (https://claude.ai/artifact/Hav1SviyP3Q9rQcBY8dGHG) |
| Bộ dữ liệu | `dataset/ViFaithKAG/` |
| Mã nguồn | `src/`, notebook Colab `colab/ViKAG_Faith_Colab.ipynb` |

## Chưa làm (so với đề cương)

Verifier Qwen trả span bằng chứng · bộ ViEduReg (quy chế đào tạo) · baseline ViHallu · toán tử Verify trong KAG · chatbot quy chế.
Thu nhỏ: 2 hệ thay vì 5, 284 claim thay vì ~3.000 (165 có nhãn người), 1 người gán, judge 7B thay vì 32B.

37. **Fine-tune đợt 2** (06/11): `run_dot2_gpu.sh` chạy 2 giờ trên GTX 1650 (29.993 cặp, premise 450 ký tự, 200 token, dev kiểm tra 1.000 cặp). Dev tổng hợp 0,594 → 0,897 nhưng trên claim thật không tốt hơn đợt 1: V1 0,441 (KTC 0,36–0,53), V3 0,501; AUROC 0,753 so với 0,738, chênh không có ý nghĩa; theo nhãn người 0,371 và 0,404. Ngưỡng V1 rơi vào cận dưới của lưới, nhưng lưới rộng hơn (chọn trên dev) còn thấp hơn (0,384). Judge 14B, Qwen span và XLM-R chưa chạy vì cần Colab. `results.json` không đổi.
