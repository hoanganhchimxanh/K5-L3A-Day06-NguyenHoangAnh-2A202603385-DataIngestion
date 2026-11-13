import json
import os
import pypdf

# 20 Benchmark questions with verified evidence quotes
questions = [
    # ------------------ DEV SPLIT (15 questions: q01 - q15) ------------------
    {
        "id": "q01",
        "type": "truc_tiep",
        "split": "dev",
        "question": "How did the Inca communicate and keep records without a written language?",
        "question_vi": "Người Inca đã giao tiếp và lưu giữ ghi chép như thế nào khi không có chữ viết?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 30,
        "gold_chapter": "Chapter 1",
        "evidence_quote": "The Inca had no written language. Instead, they communicated and kept records by means of a system of knots and colored strings called the quipu.",
        "expected_answer": "They communicated and kept records using a system of knots and colored strings called the quipu.",
        "filter": None
    },
    {
        "id": "q02",
        "type": "truc_tiep",
        "split": "dev",
        "question": "What was the estimated population of the city of Cahokia at its peak around 1100 CE?",
        "question_vi": "Dân số ước tính của thành phố Cahokia vào thời kỳ hoàng kim khoảng năm 1100 CN là bao nhiêu?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 32,
        "gold_chapter": "Chapter 1",
        "evidence_quote": "this five-square-mile city, now called Cahokia, was home to more than ten thousand residents; tens of thousands more lived on farms surrounding the urban center.",
        "expected_answer": "More than ten thousand residents lived in the city, with tens of thousands more on surrounding farms.",
        "filter": None
    },
    {
        "id": "q03",
        "type": "dien_dat_lai",
        "split": "dev",
        "question": "What catastrophic pandemic devastated the European population in the fourteenth century, wiping out entire villages?",
        "question_vi": "Đại dịch thảm khốc nào đã tàn phá dân số châu Âu vào thế kỷ 14 làm biến mất toàn bộ các ngôi làng?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 34,
        "gold_chapter": "Chapter 1",
        "evidence_quote": "Together these two are collectively called the Black Death (Figure 1.12). Entire villages disappeared.",
        "expected_answer": "The Black Death (bubonic and pneumonic plague).",
        "filter": None
    },
    {
        "id": "q04",
        "type": "truc_tiep",
        "split": "dev",
        "question": "How did the Soninke farmers of the sub-Sahara Ghana Empire generate their wealth by 750 CE?",
        "question_vi": "Những người nông dân Soninke thuộc Đế quốc Ghana vùng hạ Sahara đã tạo ra sự giàu có như thế nào vào năm 750 CN?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 40,
        "gold_chapter": "Chapter 1",
        "evidence_quote": "By 750, the Soninke farmers of the sub-Sahara had become wealthy by taxing the trade that passed through their area.",
        "expected_answer": "By taxing the commercial trade that passed through their territory.",
        "filter": {"chapter": "Chapter 1"}
    },
    {
        "id": "q05",
        "type": "dieu_kien_ngoai_le",
        "split": "dev",
        "question": "What alternative labor policy did Bartolomé de Las Casas advocate to prevent the extinction of the native population in the West Indies?",
        "question_vi": "Bartolomé de Las Casas đã đề xuất chính sách lao động thay thế nào nhằm ngăn chặn nguy cơ diệt chủng người bản địa ở Tây Ấn?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 42,
        "gold_chapter": "Chapter 1",
        "evidence_quote": "seeing the near extinction of the native population, suggested the Spanish send Black (and White) laborers to the Indies.",
        "expected_answer": "He suggested the Spanish import Black (and White) laborers to the Indies to spare the native population.",
        "filter": None
    },
    {
        "id": "q06",
        "type": "truc_tiep",
        "split": "dev",
        "question": "How did the 1494 Treaty of Tordesillas divide newly discovered overseas territories between Spain and Portugal?",
        "question_vi": "Hiệp ước Tordesillas năm 1494 đã phân chia các vùng đất hải ngoại mới phát hiện giữa Tây Ban Nha và Bồ Đào Nha như thế nào?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 52,
        "gold_chapter": "Chapter 2",
        "evidence_quote": "Spain gained territory west of the line, while Portugal retained the lands east of the line, including the east coast of Brazil.",
        "expected_answer": "Spain gained lands west of the meridian line, while Portugal retained lands east of the line (including the east coast of Brazil).",
        "filter": None
    },
    {
        "id": "q07",
        "type": "truc_tiep",
        "split": "dev",
        "question": "What rewards and concessions did Hernán Cortés seek from the Spanish monarch in exchange for his military conquests in the New World?",
        "question_vi": "Hernán Cortés tìm kiếm những phần thưởng và đặc quyền gì từ hoàng gia Tây Ban Nha để đổi lấy các cuộc chinh phục ở Tân thế giới?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 52,
        "gold_chapter": "Chapter 2",
        "evidence_quote": "Hernán Cortés hoped to gain hereditary privilege for his family, tribute payments and labor from natives, and an annual pension for his service to the crown.",
        "expected_answer": "Hereditary privileges for his family, tribute payments, forced native labor, and an annual royal pension.",
        "filter": None
    },
    {
        "id": "q08",
        "type": "dien_dat_lai",
        "split": "dev",
        "question": "Which religious figure sparked the Protestant Reformation in sixteenth-century Europe?",
        "question_vi": "Nhân vật tôn giáo nào đã khởi xướng Phong trào Cải cách Kháng cách ở châu Âu vào thế kỷ 16?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 56,
        "gold_chapter": "Chapter 2",
        "evidence_quote": "Martin Luther, a German Catholic monk and leader of the Protestant Reformation, was a close friend of the German painter Lucas Cranach the Elder.",
        "expected_answer": "Martin Luther, a German Catholic monk.",
        "filter": {"chapter": "Chapter 2"}
    },
    {
        "id": "q09",
        "type": "dieu_kien_ngoai_le",
        "split": "dev",
        "question": "What mysterious clue was discovered at the abandoned English settlement of Roanoke when Governor White returned in 1590?",
        "question_vi": "Manh mối bí ẩn duy nhất nào được phát hiện tại khu định cư Roanoke bị bỏ hoang khi Thống đốc White quay lại vào năm 1590?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 59,
        "gold_chapter": "Chapter 2",
        "evidence_quote": "The only trace the colonists left behind was the word Croatoan carved into a fence surrounding the village.",
        "expected_answer": "The word 'Croatoan' carved into a wooden fence post surrounding the settlement village.",
        "filter": None
    },
    {
        "id": "q10",
        "type": "truc_tiep",
        "split": "dev",
        "question": "What legal rights were conferred upon Spanish conquistadors under the encomienda grant system?",
        "question_vi": "Chế độ ủy thác encomienda đã trao quyền pháp lý gì cho các conquistador Tây Ban Nha?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 64,
        "gold_chapter": "Chapter 2",
        "evidence_quote": "Spain granted encomiendas—legal rights to native labor—to conquistadors who could prove their service to the crown.",
        "expected_answer": "Legal rights to compel and exploit native labor.",
        "filter": None
    },
    {
        "id": "q11",
        "type": "dien_dat_lai",
        "split": "dev",
        "question": "How did early transatlantic voyages alter the ecosystems of both the Americas and the Old World?",
        "question_vi": "Các chuyến hải hành xuyên Đại Tây Dương ban đầu đã làm biến đổi hệ sinh thái của cả châu Mỹ lẫn Cựu thế giới như thế nào?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 66,
        "gold_chapter": "Chapter 2",
        "evidence_quote": "As Europeans traversed the Atlantic, they brought with them plants, animals, and diseases that changed lives and landscapes on both sides of the ocean.",
        "expected_answer": "Through the Columbian Exchange, which transferred plants, domestic animals, and infectious diseases across both continents.",
        "filter": None
    },
    {
        "id": "q12",
        "type": "truc_tiep",
        "split": "dev",
        "question": "What is recognized as the oldest continuously inhabited European city in North America, established in 1565?",
        "question_vi": "Khu định cư châu Âu có người sinh sống liên tục lâu đời nhất ở Bắc Mỹ được thành lập năm 1565 là nơi nào?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 75,
        "gold_chapter": "Chapter 3",
        "evidence_quote": "In 1565, the victorious Menéndez founded St. Augustine, now the oldest European settlement in the Americas.",
        "expected_answer": "St. Augustine in Florida, founded by Pedro Menéndez de Avilés.",
        "filter": None
    },
    {
        "id": "q13",
        "type": "dieu_kien_ngoai_le",
        "split": "dev",
        "question": "What privileges and corresponding conditions were defined under Dutch patroonships in New Netherland?",
        "question_vi": "Chế độ patroonship của Công ty Tây Ấn Hà Lan tại New Netherland mang lại đặc quyền và điều kiện gì?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 78,
        "gold_chapter": "Chapter 3",
        "evidence_quote": "it granted Dutch merchants who invested heavily in it patroonships, or large tracts of land and the right to govern the tenants there.",
        "expected_answer": "Heavy investors were granted large tracts of land and tenant governance rights in exchange for transporting Dutch farmers to colonize the area.",
        "filter": None
    },
    {
        "id": "q14",
        "type": "dien_dat_lai",
        "split": "dev",
        "question": "What agricultural commodity formed the backbone of the economy in colonial Virginia and Maryland?",
        "question_vi": "Nông sản thương phẩm nào là trụ cột cứu sống nền kinh tế thuộc địa của người Anh tại Virginia và Maryland?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 81,
        "gold_chapter": "Chapter 3",
        "evidence_quote": "growing tobacco was the only sure means of making money.",
        "expected_answer": "Tobacco cultivation.",
        "filter": None
    },
    {
        "id": "q15",
        "type": "truc_tiep",
        "split": "dev",
        "question": "How did the headright policy operated by the Virginia Company incentivize transatlantic migration?",
        "question_vi": "Chính sách headright của Công ty Virginia đã khuyến khích người nhập cư sang Tân thế giới bằng cách nào?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 84,
        "gold_chapter": "Chapter 3",
        "evidence_quote": "those who paid their own passage to Virginia received fifty acres plus an additional fifty for each servant or family member they brought with them.",
        "expected_answer": "Settlers paying their own transportation were granted 50 acres of land, plus an extra 50 acres for each family member or servant brought.",
        "filter": None
    },

    # ------------------ TEST SPLIT (5 questions: q16 - q20) ------------------
    {
        "id": "q16",
        "type": "truc_tiep",
        "split": "test",
        "question": "What fundamental governance agreement did the English Pilgrims draft and sign aboard ship in 1620?",
        "question_vi": "Bản thỏa ước quản trị cơ bản nào đã được những người hành hương ký kết trên tàu vào năm 1620?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 61,
        "gold_chapter": "Chapter 2",
        "evidence_quote": "Their story includes the signing of the Mayflower Compact, a written agreement whereby the English voluntarily agreed to help each other.",
        "expected_answer": "The Mayflower Compact, a voluntary written covenant to bind settlers to mutual cooperation and governance.",
        "filter": None
    },
    {
        "id": "q17",
        "type": "dien_dat_lai",
        "split": "test",
        "question": "Which outspoken religious figures were expelled from the Massachusetts Bay colony during the 1630s for defying Puritan orthodoxy?",
        "question_vi": "Những nhân vật tôn giáo nào đã bị trục xuất khỏi thuộc địa Massachusetts Bay vào thập niên 1630 vì dám thách thức chính quyền Thanh giáo?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 90,
        "gold_chapter": "Chapter 3",
        "evidence_quote": "Puritan minister Roger Williams and Anne Hutchinson, challenged Governor Winthrop in Massachusetts Bay in the 1630s, they were banished.",
        "expected_answer": "Roger Williams and Anne Hutchinson were banished by Governor Winthrop and the Puritan leadership.",
        "filter": {"chapter": "Chapter 3"}
    },
    {
        "id": "q18",
        "type": "dieu_kien_ngoai_le",
        "split": "test",
        "question": "What fundamental grievance drove Wampanoag leader Metacom to launch King Philip's War against New England settlements in 1675?",
        "question_vi": "Bất bình sâu sắc nào đã thúc đẩy thủ lĩnh Wampanoag Metacom khơi mào cuộc chiến King Philip's War chống lại các khu định cư New England năm 1675?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 91,
        "gold_chapter": "Chapter 3",
        "evidence_quote": "Wampanoag leader Metacom or Metacomet, also known as King Philip among the English, was determined to stop the encroachment.",
        "expected_answer": "A determination to halt relentless English land encroachment and colonial domination over Native lands.",
        "filter": {"chapter": "Chapter 3"}
    },
    {
        "id": "q19",
        "type": "dien_dat_lai",
        "split": "test",
        "question": "Which epidemic disease caused massive casualties among indigenous peoples such as the Huron and Iroquois around the Great Lakes?",
        "question_vi": "Dịch bệnh nào đã gây thương vong nghiêm trọng nhất cho các bộ tộc bản địa như Huron và Iroquois quanh vùng Ngũ Đại Hồ?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 95,
        "gold_chapter": "Chapter 3",
        "evidence_quote": "Huron and Iroquois around the Great Lakes died of smallpox. As is often the case with disease, the very young and the very old were the most vulnerable and had the highest mortality rates.",
        "expected_answer": "Smallpox, which hit infants, children, and elderly tribal members with severe mortality.",
        "filter": None
    },
    {
        "id": "q20",
        "type": "dieu_kien_ngoai_le",
        "split": "test",
        "question": "What were the immediate military outcomes of the 1680 Pueblo Revolt against Spanish colonization in New Mexico?",
        "question_vi": "Hậu quả quân sự trực tiếp của cuộc nổi dậy Pueblo năm 1680 đối với thực dân Tây Ban Nha tại New Mexico là gì?",
        "gold_source_id": "openstax-us-history",
        "gold_page": 76,
        "gold_chapter": "Chapter 3",
        "evidence_quote": "The Pueblo Revolt killed over four hundred Spaniards and drove the rest of the settlers, perhaps as many as two thousand, south toward Mexico.",
        "expected_answer": "Over 400 Spaniards were killed, and approximately 2,000 surviving colonists were driven south toward Mexico.",
        "filter": {"chapter": "Chapter 3"}
    }
]

