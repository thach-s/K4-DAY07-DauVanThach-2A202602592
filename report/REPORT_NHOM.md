# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ & Quy định Đại học — Mảng Học phí (Tuition Fees)

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề Học phí vì đây là mảng quy định quan trọng nhất đối với sinh viên, có lượng tra cứu cao và chứa nhiều thông tin có cấu trúc (mức thu, thời hạn, hình thức thanh toán, điều kiện gia hạn, chính sách miễn giảm). Ngoài ra, mảng học phí có sự phân hóa theo đối tượng sinh viên (`audience`: `student`, `faculty`) và đơn vị quản lý (`department`: `financial-affairs`, `academic-affairs`, `student-affairs`), giúp kiểm thử hiệu quả tính năng lọc theo metadata (metadata filter) trong hệ thống RAG.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Báo cáo lộ trình thu học phí USSH VNU | https://ussh.vnu.edu.vn/vi/gioi-thieu/ba-cong-khai/bao-cao-lo-trinh-thu-hoc-phi-cac-he-nam-hoc-2026-2027-19718.html | 2026-09-19 / 2026.1 | ~18,577 | `audience: student`, `department: financial-affairs`, `category: tuition` |
| 2 | Quy định mới nhất về học phí Đại học Nha Trang | https://phongkhtc.ntu.edu.vn/tin-tuc/quy-dinh-moi-nhat-ve-muc-hoc-phi-tu-nam-hoc-2025---2026 | 2026-09-19 / 2026.1 | ~13,478 | `audience: student`, `department: financial-affairs`, `category: tuition` |
| 3 | Trang quy định học phí Giáo vụ PTIT | https://giaovu.ptit.edu.vn/hoc-bong-chinh-sach/hoc-phi/ | 2026-09-19 / 2026.1 | ~8,082 | `audience: student`, `department: academic-affairs`, `category: tuition` |
| 4 | Thông báo mức thu học phí UTT | https://www.utt.edu.vn/vn/daotao/thong-bao/thong-bao-muc-thu-hoc-phi-nam-hoc-2026-2027-a17279.html | 2026-09-19 / 2026.1 | ~6,904 | `audience: student`, `department: academic-affairs`, `category: tuition` |
| 5 | Thông báo thu học phí học lại HK phụ HVTC | https://hvtc.edu.vn/TB-Ve-viec-thu-hoc-phi-hoc-lai-hoc-cai-thien-diem-hoc-bu-Hoc-ky-phu-nam-hoc-2025--2026-doi-voi-sinh-vien-cac-he-dao-tao-_34041.html | 2026-09-19 / 2026.1 | ~4,594 | `audience: student`, `department: academic-affairs`, `category: tuition` |
| 6 | Thông báo học phí và lệ phí Y Khoa Phạm Ngọc Thạch | https://www.pnt.edu.vn/vi/thong-bao/thong-bao-ve-hoc-phi-va-cac-khoan-phi-le-phi-he-dao-tao-dai-hoc-nam-hoc-2025-2026 | 2026-09-19 / 2026.1 | ~3,235 | `audience: student`, `department: financial-affairs`, `category: tuition` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `huflit-tuition-notice-2026-2027` | Định danh duy nhất tệp tài liệu trong vector store |
| `audience` | string | `student` / `faculty` / `staff` / `all` | Lọc kết quả tìm kiếm đúng đối tượng (vd: quy định học phí cho sinh viên) |
| `department` | string | `financial-affairs` / `academic-affairs` | Khoanh vùng truy xuất theo phòng ban quản lý liên quan |
| `category` | string | `tuition` | Phân loại chủ đề tài liệu phục vụ truy xuất chủ đề cụ thể |
| `source_url` | string | `https://huflit.edu.vn/...` | Cung cấp liên kết nguồn minh bạch cho AI trích dẫn |
| `retrieved_at` | string | `2026-09-19` | Đảm bảo tính cập nhật của dữ liệu và phục vụ quản trị dữ liệu |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Đậu Văn Thạch (SentenceChunker)**
- **Loại chiến lược:** `SentenceChunker` (Tách theo đơn vị câu)
- **Mô tả & lý do chọn cho chủ đề này:** Chiến lược này tự động nhận diện ranh giới các câu bằng biểu thức chính quy (regex qua dấu chấm, chấm hỏi, chấm cảm) và gom tối đa `max_sentences_per_chunk=3` câu vào 1 chunk. Lựa chọn này cực kỳ phù hợp với mảng Học phí vì các quy định học phí luôn được phát biểu thành từng câu hoàn chỉnh (như thời hạn nộp, cú pháp chuyển khoản, mức phí). Việc cắt theo câu giúp giữ trọn vẹn ngữ nghĩa từng quy định mà không bị đứt đoạn ngẫu nhiên giữa chừng như phương pháp cắt theo ký tự cố định.
- **Code snippet (implementation):**
```python
def chunk(self, text: str) -> list[str]:
    if not text or not text.strip():
        return []
    raw_sentences = re.split(r'(?<=[.!?])(?:\s+|\n+)', text)
    sentences = [s.strip() for s in raw_sentences if s.strip()]
    if not sentences:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    for i in range(0, len(sentences), self.max_sentences_per_chunk):
        group = sentences[i : i + self.max_sentences_per_chunk]
        chunk_text = " ".join(group).strip()
        if chunk_text:
            chunks.append(chunk_text)
    return chunks
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Lộ trình thu học phí năm học 2026 - 2027 tại USSH áp dụng cho đối tượng nào? | Áp dụng cho sinh viên các hệ đào tạo tại Trường ĐH KHXH&NV. | `ussh-tuition-roadmap-2026-2027` |
| 2 | Học viện Tài chính áp dụng thu học phí học lại, học cải thiện điểm Học kỳ phụ năm học 2025 - 2026 theo đợt nào? | Theo các đợt thông báo thu học phí học lại/cải thiện học kỳ phụ cho sinh viên các hệ đào tạo. | `hvtc-summer-retake-tuition` |
| 3 | Quy định mức thu học phí mới nhất tại Đại học Nha Trang áp dụng từ năm học nào? | Áp dụng từ năm học 2025 - 2026. | `ntu-tuition-regulations-2025-2026` |
| 4 | Thông báo mức thu học phí tại Đại học Công nghệ GTVT (UTT) áp dụng cho năm học nào? | Áp dụng cho năm học 2026 - 2027. | `utt-tuition-rates-2026-2027` |
| 5 | Các khoản phí, lệ phí hệ đào tạo đại học năm học 2025 - 2026 của Trường ĐH Y khoa Phạm Ngọc Thạch do phòng ban nào quản lý? *(Cần lọc `department: financial-affairs`)* | Phòng Kế hoạch Tài chính (Trường ĐH Y khoa Phạm Ngọc Thạch). | `pnt-tuition-and-fees-2025-2026` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
