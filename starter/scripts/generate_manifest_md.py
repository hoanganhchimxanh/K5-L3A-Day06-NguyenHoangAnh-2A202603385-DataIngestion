import json

with open('data/manifest.json', 'r', encoding='utf-8') as f:
    m = json.load(f)

md_lines = []
md_lines.append('# Data Manifest — Corpus U.S. History')
md_lines.append('')
md_lines.append('Manifest mô tả chi tiết nguồn dữ liệu, phạm vi tuyển chọn trang, tính toán số lượng ký tự và giấy phép sử dụng theo yêu cầu của [GUIDE.md](../GUIDE.md).')
md_lines.append('')
md_lines.append('## 1. Thông tin nguồn tài liệu (Source Metadata)')
md_lines.append('')
md_lines.append(f"- **Source ID**: `{m['source_id']}`")
md_lines.append(f"- **Tác phẩm**: {m['title']}")
md_lines.append(f"- **Nhà xuất bản**: {m['publisher']}")
md_lines.append(f"- **Tác giả**: {', '.join(m['authors'])}")
md_lines.append(f"- **Nguồn truy cập**: [{m['source_path_or_url']}]({m['source_path_or_url']})")
md_lines.append(f"- **Tệp tin cục bộ**: `{m['local_file']}`")
md_lines.append(f"- **Giấy phép bản quyền**: {m['license_or_permission']}")
md_lines.append(f"- **Phiên bản snapshot**: {m['snapshot_version']}")
md_lines.append(f"- **Ngày truy cập / khai thác**: {m['created_at']}")
md_lines.append('')
md_lines.append('## 2. Quy tắc lọc trang và Thống kê khối lượng (Page Selection & Statistics)')
md_lines.append('')
r = m['page_selection_rule']
md_lines.append(f"- **Tổng số trang vật lý của file PDF**: {r['total_physical_pages_in_pdf']} trang.")
md_lines.append(f"- **Các trang bị loại bỏ (trang thừa)**: Trang vật lý `{r['excluded_initial_pages']}` (gồm bìa, bản quyền, mục lục TOC và lời tựa Preface).")
md_lines.append(f"- **Phạm vi trang được chọn**: Trang vật lý `{r['selected_physical_page_range']}` (tương đương trang in trong sách `{r['selected_book_page_range']}`).")
md_lines.append(f"- **Tổng số trang đưa vào Ingestion**: **{r['total_selected_pages']} trang** (vượt xa yêu cầu tối thiểu 30 trang).")
md_lines.append(f"  - Số trang bài học cốt lõi: **{r['core_content_pages_count']} trang**.")
md_lines.append(f"  - Số trang câu hỏi ôn tập / Critical Thinking: **{r['review_question_pages_count']} trang** (các trang 45, 46, 70, 71, 72, 99, 100).")
md_lines.append(f"- **Tổng số ký tự đã trích xuất**: **{r['total_characters']:,} ký tự**.")
md_lines.append(f"- **Tổng số từ**: **{r['total_words']:,} từ**.")
md_lines.append(f"- **Trung bình ký tự/trang**: **{r['avg_characters_per_page']} ký tự/trang**.")
md_lines.append('')
md_lines.append('## 3. Tóm tắt các chương trong phạm vi tuyển chọn')
md_lines.append('')
md_lines.append('| Chương | Trang vật lý | Trang in | Các phần chính |')
md_lines.append('|---|---|---|---|')
for ch in m['chapters_summary']:
    secs = '<br>'.join(ch['sections'])
    md_lines.append(f"| **{ch['chapter']}** | {ch['physical_pages']} | {ch['book_pages']} | {secs} |")
md_lines.append('')
md_lines.append('## 4. Bảng mẫu 10 trang đầu trong tập dữ liệu')
md_lines.append('')
md_lines.append('| Page ID | Physical Page | Book Page | Chương | Mục / Phần | Số ký tự | Trích dẫn mở đầu |')
md_lines.append('|---|---|---|---|---|---|---|')
for p in m['pages'][:10]:
    ch_short = p['chapter'].split(':')[0]
    md_lines.append(f"| `{p['page_id']}` | {p['physical_page']} | {p['book_page']} | {ch_short} | {p['section']} | {p['char_count']} | {p['snippet']}... |")
md_lines.append('')
md_lines.append('*(Chi tiết danh sách toàn bộ 78 trang xem tại [data/manifest.json](manifest.json))*')

with open('data/manifest.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(md_lines))

with open('starter/data/manifest.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(md_lines))

print('Done writing markdown manifest.')