# Verify against PDF
reader = pypdf.PdfReader('starter/data/US_History_-_WEB.pdf')
print("Verifying 20 questions against PDF...")
for q in questions:
    p_num = q['gold_page']
    raw_text = reader.pages[p_num-1].extract_text()
    norm_text = ' '.join(raw_text.split())
    norm_quote = ' '.join(q['evidence_quote'].split())
    assert norm_quote in norm_text, f"Mismatch in {q['id']} on page {p_num}!"
print("All 20 evidence quotes verified successfully against PDF!")

# Prepare directories
os.makedirs('benchmark', exist_ok=True)
os.makedirs('starter/benchmark', exist_ok=True)
os.makedirs('starter/data', exist_ok=True)

# Save JSON
benchmark_data = {
    "benchmark_version": "1.0.0",
    "created_at": "2026-11-13",
    "source_id": "openstax-us-history",
    "total_questions": len(questions),
    "dev_count": len([q for q in questions if q['split'] == 'dev']),
    "test_count": len([q for q in questions if q['split'] == 'test']),
    "filter_questions_count": len([q for q in questions if q['filter'] is not None]),
    "questions": questions
}

with open('benchmark/questions.json', 'w', encoding='utf-8') as f:
    json.dump(benchmark_data, f, indent=2, ensure_ascii=False)

