# 🎬 Rongyok Video Downloader

> 📥 เครื่องมือดาวน์โหลดวิดีโอจาก rongyok.com แบบอัตโนมัติ พร้อม Resume Support และ Video Merging

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com)

---

## ✨ คุณสมบัติเด่น

| 🏷️ Feature | 📝 รายละเอียด |
|------------|--------------|
| 🖥️ GUI + CLI | แอปเดสก์ท็อป และ Command-line interface |
| 📋 Episode Selection | ดาวน์โหลดทุกตอน หรือเลือกตอนที่ต้องการ |
| ⏸️ Resume Support | ดาวน์โหลดต่อได้หากถูกขัดจังหวะ |
| 🎞️ Video Merging | รวมไฟล์วิดีโอทุกตอนเป็นไฟล์เดียว |
| 📊 Progress Tracking | แสดงความคืบหน้าแบบ Real-time |
| 💾 State Persistence | บันทึกสถานะการดาวน์โหลดอัตโนมัติ |

---

## 🚀 การติดตั้ง

### 📋 ขั้นตอนที่ 1: Clone Repository

```bash
git clone https://github.com/your-username/rongyok-video-downloader.git
cd rongyok-video-downloader
```

### 📋 ขั้นตอนที่ 2: สร้าง Virtual Environment

```bash
# 🐍 สร้าง venv
python3 -m venv venv

# 🔌 Activate (Windows)
venv\Scripts\activate

# 🔌 Activate (macOS/Linux)
source venv/bin/activate
```

### 📋 ขั้นตอนที่ 3: ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 📋 ขั้นตอนที่ 4: ติดตั้ง FFmpeg 🎞️

> ⚠️ **จำเป็น** สำหรับการรวมไฟล์วิดีโอ (Video Merging)

