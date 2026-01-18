# 📋 TODO - Rongyok Video Downloader

> 📅 อัพเดทล่าสุด: 2026-01-18

---

## ✅ เสร็จแล้ว (Completed)

### 🎯 Phase 1: Core Features
- [x] 🔍 สร้าง `parser.py` - ดึง URL วิดีโอจาก JavaScript
- [x] 📥 สร้าง `downloader.py` - Download engine พร้อม resume support
- [x] 🎞️ สร้าง `merger.py` - รวมวิดีโอด้วย FFmpeg
- [x] ⌨️ สร้าง `cli.py` - Command-line interface
- [x] 🖥️ สร้าง `gui.py` - Desktop GUI ด้วย Tkinter
- [x] 📋 สร้าง `requirements.txt` - Python dependencies

### 🎯 Phase 2: GUI Improvements
- [x] 📝 เพิ่ม Debug Log tab ใน GUI
- [x] 🔧 แก้ไข EP01.mp4 pattern สำหรับ series 1038
- [x] 📋 เพิ่มปุ่ม Paste สำหรับ clipboard URL

### 🎯 Phase 3: Repository Setup
- [x] 📄 สร้าง `.gitignore` สำหรับ Python project
- [x] 🔄 สร้าง GitHub Actions CI workflow
- [x] 📖 สร้าง `README.md` ภาษาไทยพร้อม emoji
- [x] 📜 เพิ่ม MIT License
- [x] 🔧 Git init และ push ไป GitHub
- [x] 🔒 แก้ไข security vulnerabilities (ลบ AI/IDE config files)

### 🎯 Phase 4: CI/CD & Release
- [x] 🚀 สร้าง Release workflow สำหรับ Windows, macOS, Linux
- [x] 📦 Build executables ด้วย PyInstaller
- [x] 🎉 Release v1.0.0 ไป GitHub

### 🎯 Phase 5: Testing
- [x] 🧪 เพิ่ม Unit tests สำหรับ `parser.py` (37 tests)
- [x] 📦 เพิ่ม pytest และ pytest-cov ใน requirements.txt

---

## 🔄 กำลังทำ (In Progress)

- [ ] _(ไม่มี)_

---

## 📝 รอทำ (Pending)

### 🎨 UI/UX Improvements
- [ ] 🌙 เพิ่ม Dark mode สำหรับ GUI
- [ ] 📊 เพิ่ม Download speed graph
- [ ] 🔔 เพิ่ม Desktop notifications เมื่อดาวน์โหลดเสร็จ
- [ ] 🌐 รองรับหลายภาษา (i18n)

### ⚡ Performance
- [ ] 🚀 เพิ่ม Multi-threaded download
- [ ] 💾 เพิ่ม Download queue management
- [ ] 📈 ปรับปรุง Memory usage

### 🔧 Features
- [ ] 🔄 เพิ่ม Auto-update checker
- [ ] 📂 เพิ่ม Custom output filename pattern
- [ ] 🎬 รองรับ Subtitle download
- [ ] 📱 สร้าง Mobile app (Expo/React Native)

### 🧪 Testing
- [x] ✅ เพิ่ม Unit tests สำหรับ parser.py (37 tests ผ่านทั้งหมด)
- [ ] 🔍 เพิ่ม Unit tests สำหรับ downloader.py
- [ ] 🔍 เพิ่ม Unit tests สำหรับ merger.py
- [ ] 🔍 เพิ่ม Integration tests
- [ ] 📊 เพิ่ม Code coverage report

### 📚 Documentation
- [ ] 📖 เพิ่ม API documentation
- [ ] 🎥 สร้าง Video tutorial
- [ ] ❓ เพิ่ม FAQ section

---

## 🐛 Known Issues

| 🔢 | 📝 Issue | 🏷️ Status |
|----|----------|-----------|
| 1 | URL วิดีโอหมดอายุหลังจากเวลาผ่านไป | ⚠️ Expected behavior |
| 2 | ต้องติดตั้ง FFmpeg แยกต่างหาก | 📋 Documented |

---

## 💡 Ideas / Future

- 🌐 Web-based UI (Flask/FastAPI)
- 🔌 Browser extension
- 📺 รองรับเว็บไซต์อื่นๆ
- ☁️ Cloud storage integration (Google Drive, Dropbox)
- 🤖 Telegram bot

---

## 📊 Progress Summary

| Phase | Status | Progress |
|-------|--------|----------|
| Core Features | ✅ Done | 100% |
| GUI Improvements | ✅ Done | 100% |
| Repository Setup | ✅ Done | 100% |
| CI/CD & Release | ✅ Done | 100% |
| Testing | 🔄 In Progress | 25% |
| UI/UX Improvements | 📝 Pending | 0% |
| Performance | 📝 Pending | 0% |

---

<p align="center">
  📋 Last updated: 2026-01-18 | 🎬 v1.0.0
</p>