with open('starter/benchmark/questions.json', 'w', encoding='utf-8') as f:
    json.dump(benchmark_data, f, indent=2, ensure_ascii=False)

# Also save questions.md
md_lines = []
md_lines.append("# Benchmark Questions — Corpus U.S. History")
md_lines.append("")
md_lines.append("Bộ câu hỏi benchmark được biên soạn theo đúng quy chuẩn của [BENCHMARK.md](../BENCHMARK.md) và [GUIDE.md](../GUIDE.md).")
md_lines.append("")
md_lines.append(f"- **Tổng số câu hỏi**: {len(questions)} câu.")
md_lines.append(f"- **Phân chia split**: **15 câu Dev** (`q01`–`q15`) và **5 câu Test** (`q16`–`q20`).")
md_lines.append(f"- **Câu hỏi kiểm tra Metadata Filter**: 4 câu (`q04`, `q08` thuộc Dev; `q17`, `q18`, `q20` thuộc Test).")
md_lines.append("- **Kiểm chứng bằng chứng (Evidence Verification)**: 100% các đoạn `evidence_quote` đều được đối soát chính xác từng ký tự trong văn bản gốc.")
md_lines.append("")
md_lines.append("## Danh sách 20 câu hỏi và Gold Evidence")
md_lines.append("")
md_lines.append("| ID | Split | Dạng câu | Trang Gold | Filter Metadata | Câu hỏi (EN / VI) | Bằng chứng (Evidence Quote) |")
md_lines.append("|---|---|---|---|---|---|---|")

for q in questions:
    filt_str = f"`{json.dumps(q['filter'])}`" if q['filter'] else "None"
    q_text = f"**EN:** {q['question']}<br>**VI:** *{q['question_vi']}*"
    md_lines.append(f"| `{q['id']}` | **{q['split'].upper()}** | `{q['type']}` | Trang {q['gold_page']} | {filt_str} | {q_text} | *\"{q['evidence_quote']}\"* |")

with open('benchmark/questions.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(md_lines))

with open('starter/benchmark/questions.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(md_lines))

print("Successfully written benchmark/questions.json and benchmark/questions.md")

