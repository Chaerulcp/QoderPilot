# QoderPilot

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Disclaimer** — QoderPilot adalah project komunitas tidak resmi dan tidak berafiliasi,
> didukung, atau disponsori oleh Qoder.

QoderPilot adalah aplikasi CLI berbasis Python untuk otomatisasi provisioning akun dan
onboarding Qoder dalam satu alur yang dapat dipulihkan (*resumable*). Program menangani
pembuatan inbox sementara, signup, penyelesaian captcha, pengambilan OTP, pembuatan
Personal Access Token (PAT), penyiapan identitas client, hingga login ke **Qoder IDE**
atau **Qoder Agentic**.

Setiap akun diproses sebagai satu *job*. Jika proxy diaktifkan, satu proxy dipilih saat job
dimulai dan dipakai secara konsisten pada seluruh tahap. Job yang belum menyelesaikan login
client disimpan dalam antrean lokal dan dapat dilanjutkan (`resume`) tanpa kehilangan proxy
asalnya.

> Gunakan project ini hanya pada akun, perangkat, dan layanan yang Anda miliki atau berhak
> Anda uji. Pengguna bertanggung jawab mematuhi ketentuan layanan, kebijakan privasi, batas
> permintaan, dan peraturan yang berlaku.

QoderPilot tidak memberikan atau mengklaim Credits. Kelayakan Pro Trial dan jumlah Credits
ditentukan sepenuhnya oleh server Qoder — lihat bagian
[Credits dan Pro Trial](#credits-dan-pro-trial).

## Daftar Isi

- [Fitur](#fitur)
- [Cara Kerja](#cara-kerja)
- [Persyaratan](#persyaratan)
- [Instalasi](#instalasi)
- [Konfigurasi](#konfigurasi)
- [Penggunaan CLI](#penggunaan-cli)
- [Penyimpanan Data](#penyimpanan-data)
- [Credits dan Pro Trial](#credits-dan-pro-trial)
- [Struktur Project](#struktur-project)
- [Troubleshooting](#troubleshooting)
- [Pengembangan](#pengembangan)
- [Referensi dan Inspirasi](#referensi-dan-inspirasi)
- [Lisensi](#lisensi)

## Fitur

- Pembuatan inbox sementara melalui API Tempik — layanan email sekali pakai self-hosted
  dari repository [hirotomasato/tempik](https://github.com/hirotomasato/tempik).
- Signup Qoder menggunakan Playwright dengan stealth.
- Penyelesaian slider captcha secara lokal tanpa layanan eksternal.
- Pengambilan dan pengisian OTP otomatis; bila email OTP tidak tiba dalam waktu yang
  ditentukan, seluruh proses signup diulang dari awal secara otomatis.
- Pembuatan serta validasi Personal Access Token (PAT).
- Pilihan target login interaktif: Qoder IDE atau Qoder Agentic.
- Patch identitas lokal untuk Qoder IDE dan Qoder Agentic.
- Reset otomatis target sebelum setiap login akun untuk identitas baru, dengan opsi
  `--no-reset` bila tidak diinginkan.
- Pembersihan sesi akun lama secara terbatas sebelum setiap login baru, tanpa menghapus
  pengaturan, extension, project, atau riwayat chat lokal.
- Login native Qoder dengan email/password melalui browser terotomasi.
- Rotasi proxy per akun dengan dukungan autentikasi, termasuk relay autentikasi proxy
  untuk Qoder IDE dan Qoder Agentic.
- Antrean lokal untuk melanjutkan login yang gagal atau terinterupsi.
- Pemeriksaan instalasi melalui perintah `doctor`.
- Perintah terpisah untuk status, patch, reset, dan deep reset pada kedua aplikasi.

## Cara Kerja

```mermaid
flowchart LR
    P[Proxy job] --> M[Temp Mail]
    P --> S[Signup Qoder]
    P --> A{Pilih aplikasi}
    P --> L[Browser client login]
    M --> S
    S --> C[Captcha]
    C --> O[OTP]
    O --> T[PAT]
    T --> Q[Pending queue]
    Q --> A
    A -->|1| D[Qoder IDE]
    A -->|2| G[Qoder Agentic]
    D --> L
    G --> L
    L --> R{Login berhasil?}
    R -->|Ya| X[Success result]
    R -->|Belum| Q
```

Kredensial dimasukkan ke antrean sebelum tahap client dimulai. Akun hanya dikeluarkan dari
antrean setelah otomatisasi client mengembalikan status sukses.

## Persyaratan

| Komponen | Keterangan |
| --- | --- |
| Python | 3.10 atau lebih baru |
| Qoder | Qoder IDE atau Qoder Agentic sudah terpasang |
| Google Chrome | Dipakai untuk alur autentikasi |
| Playwright Chromium | Browser otomasi (`playwright install chromium`) |
| Tempik | Endpoint instance self-hosted yang aktif |
| Proxy HTTP | Opsional |

Target platform client yang tersedia adalah `Windows`, `Darwin`, dan `Linux`. Implementasi
telah diverifikasi pada Windows; beberapa interaksi UI pada platform atau versi Qoder yang
berbeda mungkin memerlukan tindakan manual.

Qoder Agentic saat ini khusus Windows dan menggunakan instalasi standar berikut:

```text
C:\ProgramData\Qoder\Qoder Launcher\Qoder Launcher.exe
C:\Program Files\Qoder\Qoder\Qoder.exe
```

## Instalasi

### Windows PowerShell

```powershell
git clone https://github.com/Chaerulcp/QoderPilot.git
cd QoderPilot

py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m playwright install chromium
```

### Linux atau macOS

```bash
git clone https://github.com/Chaerulcp/QoderPilot.git
cd QoderPilot

python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e .
./.venv/bin/python -m playwright install chromium
```

### Konfigurasi awal

Salin konfigurasi contoh, lalu sesuaikan isinya (terutama `api.tempmail_base`):

```powershell
Copy-Item config.example.toml config.toml
```

Jalankan pemeriksaan awal. Semua pemeriksaan wajib harus menampilkan status `OK` sebelum
menjalankan pipeline:

```powershell
.\.venv\Scripts\qoderpilot.exe doctor
```

## Konfigurasi

Konfigurasi menggunakan format TOML. File default adalah `config.toml`; contoh lengkap
tersedia di [`config.example.toml`](config.example.toml). Path relatif dihitung dari
direktori tempat `config.toml` berada.

### API

```toml
[api]
tempmail_base = "https://tempik.example.com/api"
qoder_base = "https://qoder.com"
qoder_openapi = "https://openapi.qoder.sh"
```

`tempmail_base` harus menunjuk ke endpoint Tempik yang aktif dan biasanya menyertakan prefix
`/api`.

### Integrasi Tempik (email sementara)

QoderPilot tidak menyediakan layanan email sementara sendiri. Tahap signup menggunakan
[Tempik](https://github.com/hirotomasato/tempik), layanan disposable email **self-hosted**
yang harus Anda deploy dan jalankan sendiri terlebih dahulu:

1. Clone dan jalankan instance Tempik mengikuti petunjuk pada repository
   [hirotomasato/tempik](https://github.com/hirotomasato/tempik), termasuk menyiapkan
   domain email yang akan dipakai untuk inbox.
2. Pastikan instance dapat diakses dari mesin yang menjalankan QoderPilot (langsung atau
   melalui proxy yang dikonfigurasi).
3. Arahkan `api.tempmail_base` pada `config.toml` ke endpoint API instance tersebut,
   misalnya `https://tempik.domain-anda.com/api`.

QoderPilot memakai Tempik untuk membuat inbox baru per akun, menunggu email OTP dari Qoder
(polling), dan mengekstrak kode verifikasi. Daftar domain inbox dibaca otomatis dari
konfigurasi instance Tempik (`mailDomains`). Verifikasi bahwa endpoint berfungsi dengan
perintah `doctor` — pemeriksaan `Temp Mail` harus berstatus `OK`.

### Signup

```toml
[signup]
headless = false
retry = 2
```

Gunakan `headless = false` ketika perlu melihat proses browser atau menyelesaikan fallback
manual. Mode headless dapat dipakai apabila alur autentikasi pada environment Anda mendukungnya.

`retry` menentukan berapa kali proses signup diulang dari awal ketika email OTP tidak tiba
dalam waktu yang ditentukan. Total percobaan adalah `retry + 1`. Setiap pengulangan memakai
inbox sementara, password, dan browser baru.

### Proxy

```toml
[proxy]
mode = "file"
pool_file = "proxies.txt"
```

Nilai `mode` yang didukung:

| Mode | Perilaku |
| --- | --- |
| `none` | Seluruh tahap menggunakan koneksi langsung. |
| `file` | Proxy dipilih secara round-robin dari `pool_file`. |
| `env` | Proxy dibaca dari environment variable `QODER_PROXY`. |

Format baris proxy:

```text
host:port:user:password
http://user:password@host:port
host:port
```

Contoh penggunaan environment variable:

```powershell
$env:QODER_PROXY = "http://user:password@proxy.example.com:8080"
.\.venv\Scripts\qoderpilot.exe run -n 1
```

Untuk setiap job, satu konfigurasi proxy yang sama diterapkan secara konsisten pada:

- request Temp Mail;
- browser signup;
- browser client login;
- proses Qoder IDE atau Qoder Agentic melalui `HTTP_PROXY`, `HTTPS_PROXY`, dan `ALL_PROXY`;
- Qoder IDE dan Qoder Agentic menerima argumen `--proxy-server`.

Untuk proxy yang memakai username/password, Qoder IDE dan Qoder Agentic diarahkan melalui
relay lokal `127.0.0.1` yang menambahkan autentikasi ke proxy upstream. Relay memakai proxy
job yang sama, tidak mencetak kredensial, dan otomatis berhenti ketika proses aplikasi
ditutup. Cara ini diperlukan karena Electron/Launcher hanya dapat menerima host/port melalui
`--proxy-server` dan tidak meneruskan kredensial proxy secara langsung.

Sebelum login dimulai, QoderPilot melakukan pengecekan IP keluar melalui proxy (best-effort)
agar jalur jaringan yang dipakai terlihat di log. Hasilnya informatif: proxy rotasi bisa saja
keluar dari IP yang berbeda dengan host proxy. Setel `QODERPILOT_SKIP_IP_CHECK=1` untuk
mematikan pengecekan ini.

Password proxy tidak ditampilkan pada output CLI. File `proxies.txt` dan seluruh data runtime
telah dimasukkan ke `.gitignore`.

### Client dan pipeline

```toml
[client]
platform = "Windows"   # Windows | Darwin | Linux
headless = false
delay_min_seconds = 30
delay_max_seconds = 60

[pipeline]
default_count = 1
```

`delay_min_seconds` dan `delay_max_seconds` menentukan jeda acak di antara job lengkap.
`default_count` digunakan ketika opsi `-n` tidak diberikan.

### Output dan logging

```toml
[output]
data_dir = "data"

[logging]
file = "data/qoder.log"
```

## Penggunaan CLI

Pada Windows, contoh berikut menggunakan interpreter dari virtual environment secara langsung
sehingga aktivasi PowerShell tidak diperlukan. Opsi global (`--config`, `--version`) harus
diletakkan sebelum subcommand.

| Perintah | Fungsi |
| --- | --- |
| `run -n <jumlah>` | Signup lalu client login untuk sejumlah akun. |
| `resume` | Melanjutkan login client yang tertunda dengan proxy asalnya. |
| `status` | Menampilkan jumlah job pending, sukses, dan gagal. |
| `doctor` | Memvalidasi prasyarat instalasi. |
| `patch` | Menerapkan identitas lokal baru (IDE atau Agentic). |
| `reset` | Reset data lalu menerapkan patch baru (IDE atau Agentic). |
| `reset --deep` | Menghapus seluruh data lokal aplikasi yang dipilih. |

### Menjalankan pipeline

```powershell
# Memproses satu akun
.\.venv\Scripts\qoderpilot.exe run -n 1

# Memproses tiga akun secara berurutan
.\.venv\Scripts\qoderpilot.exe run -n 3
```

Pipeline menyelesaikan signup dan client login untuk satu akun sebelum beralih ke akun
berikutnya.

Sebelum tahap client login pertama, program menampilkan pilihan target:

```text
Pilih aplikasi tujuan login:
  1. Qoder IDE
  2. Qoder Agentic (C:\ProgramData\Qoder\Qoder Launcher)
Masukkan pilihan [1/2], lalu tekan Enter:
```

Masukkan `1` atau `2`, kemudian tekan Enter. Eksekusi login tidak dimulai sebelum pilihan
valid diterima. Pilihan tersebut digunakan untuk seluruh job dalam satu eksekusi perintah
`run` atau `resume`.

Pada kedua target Windows, setelah aplikasi terbuka:

1. Klik `Sign In` pada aplikasi Qoder yang dipilih.
2. Tunggu sampai tab login Qoder benar-benar terbuka di browser.
3. Kembali ke terminal dan tekan Enter.

QoderPilot baru memindai URL sesi setelah Enter ditekan. Login menggunakan form email dan
password Qoder, bukan Google OAuth.

### Reset otomatis sebelum login

Secara default setiap job pada `run` dan `resume` menjalankan reset target terlebih dahulu
sebelum login sehingga tiap akun mendapatkan identitas baru. Jika reset gagal, job dilewati
dan tetap berada di antrean pending. Gunakan `--no-reset` untuk mempertahankan perilaku lama
yang hanya membersihkan sesi akun:

```powershell
.\.venv\Scripts\qoderpilot.exe run -n 1 --no-reset
.\.venv\Scripts\qoderpilot.exe resume --no-reset
```

Reset penuh menghapus seluruh data aplikasi target, termasuk:

- Qoder IDE: `%APPDATA%\Qoder`, `%USERPROFILE%\.qoder`, dan `%LOCALAPPDATA%\Qoder\Cache`;
- Qoder Agentic: `%APPDATA%\com.qoder.app.stable` beserta pengenal persisten di home
  bersama (`%USERPROFILE%\.qoder\installation_id` dan `%USERPROFILE%\.qoder\.auth`), lalu
  menulis ulang `auth.machine-id` dengan UUID baru.

Penghapusan memakai walk bottom-up dan retry singkat sehingga tetap bekerja walau ada file
read-only atau handle yang baru dilepas proses Qoder (yang dibunuh bersama process tree-nya).
Jika masih ada direktori yang gagal dihapus, reset dianggap gagal dan login dilewati agar
identitas tidak bercampur.

`machineid` Qoder IDE kini dibuat sebagai UUID v4 (format asli aplikasi) karena Qoder
memvalidasi isi file tersebut dan membuat ulang UUID sendiri bila formatnya tidak cocok.
Setelah aplikasi diluncurkan, QoderPilot mencatat di log apakah machine ID hasil patch
dipertahankan atau ditulis ulang oleh aplikasi.

### Dry run

```powershell
.\.venv\Scripts\qoderpilot.exe run -n 1 --dry-run
```

Dry run memvalidasi prasyarat dan pemilihan proxy tanpa membuat akun, menjalankan browser,
atau mengubah data Qoder.

### Melanjutkan job tertunda

```powershell
.\.venv\Scripts\qoderpilot.exe resume
```

Setiap job memakai kembali proxy yang disimpan ketika akun dibuat.

### Melihat status

```powershell
.\.venv\Scripts\qoderpilot.exe status
```

Output hanya menampilkan jumlah pending, sukses, dan gagal. Password tidak ditampilkan.

### Menggunakan file konfigurasi lain

```powershell
.\.venv\Scripts\qoderpilot.exe --config config.production.toml run -n 1
```

Path konfigurasi juga dapat ditetapkan melalui environment variable `QODERPILOT_CONFIG`.
Opsi `--config` tetap menjadi pilihan yang paling eksplisit untuk script otomasi.

### Utilitas Qoder IDE dan Qoder Agentic

Perintah `patch` dan `reset` bekerja untuk kedua aplikasi. Ketika opsi `--target` tidak
diberikan, program menampilkan pilihan aplikasi terlebih dahulu:

```text
Pilih aplikasi tujuan:
  1. Qoder IDE
  2. Qoder Agentic (C:\ProgramData\Qoder\Qoder Launcher)
Masukkan pilihan [1/2], lalu tekan Enter:
```

```powershell
# Patch identitas dengan pilihan aplikasi interaktif
.\.venv\Scripts\qoderpilot.exe patch

# Patch identitas Qoder IDE atau Qoder Agentic secara eksplisit
.\.venv\Scripts\qoderpilot.exe patch --target ide
.\.venv\Scripts\qoderpilot.exe patch --target agentic

# Reset data aplikasi lalu menerapkan patch baru
.\.venv\Scripts\qoderpilot.exe reset --target ide
.\.venv\Scripts\qoderpilot.exe reset --target agentic

# Menghapus seluruh data lokal aplikasi yang dipilih
.\.venv\Scripts\qoderpilot.exe reset --deep --target agentic
```

Gunakan `--target` pada environment non-interaktif karena pemilihan aplikasi membutuhkan
terminal yang dapat menerima input.

Patch Qoder IDE menulis ulang `machineid`, `ms_deviceid`, dan `serviceMachineId` serta
membersihkan state sesi. Patch Qoder Agentic mengganti `auth.machine-id`, regenerasi
`device_id_salt` pada `Preferences`, menghapus identitas onboarding, dan membersihkan sesi
auth, tanpa menghapus data aplikasi seperti riwayat chat.

Perintah reset meminta konfirmasi. Opsi `--yes` tersedia untuk environment non-interaktif,
tetapi sebaiknya digunakan hanya ketika target data telah dipastikan.

## Penyimpanan Data

| File | Isi |
| --- | --- |
| `data/accounts.jsonl` | Email, password, PAT, status PAT, dan waktu signup. |
| `data/pending_jobs.jsonl` | Kredensial serta proxy untuk client login yang belum selesai. |
| `data/qoder_sukses.txt` | Hasil client login yang berhasil. |
| `data/qoder_failed.txt` | Riwayat client login yang gagal. |
| `data/qoder.log` | Log tahap signup. |
| `data/qoder_client.log` | Log tahap Qoder IDE/Agentic dan client login. |

File tersebut dapat berisi informasi sensitif. Jangan mengunggah folder `data/`,
`proxies.txt`, log, screenshot autentikasi, atau konfigurasi yang berisi endpoint privat ke
repository publik.

## Credits dan Pro Trial

QoderPilot hanya menangani signup dan login client; project ini tidak memiliki endpoint atau
mekanisme untuk memberikan Credits. Menurut dokumentasi resmi Qoder, Pro Trial diberikan
otomatis oleh server pada login client pertama jika pengguna memenuhi persyaratan, termasuk
menggunakan client terbaru, tidak berjalan pada virtual machine, dan belum pernah menerima
trial. Trial dibatasi satu kali per pengguna; akun tambahan dapat ditangguhkan.

Periksa nilai aktual melalui `Settings > Usage` di Qoder. Jika data kredit tidak tersedia
secara lokal, CLI menampilkan `Credits tidak dapat diverifikasi` dan tidak mengarang nilai
default. Lihat [Qoder Pricing](https://docs.qoder.com/account/pricing) dan
[Qoder FAQ](https://docs.qoder.com/troubleshooting/common-issue) untuk aturan terbaru.

## Struktur Project

```text
QoderPilot/
|-- pyproject.toml             # Metadata package dan CLI
|-- main.py                    # Entry point kompatibilitas
|-- config.example.toml        # Template konfigurasi
|-- requirements.txt           # Daftar dependensi alternatif
|-- qoderpilot/
|   |-- cli.py                 # Command-line interface
|   |-- config.py              # Validasi konfigurasi
|   |-- models.py              # Model job dan hasil
|   |-- pipeline.py            # Orkestrasi alur utama
|   `-- storage.py             # Antrean pending yang atomik
|-- qoder_creator/
|   |-- signup.py              # Signup, captcha, OTP, dan PAT
|   |-- tempmail.py            # Client Tempik
|   |-- proxy.py               # Parsing dan rotasi proxy
|   |-- captcha.py             # Slider captcha solver
|   `-- ...
|-- qoder_client/
|   |-- automation.py          # Patch, reset, dan login Qoder IDE
|   |-- agentic.py             # Login, patch, dan reset Qoder Agentic (Windows Launcher)
|   `-- proxy_bridge.py        # Relay autentikasi proxy khusus Agentic
`-- tests/                     # Unit dan integration tests
```

## Troubleshooting

### `doctor` melaporkan dependensi belum tersedia

Pastikan perintah dijalankan menggunakan interpreter virtual environment yang sama:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

### Playwright Chromium tidak ditemukan

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

### Endpoint Temp Mail gagal

- Pastikan instance Tempik sudah di-deploy dan berjalan; ikuti petunjuk pada repository
  [hirotomasato/tempik](https://github.com/hirotomasato/tempik).
- Pastikan `api.tempmail_base` dapat diakses.
- Pastikan URL menyertakan path API yang benar.
- Periksa apakah proxy mengizinkan koneksi ke endpoint tersebut.
- Jika pesan memuat `Tunnel connection failed: 402 Payment Required`, saldo/kuota proxy di
  `proxies.txt` sudah habis — isi ulang langganan atau ganti proxy. Kode `407` berarti
  username/password proxy salah. QoderPilot kini menyertakan diagnosis ini otomatis pada
  pesan error temp-mail dan pada warning pemeriksaan IP keluar.
- Periksa `data/qoder.log` untuk status HTTP atau timeout.

### Signup berhasil tetapi client login belum selesai

- Pastikan aplikasi Qoder yang dipilih dan Google Chrome terpasang.
- QoderPilot menghentikan target yang dipilih dan membersihkan token akun lamanya secara
  otomatis sebelum membuat sesi PKCE baru. Untuk IDE akan muncul pesan
  `Previous Qoder account session cleared`; untuk Agentic akan muncul
  `Sesi akun lama Qoder Agentic sudah dibersihkan`.
- Gunakan `client.headless = false`.
- QoderPilot menggunakan form email/password Qoder, bukan tombol Google OAuth.
- Jangan tutup atau membuka ulang Qoder selama login. URL PKCE hanya berlaku untuk proses
  Qoder yang membuatnya.
- Pada Windows, klik `Sign In` secara manual lalu tunggu sampai tab browser benar-benar
  terbuka. Tidak ada pemindaian atau klik otomatis sebelum Enter ditekan dan pesan
  `Mencari URL PKCE` ditampilkan.
- Jalankan `resume`; job akan tetap menggunakan proxy asal.
- Periksa `data/qoder_client.log`.
- Jika selector halaman Qoder berubah, periksa `data/native_login_failed.png`. Jangan
  unggah screenshot tersebut karena dapat memuat alamat email akun.

Untuk Qoder Agentic, pastikan kedua file instalasi pada bagian Persyaratan tersedia. Status
berhasil hanya diberikan setelah log aplikasi mencatat `Device login completed`. Jika gagal,
periksa `data/agentic_login_failed.png` dan `data/qoder_client.log` tanpa mempublikasikan
data sensitif di dalamnya.

### Halaman menampilkan `Parameter invalid`

Qoder IDE atau Agentic harus membuat URL PKCE yang berisi `nonce`, `challenge`,
`challenge_method`, dan `redirect_uri`. QoderPilot menangkap URL tersebut dari browser lalu
memvalidasinya sebelum login. Qoder IDE menggunakan callback `qoder://`, sedangkan Agentic
menggunakan `qoder-app://`. URL sederhana yang hanya berisi `machine_id` sengaja ditolak
karena tidak terhubung ke sesi autentikasi aplikasi. Pastikan browser default tidak dibatasi
oleh software yang mencegah Qoder membuka tab login, lalu jalankan kembali `resume`.

### Proxy gagal atau meminta autentikasi

- Periksa format baris dan kredensial proxy.
- Pastikan proxy mendukung trafik HTTPS.
- Jalankan `doctor` untuk memastikan pool dapat dibaca.
- Hindari mengganti isi antrean pending secara manual karena proxy tersimpan bersama job.

Jika Qoder Agentic sebelumnya menampilkan `登录服务返回异常（HTTP 407）`, pastikan versi
QoderPilot sudah memuat `qoder_client/proxy_bridge.py`, tutup Agentic, lalu jalankan kembali
`resume`. Output log harus memuat `Agentic authenticated proxy bridge ready`; kredensial
proxy tidak akan muncul pada command line Qoder.

## Pengembangan

Jalankan seluruh test dengan:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

Kontribusi dipersilakan. Baca [`CONTRIBUTING.md`](CONTRIBUTING.md) sebelum membuka pull
request. Untuk laporan kerentanan, ikuti [`SECURITY.md`](SECURITY.md) dan jangan
mempublikasikan detail sensitif melalui issue umum.

## Referensi dan Inspirasi

QoderPilot terinspirasi dan dikembangkan dengan rujukan dari project-project sebelumnya:

- [hirotomasato/qoder-creator](https://github.com/hirotomasato/qoder-creator)
- [okky-x0f/qoder-creator](https://github.com/okky-x0f/qoder-creator)
- [arbilaksmana/qoder-autoreg](https://github.com/arbilaksmana/qoder-autoreg) — solver
  slider captcha pada `qoder_creator/captcha.py` di-port dari project ini.

Sebagian alur otomasi dan pendekatan pada project ini dibangun berdasarkan repository
tersebut, lalu dikembangkan ulang dan diperluas untuk Qoder IDE serta Qoder Agentic.
QoderPilot juga berintegrasi dengan [hirotomasato/tempik](https://github.com/hirotomasato/tempik)
sebagai layanan email sementara self-hosted.

## Lisensi

QoderPilot didistribusikan di bawah [MIT License](LICENSE) — Copyright © 2026
Chaerul Candra Pranugrah.

Project ini dikembangkan dengan inspirasi dan sebagian kode yang diturunkan dari
project-project berlisensi MIT:
[hirotomasato/qoder-creator](https://github.com/hirotomasato/qoder-creator),
[okky-x0f/qoder-creator](https://github.com/okky-x0f/qoder-creator), dan
[arbilaksmana/qoder-autoreg](https://github.com/arbilaksmana/qoder-autoreg) — solver
slider captcha pada `qoder_creator/captcha.py` di-port dari project tersebut. QoderPilot
juga berintegrasi dengan layanan email sementara
[Tempik](https://github.com/hirotomasato/tempik) (MIT) yang di-deploy terpisah oleh
pengguna dan tidak disertakan dalam distribusi ini.

Atribusi lengkap beserta notices hak cipta masing-masing project dipertahankan dalam
[`NOTICE`](NOTICE).
