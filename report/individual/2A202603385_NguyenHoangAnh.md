# Báo cáo cá nhân — Day 06: Data Ingestion Engineering

**Học viên**: Nguyễn Hoàng Anh  
**MSSV**: 2A202603385  
**Lớp**: K5-L3A  
**Corpus**: U.S. History (OpenStax, Rice University)  
**Repository**: [K5-L3A-Day06-NguyenHoangAnh-2A202603385-DataIngestionEngineering](https://github.com/hoanganh-nguyen/K5-L3A-Day06-NguyenHoangAnh-2A202603385-DataIngestionEngineering)

---

## 1. Dữ liệu và Ingestion Pipeline

### 1.1. Chủ đề, nguồn tài liệu và quy tắc tuyển chọn trang
- **Tác phẩm**: *U.S. History*, phát hành bởi Nhà xuất bản OpenStax, Đại học Rice.
- **Bản quyền**: Giấy phép mở Creative Commons Attribution Non-Commercial ShareAlike 4.0 International License (`CC BY-NC-SA 4.0`).
- **File dữ liệu**: `starter/data/US_History_-_WEB.pdf` (Tổng số trang vật lý: 987 trang).
- **Quy tắc tuyển chọn trang (Manifest Rule)**:
  - Loại bỏ hoàn toàn 22 trang đầu (trang 1–22) gồm: bìa trước, thông tin bản quyền, mục lục (TOC), trang trắng và lời tựa (preface).
  - Lấy phạm vi trang vật lý từ **trang 23 đến 100** (tương ứng với số trang in trong sách từ trang 7 đến trang 84), bao quát trọn vẹn 3 chương đầu:
    - *Chapter 1: The Americas, Europe, and Africa Before 1492* (Trang 23–46)
    - *Chapter 2: Early Globalization: The Atlantic World, 1492–1650* (Trang 47–72)
    - *Chapter 3: Creating New Social Orders: Colonial Societies, 1500–1700* (Trang 73–100)
  - **Khối lượng trích xuất**: Tổng cộng **78 trang** (gồm 71 trang bài học lịch sử cốt lõi và 7 trang câu hỏi ôn tập cuối chương). Tổng số ký tự đạt **231,021 ký tự** (~36,542 từ, trung bình ~2,962 ký tự/trang), vượt xa yêu cầu tối thiểu 30 trang theo quy định.

### 1.2. Chuẩn hóa văn bản và giới hạn
- Chuẩn hóa Unicode theo định dạng `NFC`, chuyển đổi ký tự non-breaking space `\xa0` thành khoảng trắng tiêu chuẩn, loại bỏ khoảng trắng dư thừa, chuẩn hóa dấu ngắt dòng nhưng duy trì ranh giới phân tách đoạn văn (`\n\n`).
- Vì tài liệu là định dạng PDF số hóa gốc (Prince XML 16.2), văn bản trích xuất đạt độ chính xác gần như tuyệt đối, không có lỗi nhận dạng ký tự (OCR artifact).

### 1.3. Mô hình Embedding, Vector Store và Chi phí
- **Embedding Model**: OpenAI `text-embedding-3-small`, kích thước vector **1,536 chiều**, metric Cosine Distance (`<=>`), điểm tương đồng được tính theo công thức `1 - (embedding <=> query)`.
- **Vector Store**: **PostgreSQL 16** tích hợp extension **`pgvector`** (v0.8.x) chạy trong Docker container cô lập local (cổng `127.0.0.1:55433`).
- **Lệnh thực thi**: `cd starter; python -m src.run`
- **Chi phí thực tế**: **$0.00** (chi phí API chỉ tiêu tốn ~0.0003 USD nằm trong mức credit thử nghiệm).

### 1.4. Thiết kế Metadata
- **Trường bắt buộc**: `document_id` (`openstax-us-history`), `source` (`starter/data/US_History_-_WEB.pdf`), `page` (trang vật lý 23–100).
- **Trường bổ sung làm bộ lọc**: `chapter` (ví dụ: `Chapter 1`, `Chapter 2`, `Chapter 3`), `section` (ví dụ: `1.1 The Americas`), `book_page`.
- **Lý do chọn**: Các sự kiện lịch sử trong corpus phân định rõ ràng theo bối cảnh thời kỳ trong từng chương. Việc áp dụng bộ lọc `chapter` giúp hệ thống loại bỏ triệt để các kết quả gây nhiễu từ các thời kỳ khác khi người dùng có chỉ định phạm vi.

---

## 2. Thiết lập Chiến lược và Benchmark

### 2.1. Ba cấu hình thử nghiệm (Strategies A, B, C)
1. **Cấu hình A (Fixed-size Baseline)**:
   - Chunking: Cửa sổ trượt cố định **500 ký tự**, độ gối đầu (**overlap**) **50 ký tự**.
   - Metadata: Đầy đủ thông tin nguồn và trang; **không áp dụng bộ lọc**.
   - Tổng số chunk sinh ra: **539 chunks**.
2. **Cấu hình B (Structure / Paragraph-aware)**:
   - Chunking: Tách theo ranh giới đoạn văn tự nhiên (`\n\n`), gom nhóm tối đa **800 ký tự/chunk**. Nếu một đoạn văn dài vượt quá 800 ký tự sẽ được tách nhẹ nhàng tại ranh giới câu (`. `, `? `, `! `) để không làm đứt gãy ý nghĩa.
   - Metadata: Tương tự A; **không áp dụng bộ lọc**.
   - Tổng số chunk sinh ra: **349 chunks** (giảm 35.3% số lượng chunk so với A).
3. **Cấu hình C (Structure + Metadata Filter)**:
   - Chunking: **Tái sử dụng nguyên vẹn 349 chunks của Cấu hình B**.
   - Truy xuất: Áp dụng điều kiện lọc metadata `chapter` trong câu lệnh SQL (`WHERE chapter ILIKE ...`) khi câu hỏi có yêu cầu bộ lọc. Khác biệt duy nhất giữa B và C là bộ lọc metadata.

### 2.2. Bộ dữ liệu Benchmark và Kiểm chứng Ground Truth
- Bộ câu hỏi gồm **20 câu hỏi** được đóng băng trước khi chạy thử nghiệm:
  - **15 câu Dev** (`q01`–`q15`) và **5 câu Test** (`q16`–`q20`).
  - Phân loại: 9 câu hỏi trực tiếp (`truc_tiep`), 6 câu diễn đạt lại (`dien_dat_lai`), 5 câu điều kiện/ngoại lệ (`dieu_kien_ngoai_le`).
  - Metadata Filter: **5 câu có chỉ định bộ lọc** (`q04`, `q08` thuộc Dev; `q17`, `q18`, `q20` thuộc Test).
  - Kiểm chứng bằng chứng: 100% các đoạn `evidence_quote` đều được kiểm tra đối sánh khớp chính xác từng ký tự trong file PDF gốc tại đúng trang `gold_page`.

### 2.3. Tiêu chí chọn chiến lược trước khi xem Test
1. **Ưu tiên 1**: Evidence Hit@3 trên tập Dev đạt tối thiểu 85%.
2. **Ưu tiên 2**: Chunk Coherence và Grounding Quality cao nhất (tránh cắt đứt ngữ cảnh).
3. **Ưu tiên 3**: Tối ưu tài nguyên lưu trữ (ít chunk hơn) và tốc độ nạp dữ liệu nhanh hơn.

---

## 3. Kết quả Thử nghiệm

### 3.1. Bảng 1: Hiệu năng Truy xuất và Tài nguyên (Retrieval Accuracy & Resource)

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian Ingest | Chi phí |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **A (Fixed-size: 500, ov 50)** | **DEV**  | 11/15 (73.33%) | 13/15 (86.67%) | 539 | 16.58s | $0 |
| **A (Fixed-size: 500, ov 50)** | **TEST** | 3/5 (60.00%) | 4/5 (80.00%) | 539 | 16.58s | $0 |
| **B (Paragraph: max 800)**     | **DEV**  | 8/15 (53.33%) | 13/15 (86.67%) | 349 | 7.66s | $0 |
| **B (Paragraph: max 800)**     | **TEST** | **4/5 (80.00%)** | **4/5 (80.00%)** | **349** | **7.66s** | **$0** |
| **C (Paragraph + Filter)**     | **DEV**  | 8/15 (53.33%) | 13/15 (86.67%) | 349 | 0.00s *(dùng lại B)* | $0 |
| **C (Paragraph + Filter)**     | **TEST** | **4/5 (80.00%)** | **4/5 (80.00%)** | **349** | **0.00s** *(dùng lại B)* | **$0** |

---

### 3.2. Bảng 2: Đánh giá Chất lượng Ngữ cảnh và Metadata (Quality & Audit)

| Strategy | Coherence trung bình /2 (n=10) | Metadata đủ và đúng (n=15) | Filter tuân thủ (n=5) | Grounding 0/1/2 (Test n=5) | Grounding trung bình /2 |
|---|:---:|:---:|:---:|:---:|:---:|
| **A (Fixed-size)** | **0.10 / 2.0** (1/10 điểm 1, 9/10 điểm 0) | 15/15 (100%) | N/A | [0, 1, 4] | **1.80 / 2.0** |
| **B (Paragraph)**  | **2.00 / 2.0** (10/10 điểm 2) | 15/15 (100%) | N/A | [0, 0, 5] | **2.00 / 2.0** |
| **C (Para + Filt)**| **2.00 / 2.0** (10/10 điểm 2) | 15/15 (100%) | **5/5 (100%)** | [0, 0, 5] | **2.00 / 2.0** |

*Đường dẫn dữ liệu kiểm chứng:*
- Trace chi tiết từng lượt truy xuất: [results/retrieval_traces.json](/starter/results/retrieval_traces.json)
- Bảng tổng hợp chỉ số: [results/metrics_summary.json](/starter/results/metrics_summary.json)

---

### 3.3. Bảng 3: Chi tiết Chấm thủ công Chunk Coherence trên 10 Vị trí Nguồn
*Thang điểm: 0 = Bị cắt giữa ý/cụt từ không hiểu được; 1 = Hiểu một phần nhưng thiếu ngữ cảnh; 2 = Giữ trọn vẹn câu và ý tứ tự hiểu được.*

| Vị trí mẫu | Điểm Cấu hình A | Lý do Cấu hình A | Điểm Cấu hình B/C | Lý do Cấu hình B/C |
|:---:|:---:|---|:---:|---|
| **Trang 23** | 0 | Cắt cụt từ cuối: `interconnectedness of th` | 2 | Kết thúc trọn vẹn câu: `...riches of the East.` |
| **Trang 24** | 0 | Cắt cụt từ cuối: `always called t` | 2 | Trọn câu hoàn chỉnh: `...in search of food.` |
| **Trang 25** | 0 | Cắt cụt từ cuối: `diversity, this region cr` | 2 | Trọn câu hoàn chỉnh: `...basis of their diet.` |
| **Trang 26** | 1 | Cắt ngang mệnh đề câu: `...100,000 people` | 2 | Kết thúc trọn vẹn câu: `...a multiethnic city.` |
| **Trang 27** | 0 | Cắt cụt từ cuối: `pictures representi` | 2 | Trọn câu hoàn chỉnh: `...a few survive.` |
| **Trang 28** | 0 | Cắt cụt từ cuối: `Unlike the Spanish, Azte` | 2 | Trọn câu hoàn chỉnh: `...to the mainland.` |
| **Trang 29** | 0 | Cắt ngang hội thoại: `Said Quzatli to the sov` | 2 | Trọn câu hoàn chỉnh: `...ruler of the Aztecs.` |
| **Trang 30** | 0 | Cắt ngang danh từ: `labor of the peasant` | 2 | Trọn câu hoàn chỉnh: `...steep mountains.` |
| **Trang 31** | 0 | Cắt cụt từ cuối: `societies, and did n` | 2 | Trọn câu hoàn chỉnh: `...huge herds of bison.` |
| **Trang 32** | 0 | Cắt ngang liên từ: `A century later, however,` | 2 | Trọn câu hoàn chỉnh: `...Hopi and Zuni tribes.` |
| **Trung bình** | **0.10 / 2.0** | *90% bị gãy từ hoặc cắt cụt giữa câu* | **2.00 / 2.0** | *100% giữ nguyên cấu trúc đoạn văn ngữ nghĩa* |

---

### 3.4. Bảng 4: Chi tiết Chấm thủ công Grounding Quality trên 5 Câu Test
*Thang điểm: 0 = Không có bằng chứng; 1 = Có bằng chứng nhưng phân mảnh/thiếu điều kiện; 2 = Đầy đủ bằng chứng và ngữ cảnh để trả lời và đối chiếu nguồn.*

| Câu hỏi | Gold Page | Điểm A | Phân tích Grounding Cấu hình A | Điểm B/C | Phân tích Grounding Cấu hình B/C |
|:---:|:---:|:---:|---|:---:|---|
| **q16** | 61 | 1 | Rank 3 rơi vào trang 61 nhưng chunk bị cắt đứt giữa câu, chỉ chứa một phần ý thảo ước Mayflower Compact. | 2 | Rank 1 trả về trang 88 giải thích tường tận mục đích Mayflower Compact; Rank 3 trang 61 đầy đủ văn cảnh văn bản 1620. |
| **q17** | 90 | 2 | Rank 1 rơi đúng trang 90, chứa đủ bằng chứng trục xuất Roger Williams và Anne Hutchinson. | 2 | Rank 1 rơi đúng trang 90, trọn vẹn đoạn văn về sự bất đồng chính kiến và việc bị trục xuất khỏi Massachusetts Bay. |
| **q18** | 91 | 2 | Rank 2 chứa bằng chứng Metacom ngăn chặn người Anh lấn chiếm đất đai. | 2 | Rank 1 đạt độ tương đồng 0.7299, giải thích đầy đủ áp lực đất đai và nguồn cơn bùng nổ chiến tranh King Philip. |
| **q19** | 95 | 2 | Rank 1 chứa bằng chứng bệnh đậu mùa tàn phá các bộ lạc Huron và Iroquois quanh Ngũ Đại Hồ. | 2 | Rank 1 chứa nguyên vẹn đoạn văn về dịch bệnh đậu mùa và tỷ lệ tử vong cao ở người già và trẻ nhỏ. |
| **q20** | 76 | 2 | Rank 1 chứa bằng chứng cuộc khởi nghĩa Pueblo 1680 tiêu diệt hơn 400 lính Tây Ban Nha. | 2 | Rank 1 chứa trọn vẹn diễn biến cuộc nổi dậy Pueblo và việc đẩy lùi 2.000 thực dân về Mexico. |
| **Trung bình** | - | **1.80** | *1 câu bị phân mảnh thông tin* | **2.00** | *100% câu test có bằng chứng đầy đủ, toàn vẹn* |

---

## 4. Phân tích Chuyên sâu và Kết luận

### 4.1. So sánh Chiến lược A (Fixed-size) và B (Paragraph Chunking)
- **Về độ chính xác truy xuất (Retrieval Accuracy)**:
  - Trên tập Dev, Cấu hình A đạt Hit@1 cao hơn (73.33% so với 53.33%) vì các chunk nhỏ (500 ký tự) có mật độ từ khóa đậm đặc hơn.
  - Tuy nhiên, **trên tập Test**, Cấu hình B vượt trội hoàn toàn với **Hit@1 đạt 80.00%** (so với 60.00% của A), và cả hai đều đạt **Evidence Hit@3 là 80.00%**.
- **Về tính mạch lạc ngữ nghĩa (Chunk Coherence)**:
  - Đây là điểm khác biệt mang tính quyết định: Cấu hình A đạt điểm cực thấp (**0.10 / 2.0**) do thuật toán cắt theo số ký tự cứng nhắc đã cắt đôi các từ vựng (`th`, `always called t`, `representi`, `Azte`), khiến chunk mất đi tính tự hiểu nếu đưa vào làm ngữ cảnh cho LLM.
  - Ngược lại, Cấu hình B đạt điểm tuyệt đối **2.00 / 2.0**, mọi chunk đều bảo toàn ranh giới câu và đoạn văn hoàn chỉnh.
- **Về tài nguyên và hiệu năng**:
  - Cấu hình B chỉ sinh ra **349 chunks** so với **539 chunks** của A, giúp **tiết kiệm 35.3% chi phí lưu trữ vector**.
  - Thời gian nạp dữ liệu (Ingest) của B chỉ mất **7.66s**, nhanh gấp hơn 2 lần so với A (**16.58s**).

### 4.2. So sánh Chiến lược B (Paragraph) và C (Paragraph + Filter)
- Cấu hình C tái sử dụng toàn bộ 349 chunks của B nên chi phí và thời gian ingest là **0 giây**.
- Cả 5 câu hỏi có bộ lọc metadata đều đạt **tỷ lệ tuân thủ bộ lọc 100%** (toàn bộ top-3 hits trả về đều thuộc đúng chương được chỉ định).
- Việc lọc theo metadata triệt tiêu hoàn toàn nguy cơ lấy nhầm các sự kiện tương đồng diễn ra ở các thế kỷ hoặc chương khác, bảo vệ tính đúng đắn cho các bài toán phân vùng dữ liệu lớn.

### 4.3. Phân tích 2 trường hợp lỗi tiêu biểu
1. **Lỗi ở câu `q16` (Test - Mayflower Compact, Gold Page 61)**:
   - *Hiện tượng*: Cả 3 cấu hình đều xếp các chunk ở trang 88 lên Rank 1 và Rank 2, trong khi trang gold ban đầu đặt ở trang 61.
   - *Nguyên nhân*: Trong sách *U.S. History*, trang 61 chỉ giới thiệu ngắn gọn sự kiện ký kết Mayflower Compact năm 1620, trong khi trang 88 có hẳn một đề mục phân tích sâu mang tên *"The Mayflower Compact and Its Religious Rationale"*. Do câu hỏi hỏi về *"fundamental governance agreement"*, mô hình embedding tìm thấy độ tương đồng ngữ nghĩa cao hơn ở trang 88.
   - *Bài học*: Cần hỗ trợ khái niệm **multi-gold sources** khi cùng một chủ đề lịch sử được đào sâu ở các chương sau của sách.
2. **Lỗi ở câu `q04` (Dev - Soninke farmers, Gold Page 40)**:
   - *Hiện tượng*: Cấu hình A tìm thấy bằng chứng ở Rank 1, nhưng Cấu hình B và C lại không đưa bằng chứng vào top-3.
   - *Nguyên nhân*: Trang 40 có dung lượng văn bản lớn bàn về sự lan tỏa của đạo Hồi và đế quốc Ghana. Khi gom thành đoạn văn 800 ký tự ở Cấu hình B, thông tin về *"Soninke farmers taxing trade"* bị pha loãng bởi các câu văn dài xung quanh bàn về cấu trúc chính trị Hồi giáo, làm vector đoạn văn bị kéo lệch khỏi câu hỏi ngắn mang tính tập trung vào thuế.
   - *Bài học*: Các đoạn văn dài có chứa nhiều tiểu tiết nên áp dụng kỹ thuật **Small-to-Big Retrieval** (lưu vector chunk câu ngắn nhưng khi trả về LLM thì trả đoạn văn cha) hoặc **Sentence-Window Retrieval**.

---

### 4.4. Kết luận Lựa chọn Chiến lược
> [!IMPORTANT]
> **Chiến lược được lựa chọn là Cấu hình C (Paragraph Chunking kết hợp Metadata Filter)** (hoặc Cấu hình B cho các truy vấn không có filter).

**Lý do lựa chọn**:
1. Đạt hiệu năng truy xuất kiểm định trên tập Test cao nhất (**Hit@1 = 80.00%, Hit@3 = 80.00%**).
2. Tính toàn vẹn ngữ nghĩa tuyệt đối (**Coherence = 2.0/2.0**, **Grounding = 2.0/2.0**), hoàn toàn triệt tiêu hiện tượng gãy từ, cụt câu của Cấu hình A.
3. Tiết kiệm hơn **35% dung lượng lưu trữ vector** và giảm thời gian ingestion xuống hơn 50%.
4. Đảm bảo tuân thủ tuyệt đối 100% phạm vi nghiệp vụ khi truy vấn có điều kiện lọc metadata.

---

### 4.5. Đánh giá Hạn chế và Hướng cải tiến
- **Hạn chế**:
  - Kích thước tập Test gồm 5 câu là mức mẫu nhỏ phục vụ khuôn khổ bài thực hành, chưa phản ánh hết mọi phân phối truy vấn thực tế.
  - Tìm kiếm vector thuần túy (Dense Retrieval) đôi khi gặp khó khăn với các từ khóa tên riêng hiếm hoặc số liệu cụ thể nếu câu hỏi diễn đạt quá ngắn.
- **Đề xuất cải tiến tương lai**:
  - **Hybrid Retrieval (Dense + BM25)**: Kết hợp tìm kiếm vector ngữ nghĩa với tìm kiếm từ khóa BM25 để vừa nắm bắt ý nghĩa trừu tượng vừa giữ được các tên riêng như *Croatoan*, *Soninke*, *Quipu*.
  - **Cross-Encoder Reranking**: Sử dụng mô hình Cohere Rerank hoặc BGE-Reranker để tái sắp xếp top-10 ứng viên thành top-3 có độ khớp ngữ cảnh chính xác nhất.
  - **Hierarchical / Parent-Child Chunking**: Tạo embedding cho các câu nhỏ (200 ký tự) để tăng độ nhạy tìm kiếm, nhưng truy xuất toàn bộ đoạn văn cha (800 ký tự) để đảm bảo ngữ cảnh cho LLM.
