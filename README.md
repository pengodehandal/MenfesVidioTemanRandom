# 🔥 Menfes Video Bot Telegram 🔥

Bot Menfes buat kirim vidio ke channel Telegram dengan tampilan kece dan fitur komplet. Udah support verifikasi member dan ada log admin!

## 📱 Fitur Keren

- ✅ **Support Video**: Kirim vidio maksimal 30 detik
- ✅ **Verifikasi Member**: Pastiin pengirim udah gabung channel & grup
- ✅ **Wajib Username**: Cuma yang punya username yang bisa kirim
- ✅ **Wajib Caption**: Vidio harus ada caption/pesan
- ✅ **Format Keren**: Caption tampil rapi dengan format baku
- ✅ **Cooldown**: Interval kirim 3 menit (anti spam)
- ✅ **Blacklist**: Admin bisa ban user nakal
- ✅ **Admin Log**: Semua aktivitas dilaporkan ke admin
- ✅ **Anti Spam Grup**: Bot cuma balas di chat pribadi
- ✅ **Multi Format Verifikasi**: Deteksi keanggotaan akurat banget

## 🛠️ Cara Install

### Kebutuhan Sistem

**VPS/Server minimum:**
- RAM: 1 GB
- CPU: 1 core
- Disk: 5 GB
- OS: Ubuntu 20.04/22.04 (rekomendasi)

**Software requirements:**
- Python 3.8 atau lebih baru
- pip (Python package manager)
- Git (opsional, untuk clone repo)

### Langkah Install

1. **Update sistem dulu biar fresh**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Python & tools yang diperluin**
   ```bash
   sudo apt install python3 python3-pip git screen -y
   ```

3. **Clone repository atau download kode bot**
   ```bash
   git clone https://github.com/username/menfes-video-bot.git
   cd menfes-video-bot
   ```

4. **Install library yang dibutuhin**
   ```bash
   pip3 install python-telegram-bot==20.4 # Pastiin pake versi 20+ ya
   ```

5. **Edit konfigurasi bot**
   ```bash
   nano menfesvidio.py
   ```
   
   Ganti nilai-nilai berikut:
   - `BOT_TOKEN` = Token dari @BotFather
   - `CHANNEL_ID` = Username channel tujuan (misal '@TemanRandomCH')
   - `GROUP_USERNAME` = Username grup (tanpa @, misal 'teman_random_grup')
   - `GROUP_LINK` = Link invite grup
   - `ADMIN_ID` = ID Telegram admin untuk menerima log

6. **Jalankan bot**
   
   Cara biasa (untuk test):
   ```bash
   python3 menfesvidio.py
   ```
   
   Cara pro (biar jalan terus di background):
   ```bash
   screen -S menfesbot
   python3 menfesvidio.py
   # Pencet Ctrl+A lalu D untuk detach
   ```

7. **Untuk lihat bot lagi setelah detach**
   ```bash
   screen -r menfesbot
   ```

## 📝 Cara Pake

1. Start bot: `/start`
2. Ikuti instruksi untuk gabung channel & grup
3. Klik "Sudah Bergabung - Cek Kembali"
4. Kirim video dengan caption ke bot
5. Video akan dikirim ke channel dengan format:
   ```
   📨 MENFES VIDEO

   Pesan:
   [caption mu di sini]

   Dikirim oleh: @username
   Via: @TemanRandomMenfes_bot
   ```

## ⚠️ Peringatan

- Bot harus jadi admin di channel
- Bot harus jadi member di grup
- Video maks 30 detik
- Interval minimal 3 menit antar pengiriman

## 📚 Perintah Admin

- `/ban [user_id] [alasan]` - Ban user nakal
- Semua log aktivitas dikirim ke ADMIN_ID yang dikonfigurasi

## 💖 Credits

Dikembangin dengan ❤️ untuk komunitas Telegram Indonesia.


---

*Semoga Bermanfaat! Jangan lupa kasih bintang ya kalo suka!* ⭐
