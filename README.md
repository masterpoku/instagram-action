# instagram-action

# Instagram API Flask App

## Deskripsi

Aplikasi ini adalah API berbasis Flask yang memungkinkan interaksi dengan Instagram menggunakan library `instagrapi`. API ini mendukung berbagai fungsi seperti login, logout, mengirim dan menerima pesan langsung, memberi komentar, menyukai media, serta mengupload post, reel, dan video.

## Fitur

- **Login**: Login ke Instagram menggunakan username dan password.
- **Logout**: Logout dan hapus sesi.
- **Kirim Pesan Langsung**: Kirim pesan langsung ke pengguna Instagram.
- **Dapatkan Pesan Langsung**: Ambil pesan langsung dari akun Instagram.
- **Comment**: Berikan komentar pada media Instagram.
- **Like Media**: Suka media di Instagram.
- **Upload Post**: Upload foto ke Instagram.
- **Upload Reel**: Upload reel ke Instagram.
- **Upload Video**: Upload video ke Instagram.

## Instalasi

1. **Clone Repository**

    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Install Dependencies**

    Buat dan aktifkan lingkungan virtual (opsional), lalu install dependencies menggunakan pip:

    ```bash
    python -m venv venv
    source venv/bin/activate  # untuk Unix/macOS
    venv\Scripts\activate  # untuk Windows
    pip install -r requirements.txt
    ```

3. **Set Up Environment Variables**

    Pastikan untuk mengganti `your_secret_key` dengan kunci yang aman dalam file `app.py`.

4. **Membuat Direktori Session**

    Direktori ini digunakan untuk menyimpan file sesi.

    ```bash
    mkdir sessions
    ```

## Penggunaan

1. **Menjalankan Aplikasi**

    Jalankan server Flask:

    ```bash
    python app.py
    ```

2. **Endpoints API**

    - **Login**
    
      `POST /login`
    
      Request body:
      ```json
      {
        "username": "your_username",
        "password": "your_password"
      }
      ```

    - **Logout**

      `POST /logout`

      Request body:
      ```json
      {
        "session_id": "your_session_id"
      }
      ```

    - **Kirim Pesan Langsung**

      `POST /send_dm`

      Request body:
      ```json
      {
        "session_id": "your_session_id",
        "to": "recipient_username",
        "message": "your_message"
      }
      ```

    - **Dapatkan Pesan Langsung**

      `POST /get_dms`

      Request body:
      ```json
      {
        "session_id": "your_session_id"
      }
      ```

    - **Comment**

      `POST /comment`

      Request body:
      ```json
      {
        "session_id": "your_session_id",
        "url": "media_url",
        "comment_text": "your_comment"
      }
      ```

    - **Like Media**

      `POST /like`

      Request body:
      ```json
      {
        "session_id": "your_session_id",
        "url": "media_url"
      }
      ```

    - **Upload Post**

      `POST /upload_post`

      Request body:
      ```json
      {
        "session_id": "your_session_id",
        "url": "media_url",
        "caption": "your_caption"
      }
      ```

    - **Upload Reel**

      `POST /upload_reel`

      Request body:
      ```json
      {
        "session_id": "your_session_id",
        "url": "media_url",
        "caption": "your_caption"
      }
      ```

    - **Upload Video**

      `POST /upload_video`

      Request body:
      ```json
      {
        "session_id": "your_session_id",
        "url": "media_url",
        "caption": "your_caption"
      }
      ```

## Catatan

- Pastikan untuk mengganti placeholder seperti `<repository-url>` dan `<repository-directory>` sesuai dengan informasi spesifik repositori kamu.
- Selalu periksa dan patuhi kebijakan privasi serta ketentuan layanan Instagram saat menggunakan API ini.

## Lisensi

Aplikasi ini menggunakan lisensi MIT. Lihat [LICENSE](LICENSE) untuk detail lebih lanjut.
