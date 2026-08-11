# Dashboard Analisis Pola Kerja Pembacaan Meter

Dashboard Streamlit untuk menganalisis aktivitas pembacaan meter.

## File
- `app.py` — aplikasi Streamlit
- `requirements.txt` — dependency Python

## Menjalankan dari Google Colab setelah repository di-upload ke GitHub

```python
!git clone https://github.com/USERNAME/NAMA-REPOSITORY.git
%cd NAMA-REPOSITORY

!pip install -r requirements.txt -q

!streamlit run app.py &>/content/streamlit.log &
```

Untuk membuka aplikasi dari Colab, gunakan tunnel seperti ngrok atau Cloudflare Tunnel.

## Format Excel
Kolom minimum yang digunakan:
- `NOMOR`
- `WAKTU`
- `LATITUDE`
- `LONGITUDE`
- `TGLBACA`
- `IDPEL`

Contoh `WAKTU`: `0 00:12:45`
