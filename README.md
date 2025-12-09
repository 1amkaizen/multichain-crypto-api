# Multi-Chain Crypto Utility Suite API

API service untuk manajemen dan pengiriman token crypto (ETH, USDT, USDC, BNB, SOL, dan lainnya) dengan FastAPI.

## 📦 Fitur

* **Ping API** – Mengecek status service.
* **Send Token** – Mengirim token crypto ke address lain (`send/native`, `send/usdt`, `send/usdc`).
* **Balance** – Mengecek saldo wallet.
* **Price** – Mendapatkan harga token terkini.
* **History** – Melihat riwayat transaksi.
* **Estimate Gas** – Perkiraan biaya gas untuk transaksi.
* **Tokens** – Daftar token yang tersedia.
* **Swap** – Melakukan swap token (simulasi / real swap).
* **Token Info** – Detail informasi token.
* **Transaction Status** – Mengecek status transaksi.

## 🚀 Instalasi

1. Clone repo:

```bash
git clone https://github.com/1amkaizen/Crypto-API.git
cd Crypto-API
```

2. Buat virtual environment & install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Jalankan server FastAPI:

```bash
uvicorn main:app --reload
```

atau

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Server akan berjalan di `http://127.0.0.1:8000`.

---

## 📌 Endpoint

Semua endpoint berada di prefix `/api/v1/crypto`.

| Endpoint                      | Method | Deskripsi                       |
| ----------------------------- | ------ | ------------------------------- |
| `/api/v1/crypto/ping`         | GET    | Cek status service              |
| `/api/v1/crypto/send/native`  | POST   | Kirim native token              |
| `/api/v1/crypto/send/usdt`    | POST   | Kirim USDT                      |
| `/api/v1/crypto/send/usdc`    | POST   | Kirim USDC                      |
| `/api/v1/crypto/balance`      | GET    | Cek saldo wallet                |
| `/api/v1/crypto/price`        | GET    | Mendapatkan harga token terkini |
| `/api/v1/crypto/history`      | GET    | Riwayat transaksi               |
| `/api/v1/crypto/estimate_gas` | GET    | Perkiraan biaya gas transaksi   |
| `/api/v1/crypto/tokens`       | GET    | Daftar token tersedia           |
| `/api/v1/crypto/swap`         | POST   | Simulasi Swap token             |
| `/api/v1/crypto/token_info`   | GET    | Detail informasi token          |
| `/api/v1/crypto/tx_status`    | GET    | Status transaksi                |

> Dokumentasi interaktif tersedia di `https://api.aigoretech.cloud/docs` (Swagger UI) dan `https://api.aigoretech.cloud/redoc` (ReDoc).

---

## 📝 Catatan

* Pastikan environment variables (API keys, wallet private key, dll) sudah diatur sebelum menjalankan.

---

## 👨‍💻 Kontribusi

1. Fork repo ini.
2. Buat branch baru: `git checkout -b feature/your-feature`
3. Commit perubahan: `git commit -m "Add some feature"`
4. Push ke branch: `git push origin feature/your-feature`
5. Buat Pull Request.

---

## 📄 Lisensi

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/1amkaizen/crypto-api-service/blob/main/LICENSE)