| 🖥️ Platform | 📦 คำสั่งติดตั้ง |
|-------------|----------------|
| 🍎 macOS | `brew install ffmpeg` |
| 🐧 Ubuntu/Debian | `sudo apt install ffmpeg` |
| 🪟 Windows | ดาวน์โหลดจาก [ffmpeg.org](https://ffmpeg.org/download.html) |

---

## 📖 วิธีใช้งาน

### 🖥️ GUI Mode (แนะนำ ⭐)

```bash
source venv/bin/activate  # Windows: venv\Scripts\activate
python gui.py
```

#### 📸 ขั้นตอนการใช้งาน:

1. 📋 กรอก URL ซีรีส์จาก rongyok.com
2. 🔍 กดปุ่ม **"Fetch"** เพื่อโหลดรายการตอน
3. ✅ เลือกตอนที่ต้องการดาวน์โหลด
4. 📥 กดปุ่ม **"Download"** เพื่อเริ่มดาวน์โหลด
5. ☕ รอจนเสร็จสิ้น!

---

### ⌨️ CLI Mode

```bash
source venv/bin/activate

# 📥 ดาวน์โหลดทุกตอน
python cli.py https://rongyok.com/watch/?series_id=941

# 📥 ดาวน์โหลดตอนที่เลือก (ช่วง)
python cli.py https://rongyok.com/watch/?series_id=941 --episodes 1-10

# 📥 ดาวน์โหลดตอนที่เลือก (เจาะจง)
python cli.py https://rongyok.com/watch/?series_id=941 --episodes 1,3,5,7

# ▶️ ดาวน์โหลดต่อ (Resume)
python cli.py https://rongyok.com/watch/?series_id=941 --resume

# 🚫 ดาวน์โหลดโดยไม่รวมวิดีโอ
python cli.py https://rongyok.com/watch/?series_id=941 --no-merge

# 🎞️ รวมวิดีโอที่มีอยู่แล้ว
python cli.py --merge-only

# 📋 ดูรายการตอน (ไม่ดาวน์โหลด)
python cli.py https://rongyok.com/watch/?series_id=941 --list
```

---

### ⚙️ CLI Options

| 🏷️ Option | 📝 คำอธิบาย |
|-----------|------------|
| `-e, --episodes` | ตอนที่ต้องการ (เช่น "1-10", "1,3,5", "all") |
| `-o, --output` | โฟลเดอร์เก็บไฟล์ (default: ./output) |
| `-r, --resume` | ดาวน์โหลดต่อจากที่ค้างไว้ |
| `--no-merge` | ไม่รวมวิดีโอหลังดาวน์โหลดเสร็จ |
| `--merge-only` | รวมวิดีโอที่มีอยู่แล้วเท่านั้น |
| `-l, --list` | แสดงรายการตอนโดยไม่ดาวน์โหลด |

---

## 📁 โครงสร้างไฟล์

### 📦 โปรเจค

```
📦 rongyok-downloader/
├── 🖥️ gui.py           # Desktop GUI (Tkinter)
├── ⌨️ cli.py           # Command-line interface
├── 🔍 parser.py        # Episode URL parser
├── 📥 downloader.py    # Download engine + resume
├── 🎞️ merger.py        # FFmpeg video merger
├── 📋 requirements.txt # Python dependencies
└── 📂 output/          # Downloaded videos
```

### 📂 Output Folder

```
📂 output/
├── 🎬 ep_01.mp4
├── 🎬 ep_02.mp4
├── 🎬 ...
├── 🎬 ep_30.mp4
├── 🎬 merged.mp4          # 🎞️ วิดีโอรวม (ถ้าเปิด merge)
└── 💾 download_state.json # 📊 สถานะดาวน์โหลด
```

---

## ⚙️ Dependencies

| 📦 Package | 📝 หน้าที่ | 🔗 Link |
|-----------|----------|---------|
| `requests` | 🌐 HTTP requests | [PyPI](https://pypi.org/project/requests/) |
| `beautifulsoup4` | 🔍 HTML parsing | [PyPI](https://pypi.org/project/beautifulsoup4/) |
| `tqdm` | 📊 Progress bar | [PyPI](https://pypi.org/project/tqdm/) |
| `tkinter` | 🖥️ GUI (มาพร้อม Python) | Built-in |

---

## 🔧 Troubleshooting

### ❌ ปัญหา: URL หมดอายุ

> 💡 **เหตุผล:** URL วิดีโอมี Token ที่หมดอายุ

**วิธีแก้:** Parse URL ใหม่ก่อนดาวน์โหลด
```bash
python cli.py https://rongyok.com/watch/?series_id=941 --fresh
```

---

### ❌ ปัญหา: FFmpeg ไม่พบ

> 💡 **เหตุผล:** ยังไม่ได้ติดตั้ง หรือไม่อยู่ใน PATH

**วิธีตรวจสอบ:**
```bash
ffmpeg -version
```

**วิธีแก้:** ติดตั้ง FFmpeg ตามขั้นตอนด้านบน ☝️

---

### ❌ ปัญหา: ดาวน์โหลดไม่ครบ

> 💡 **เหตุผล:** อินเทอร์เน็ตขัดจังหวะ

**วิธีแก้:** ใช้ Resume feature
```bash
python cli.py https://rongyok.com/watch/?series_id=941 --resume
```

---

## 🔬 รายละเอียดทางเทคนิค

| 🏷️ หัวข้อ | 📝 รายละเอียด |
|-----------|--------------|
| 🔍 Extraction | ดึงข้อมูลจาก JavaScript data ในหน้าเว็บ |
| 🌐 Video Host | ไฟล์วิดีโอ host อยู่บน Discord CDN |
| ⏸️ Resume | รองรับ HTTP Range Requests |
| 🎞️ Merging | ใช้ FFmpeg concat (ไม่ re-encode = เร็ว) |

---

## 📜 License

MIT License - ใช้งานได้อย่างอิสระ 🎉

---

## 👤 ผู้พัฒนา

สร้างด้วย ❤️ และ ☕ มากมาย

---

## ⭐ Support

ถ้าชอบโปรเจคนี้ อย่าลืมกด ⭐ ให้ด้วยนะครับ!

```
🌟 Star this repo if you find it useful! 🌟
```

---

<p align="center">
  Made with 💜 in Thailand 🇹🇭
</p>
