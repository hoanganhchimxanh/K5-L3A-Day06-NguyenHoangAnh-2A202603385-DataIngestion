# Data Manifest — Corpus U.S. History

Manifest mô tả chi tiết nguồn dữ liệu, phạm vi tuyển chọn trang, tính toán số lượng ký tự và giấy phép sử dụng theo yêu cầu của [GUIDE.md](../GUIDE.md).

## 1. Thông tin nguồn tài liệu (Source Metadata)

- **Source ID**: `openstax-us-history`
- **Tác phẩm**: U.S. History
- **Nhà xuất bản**: OpenStax, Rice University
- **Tác giả**: P. Scott Corbett, Volker Janssen, John M. Lund, Todd Pfannestiel, Paul Vickery, Sylvie Waskiewicz
- **Nguồn truy cập**: [https://openstax.org/details/books/us-history](https://openstax.org/details/books/us-history)
- **Tệp tin cục bộ**: `starter/data/US_History_-_WEB.pdf`
- **Giấy phép bản quyền**: Creative Commons Attribution Non-Commercial ShareAlike 4.0 International License (CC BY-NC-SA 4.0)
- **Phiên bản snapshot**: 2026 Web Edition (Producer Prince 16.2)
- **Ngày truy cập / khai thác**: 2026-11-13

## 2. Quy tắc lọc trang và Thống kê khối lượng (Page Selection & Statistics)

- **Tổng số trang vật lý của file PDF**: 987 trang.
- **Các trang bị loại bỏ (trang thừa)**: Trang vật lý `1-22 (Cover, Copyright, Table of Contents, Preface)` (gồm bìa, bản quyền, mục lục TOC và lời tựa Preface).
- **Phạm vi trang được chọn**: Trang vật lý `23-100` (tương đương trang in trong sách `7-84`).
- **Tổng số trang đưa vào Ingestion**: **78 trang** (vượt xa yêu cầu tối thiểu 30 trang).
  - Số trang bài học cốt lõi: **71 trang**.
  - Số trang câu hỏi ôn tập / Critical Thinking: **7 trang** (các trang 45, 46, 70, 71, 72, 99, 100).
- **Tổng số ký tự đã trích xuất**: **231,021 ký tự**.
- **Tổng số từ**: **36,542 từ**.
- **Trung bình ký tự/trang**: **2961.8 ký tự/trang**.

## 3. Tóm tắt các chương trong phạm vi tuyển chọn

| Chương | Trang vật lý | Trang in | Các phần chính |
|---|---|---|---|
| **Chapter 1: The Americas, Europe, and Africa Before 1492** | 23-46 | 7-30 | 1.1 The Americas<br>1.2 Europe on the Brink of Change<br>1.3 West Africa and the Role of Slavery<br>Review & Critical Thinking |
| **Chapter 2: Early Globalization: The Atlantic World, 1492-1650** | 47-72 | 31-56 | 2.1 Portuguese Exploration and Spanish Conquest<br>2.2 Religious Upheavals in the Developing Atlantic World<br>2.3 Challenges to Spain’s Supremacy<br>2.4 New Worlds in the Americas: Labor, Commerce, and the Columbian Exchange<br>Review & Critical Thinking |
| **Chapter 3: Creating New Social Orders: Colonial Societies, 1500-1700** | 73-100 | 57-84 | 3.1 Spanish Exploration and Colonial Society<br>3.2 Colonial Rivalries: Dutch and French Colonial Ambitions<br>3.3 English Settlements in America<br>3.4 The Impact of Colonization<br>Review & Critical Thinking |

## 4. Bảng mẫu 10 trang đầu trong tập dữ liệu

| Page ID | Physical Page | Book Page | Chương | Mục / Phần | Số ký tự | Trích dẫn mở đầu |
|---|---|---|---|---|---|---|
| `page_023` | 23 | 7 | Chapter 1 | Chapter Introduction | 1781 | FIGURE 1.1 This 1507 map by cartographers Martin Waldseemüller and Matthais Ringmann is credited as ... |
| `page_024` | 24 | 8 | Chapter 1 | 1.1 The Americas | 2051 | 1.1 The Americas ... |
| `page_025` | 25 | 9 | Chapter 1 | 1.1 The Americas | 2623 | FIGURE 1.3 This map shows the extent of the major civilizations of the Western Hemisphere. In South ... |
| `page_026` | 26 | 10 | Chapter 1 | 1.1 The Americas | 2314 | FIGURE 1.4 The Olmec carved heads from giant boulders that ranged from four to eleven feet in height... |
| `page_027` | 27 | 11 | Chapter 1 | 1.1 The Americas | 2511 | FIGURE 1.5 El Castillo, located at Chichen Itza in the eastern Yucatán peninsula, served as a temple... |
| `page_028` | 28 | 12 | Chapter 1 | 1.1 The Americas | 1865 | FIGURE 1.6 This rendering of the Aztec island city of Tenochtitlán depicts the causeways that connec... |
| `page_029` | 29 | 13 | Chapter 1 | 1.1 The Americas | 3069 | CLICK AND EXPL ORE ... |
| `page_030` | 30 | 14 | Chapter 1 | 1.1 The Americas | 2648 | FIGURE 1.8 The Inca had no written language. Instead, they communicated and kept records by means of... |
| `page_031` | 31 | 15 | Chapter 1 | 1.1 The Americas | 2269 | FIGURE 1.9 Located in today’s Peru at an altitude of nearly 8,000 feet, Machu Picchu was a ceremonia... |
| `page_032` | 32 | 16 | Chapter 1 | 1.1 The Americas | 3529 | FIGURE 1.10 To access their homes, the cliff-dwelling Anasazi used ropes or ladders that could be pu... |

*(Chi tiết danh sách toàn bộ 78 trang xem tại [data/manifest.json](manifest.json))*