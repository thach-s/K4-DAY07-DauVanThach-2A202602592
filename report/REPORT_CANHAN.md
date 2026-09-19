# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đậu Văn Thạch
**Nhóm:** K4-Day07 Group
**Ngày:** 2026-09-19

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiệm cận 1.0) nghĩa là hai vectơ chỉ cùng về một hướng trong không gian đa chiều, thể hiện hai văn bản có nội dung/ngữ nghĩa rất gần gũi nhau bất kể độ dài ngắn của đoạn văn.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên cần nộp học phí trước ngày 15 tháng 9.
- Câu B: Hạn chót đóng tiền học cho sinh viên là ngày 15/09.
- Tại sao tương đồng: Cả hai câu cùng diễn đạt một ý nghĩa về thời hạn nộp học phí, dùng từ vựng đồng nghĩa trong cùng bối cảnh.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Quy trình đăng ký học phần trên trang học vụ.
- Câu B: Công thức chế biến món phở bò truyền thống.
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau (giáo dục vs ẩm thực), từ vựng và vectơ biểu diễn không có điểm tương đồng.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Độ tương tự cosine chỉ đo góc giữa 2 vectơ mà bỏ qua độ dài (magnitude). Điều này giúp so sánh chuẩn xác ngữ nghĩa giữa các đoạn văn dài/ngắn khác nhau mà không bị ảnh hưởng bởi số lượng từ trong chunk.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Bước nhảy (step) = `chunk_size - overlap` = `500 - 50` = `450` ký tự.
> - Chunk 1: [0 : 500]. Phần còn lại sau chunk 1 là 9,500 ký tự.
> - Số bước tiếp theo = `ceil(9500 / 450)` = `ceil(21.11)` = 22 bước.
> - Tổng số chunks = `1 + 22` = **23 chunks**.
> 
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Nếu overlap tăng lên 100, bước nhảy giảm xuống còn 400 ký tự, số lượng chunk tăng lên thành 25 chunks. Độ chồng chéo nhiều hơn giúp đảm bảo thông tin quan trọng nằm ở ranh giới giữa hai chunk không bị ngắt đôi hay mất ngữ cảnh.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Hàm sử dụng biểu thức chính quy (regex) `r'(?<=[.!?])(?:\s+|\n+)'` để nhận diện điểm kết thúc câu dựa trên các dấu chấm, chấm hỏi, chấm cảm kết hợp khoảng trắng hoặc xuống dòng. Xử lý trường hợp ngoại lệ bằng cách loại bỏ khoảng trắng dư thừa (`strip()`), loại bỏ các chuỗi rỗng và xử lý văn bản không chứa dấu ngắt câu bằng cách trả về toàn bộ văn bản như 1 câu duy nhất. Sau đó gom nhóm tối đa `max_sentences_per_chunk` câu liên tiếp thành từng chunk hoàn chỉnh.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán chia nhỏ đệ quy theo thứ tự ưu tiên separator `["\n\n", "\n", ". ", " ", ""]`. Trường hợp cơ sở (base case) là khi văn bản nhỏ hơn `chunk_size` hoặc đã hết danh sách separator. Nếu một đoạn vẫn vượt quá `chunk_size`, thuật toán tiếp tục gọi đệ quy `_split` với separator mức thấp hơn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi document được chuyển thành một bản ghi chứa `id`, `content`, `metadata` và vectơ `embedding` được tạo từ `_embedding_fn`. Khi tìm kiếm (`search`), hàm tính toán độ tương tự Cosine giữa vectơ câu hỏi và từng bản ghi trong store, sau đó sắp xếp giảm dần và lấy top-k kết quả cao nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Với `search_with_filter`, hệ thống thực hiện pre-filtering: lọc trước các bản ghi khớp hoàn toàn các cặp key-value trong `metadata_filter`, sau đó mới tính độ tương tự vector trên tập đã lọc. Với `delete_document`, hệ thống tìm và xóa tất cả các bản ghi có `id` hoặc `metadata['doc_id']` khớp với tham số truyền vào.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Hàm gọi `store.search` để truy xuất top-k chunks liên quan nhất từ vector store, sau đó ghép các chunk này thành đoạn `Context:` đánh số thứ tự `[1]`, `[2]...` để bơm vào Prompt gửi cho LLM tổng hợp câu trả lời minh bạch.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform linux -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/thach2207/K4-DAY07-DauVanThach-2A202602592
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================== 42 passed in 0.14s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Học phí kỳ 1 nộp trước 15/09. | Thời hạn đóng tiền học HK1 là 15/09. | cao | 0.92 | Có |
| 2 | Hướng dẫn nộp đơn xin gia hạn học phí. | Thủ tục xét miễn giảm học phí sinh viên. | cao | 0.78 | Có |
| 3 | Quy định mức thu học phí năm 2026. | Công thức nấu món phở bò Hà Nội. | thấp | 0.05 | Có |
| 4 | Sinh viên học lại đóng học phí theo tín chỉ. | Đăng ký lớp học phần trên hệ thống học vụ. | cao | 0.68 | Có |
| 5 | Phòng Kế hoạch Tài chính xử lý thắc mắc học phí. | Thư viện trường mở cửa vào cuối tuần. | thấp | 0.12 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả cặp số 4 có độ tương đồng khá cao dù một câu nói về học phí học lại và một câu nói về đăng ký lớp học phần. Điều này phản ánh rằng mô hình embedding bắt được ngữ cảnh đồng xuất hiện trong môi trường đại học (sinh viên, học phần, tín chỉ).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src` (sử dụng chiến lược `SentenceChunker`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Lộ trình thu học phí năm học 2026 - 2027 tại USSH áp dụng cho đối tượng nào? | Áp dụng cho sinh viên các hệ đào tạo tại Trường ĐH KHXH&NV... | 0.89 | Có | Áp dụng cho sinh viên các hệ đào tạo USSH. |
| 2 | Học viện Tài chính áp dụng thu học phí học lại, học cải thiện điểm Học kỳ phụ năm học 2025 - 2026 theo đợt nào? | Thông báo thu học phí học lại, học cải thiện điểm đợt học kỳ phụ... | 0.85 | Có | Áp dụng theo các đợt thu học kỳ phụ được công bố. |
| 3 | Quy định mức thu học phí mới nhất tại Đại học Nha Trang áp dụng từ năm học nào? | Quy định mới nhất về mức học phí từ năm học 2025 - 2026... | 0.91 | Có | Áp dụng từ năm học 2025 - 2026. |
| 4 | Thông báo mức thu học phí tại Đại học Công nghệ GTVT (UTT) áp dụng cho năm học nào? | Thông báo mức thu học phí năm học 2026 - 2027 dành cho sinh viên... | 0.88 | Có | Áp dụng cho năm học 2026 - 2027. |
| 5 | Các khoản phí, lệ phí hệ đào tạo đại học năm học 2025 - 2026 của Trường ĐH Y khoa Phạm Ngọc Thạch do phòng ban nào quản lý? | Thông báo về học phí và các khoản phí lệ phí Y khoa Phạm Ngọc Thạch (Phòng KHTC)... | 0.87 | Có | Do Phòng Kế hoạch Tài chính quản lý. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua trải nghiệm thực hành, việc chia nhỏ theo đơn vị câu (`SentenceChunker`) giúp các câu trả lời hoàn toàn tròn ý và không bị cắt đứt giữa câu, giúp Agent đưa ra câu trả lời chuẩn xác và tự nhiên hơn so với phương pháp chia theo ký tự cố định.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
