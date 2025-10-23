# 🎯 Cambridge XML Extractor

<div align="center">

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

**เครื่องมือสกัดคำถามและคำตอบจากไฟล์ Cambridge data.js**

*A tool for extracting questions and answers from Cambridge data.js files*

</div>

---

## 🇹🇭 ภาษาไทย

### 📖 คำอธิบาย
โปรแกรมนี้เป็นเครื่องมือสำหรับสกัดคำถามและคำตอบจากไฟล์ `data.js` ของ Cambridge โดยสามารถ:
- ดาวน์โหลดและถอดรหัสไฟล์ data.js
- สกัดไฟล์ XML ที่ฝังอยู่ในไฟล์
- หาคำถามและคำตอบจากไฟล์ XML
- รองรับไฟล์ที่มีคำถามหลายข้อในไฟล์เดียว
- แสดงผลลัพธ์อย่างสวยงาม

### ✨ ฟีเจอร์
- 🔄 **รองรับไฟล์หลายประเภท** - ทั้งคำถามเดี่ยวและคำถามหลายข้อ
- 🎨 **UI สวยงาม** - แสดงผลด้วย ASCII Art และสีสัน
- 📁 **จัดการไฟล์อัตโนมัติ** - สร้างและลบไฟล์ XML อัตโนมัติ
- 🔍 **ระบบค้นหาขั้นสูง** - หาคำตอบได้หลายวิธี
- 📊 **สรุปผลลัพธ์** - แสดงสถิติการประมวลผล

### 🚀 การติดตั้ง
```bash
git clone https://github.com/z3nTr4ry/cambridge-xml-extractor.git
cd cambridge-xml-extractor
pip install -r requirements.txt
```

### 📋 ความต้องการ
- Python 3.7+
- requests
- colorama
- pathlib

### 🎮 วิธีการใช้งาน
```bash
python xml_extractor.py
```

1. เลือกตัวเลือก "1. Continue"
2. ใส่ URL ของไฟล์ data.js
3. รอการประมวลผล
4. ดูผลลัพธ์ที่ได้

#### 📸 วิธีการหา URL ของไฟล์ data.js

![How to get URL](How%20to%20get%20url.png)

*ภาพแสดงวิธีการหา URL ของไฟล์ data.js จาก Cambridge*

### 📝 ตัวอย่างการใช้งาน
```
Cambridge XML Extractor
==================================================

Enter data.js URL: https://content.cambridgeone.org/.../data.js

Processing 8 files...

cat3105020.xml
Question: Rafael practices the guitar every day. His ______ amazes me.
Options: bravery, wisdom, dedication
Correct: dedication

Summary: 6 processed, 2 skipped
```

---

## 🇺🇸 English

### 📖 Description
This tool extracts questions and answers from Cambridge `data.js` files. It can:
- Download and decode data.js files
- Extract embedded XML files
- Find questions and answers from XML files
- Support files with multiple questions
- Display results beautifully

### ✨ Features
- 🔄 **Multiple File Types** - Single and multiple questions support
- 🎨 **Beautiful UI** - ASCII Art and colored output
- 📁 **Auto File Management** - Automatic XML file creation and cleanup
- 🔍 **Advanced Search** - Multiple methods to find answers
- 📊 **Result Summary** - Processing statistics display

### 🚀 Installation
```bash
git clone https://github.com/z3nTr4ry/cambridge-xml-extractor.git
cd cambridge-xml-extractor
pip install -r requirements.txt
```

### 📋 Requirements
- Python 3.7+
- requests
- colorama
- pathlib

### 🎮 Usage
```bash
python xml_extractor.py
```

1. Select "1. Continue"
2. Enter data.js file URL
3. Wait for processing
4. View results

#### 📸 How to Get data.js URL

![How to get URL](How%20to%20get%20url.png)

*Image showing how to find data.js URL from Cambridge*

### 📝 Example Usage
```
Cambridge XML Extractor
==================================================

Enter data.js URL: https://content.cambridgeone.org/.../data.js

Processing 8 files...

cat3105020.xml
Question: Rafael practices the guitar every day. His ______ amazes me.
Options: bravery, wisdom, dedication
Correct: dedication

Summary: 6 processed, 2 skipped
```

---

## 🛠️ Technical Details

### 🔧 Supported File Types
- **Single Question Files** - One question per XML file
- **Multiple Question Files** - Multiple questions in one XML file
- **Gap Text Questions** - Fill-in-the-blank questions
- **Choice Questions** - Multiple choice questions

### 🎯 Extraction Methods
1. **Content Block Search** - Find questions in content blocks
2. **Simple Choice** - Extract from choice elements
3. **Gap Text** - Extract from gap text elements
4. **Feedback Text** - Find answers from feedback
5. **Response Declaration** - Extract from response declarations
6. **Choice Interaction** - Handle multiple question files

### 📁 File Structure
```
cambridge-xml-extractor/
├── xml_extractor.py      # Main program
├── requirements.txt      # Dependencies
├── README.md            # This file
└── decoded_xml/         # Output directory (auto-created)
```

---

## 🤝 Contributing

We welcome contributions! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**z3nTr4ry**

- GitHub: [@z3nTr4ry](https://github.com/z3nTr4ry)

---

## ⭐ Support

If you find this project helpful, please give it a star! ⭐

---

<div align="center">

**Made with ❤️ by z3nTr4ry**

</div>
