# Panduan Kontribusi

Terima kasih atas minat Anda untuk berkontribusi pada QoderPilot. Kontribusi berupa laporan
bug, perbaikan dokumentasi, test, dan perubahan kode dipersilakan selama tetap berada dalam
ruang lingkup penggunaan yang sah dan bertanggung jawab.

## Sebelum memulai

1. Periksa issue yang sudah ada untuk menghindari duplikasi.
2. Untuk perubahan besar, buka discussion atau issue terlebih dahulu agar desain dapat
   disepakati sebelum implementasi.
3. Jangan menyertakan akun, password, PAT, OTP, endpoint privat, kredensial proxy, log mentah,
   atau screenshot autentikasi.
4. Jangan mengirim perubahan yang ditujukan untuk penyalahgunaan layanan, penghindaran kontrol
   akses, atau penggunaan sistem tanpa izin.

Kerentanan keamanan tidak boleh dilaporkan melalui issue publik. Ikuti
[`SECURITY.md`](SECURITY.md).

## Menyiapkan environment pengembangan

```powershell
git clone <repository-url>
cd qoderpilot
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m playwright install chromium
Copy-Item config.example.toml config.toml
```

Gunakan endpoint dan akun pengujian yang memang Anda miliki. Jangan melakukan test integrasi
terhadap layanan produksi tanpa izin.

## Standar perubahan

- Pertahankan kompatibilitas dengan Python 3.10+.
- Gunakan type hint pada batas antarmodule dan input eksternal.
- Jaga pemisahan antara orkestrasi (`qoderpilot`), signup (`qoder_creator`), dan client
  desktop (`qoder_client`).
- Jangan menulis kredensial ke output terminal atau menambahkannya ke source code.
- Gunakan pemanggilan subprocess berbentuk list argument dan hindari `shell=True`.
- Tambahkan penanganan error yang menghasilkan pesan operasional yang dapat ditindaklanjuti.
- Perbarui dokumentasi dan `config.example.toml` ketika perilaku atau konfigurasi berubah.

## Menjalankan pemeriksaan

```powershell
.\.venv\Scripts\python.exe -m compileall -q main.py qoderpilot qoder_creator qoder_client tests
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\qoderpilot.exe doctor
```

Test otomatis tidak boleh membuat akun sungguhan, menghapus data Qoder, atau bergantung pada
kredensial lokal pengembang. Gunakan fake atau mock untuk batas jaringan dan aplikasi desktop.

## Membuka pull request

Pull request sebaiknya berisi:

- ringkasan masalah dan solusi;
- alasan desain jika ada perubahan perilaku;
- test yang ditambahkan atau diperbarui;
- hasil perintah test;
- dampak terhadap konfigurasi, data, atau kompatibilitas;
- screenshot yang sudah disanitasi jika perubahan menyangkut output UI.

Pastikan pull request tidak menyertakan file berikut:

- `config.toml` yang berisi konfigurasi privat;
- `proxies.txt`;
- folder `data/`;
- `.venv/`;
- PAT, password, OTP, cookie, token sesi, atau log autentikasi.

Dengan mengirim kontribusi, Anda menyetujui bahwa kontribusi tersebut didistribusikan di bawah
lisensi project.



