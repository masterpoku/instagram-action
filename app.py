from flask import Flask, request, jsonify, session
from flask_session import Session
import instagrapi
import os
import requests
import tempfile
from PIL import Image

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Ganti dengan kunci yang aman
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './sessions'  # Direktori untuk menyimpan file session
Session(app)

# Menyimpan clients dalam dictionary dengan session ID sebagai kunci
clients = {}
session_queue = []  # Queue untuk melacak urutan penggunaan session

# Inisialisasi direktori session
if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])

def load_sessions():
    """Memuat sesi dari filesystem dan memvalidasi mereka."""
    global clients, session_queue
    for session_id in os.listdir(app.config['SESSION_FILE_DIR']):
        session_file = os.path.join(app.config['SESSION_FILE_DIR'], session_id)
        try:
            with open(session_file, 'r') as f:
                credentials = f.read().strip().split('\n')
                if len(credentials) == 2:
                    username, password = credentials
                    cl = instagrapi.Client()
                    cl.login(username, password)
                    clients[session_id] = cl
                    session_queue.append(session_id)
        except Exception as e:
            print(f"Failed to load session {session_id}: {e}")
            os.remove(session_file)

load_sessions()

def get_next_session():
    """Mendapatkan sesi berikutnya dari queue dan memindahkannya ke akhir queue."""
    if not session_queue:
        return None
    session_id = session_queue.pop(0)
    session_queue.append(session_id)
    return session_id

def is_valid_image(file_path):
    """Memeriksa apakah file adalah gambar valid dan format yang didukung."""
    try:
        with Image.open(file_path) as img:
            img.verify()  # Verifikasi file gambar
        return img.format.lower() in {'jpg', 'jpeg', 'png', 'webp'}
    except (IOError, SyntaxError) as e:
        print(f"Image verification failed: {e}")
        return False

def download_file_from_url(url):
    """Mengunduh file dari URL dan mengembalikan path ke file sementara."""
    response = requests.get(url, stream=True)
    response.raise_for_status()

    # Membuat file sementara
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')  # Default ke PNG
    with open(temp_file.name, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    temp_file.close()

    # Memeriksa dan memperbaiki ekstensi file jika diperlukan
    if not is_valid_image(temp_file.name):
        os.remove(temp_file.name)
        raise ValueError("File yang diunduh bukan gambar valid atau format tidak didukung.")

    return temp_file.name

def get_client(session_id=None):
    """Mengambil session Instagram. Jika session_id tidak ada, ambil dari queue."""
    if session_id:
        cl = clients.get(session_id)
        if cl:
            return cl
    # Jika session_id tidak diberikan atau tidak valid, ambil dari queue
    session_id = get_next_session()
    if session_id:
        return clients.get(session_id)
    return None

# API Endpoint untuk Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    usr = data.get('username')
    pas = data.get('password')

    cl = instagrapi.Client()
    try:
        cl.login(usr, pas)
        session_id = usr  # Gunakan username sebagai session ID
        session['session_id'] = session_id
        clients[session_id] = cl

        # Simpan kredensial ke file session
        session_file = os.path.join(app.config['SESSION_FILE_DIR'], session_id)
        with open(session_file, 'w') as f:
            f.write(f"{usr}\n{pas}")

        return jsonify({"status": "success", "session_id": session_id, "message": "Login berhasil!"}), 200
    except instagrapi.exceptions.BadPassword:
        return jsonify({"status": "error", "message": "Password salah!"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# API Endpoint untuk Logout
@app.route('/logout', methods=['POST'])
def logout():
    session_id = request.json.get('session_id')
    if session_id in clients:
        del clients[session_id]
        os.remove(os.path.join(app.config['SESSION_FILE_DIR'], session_id))
    session.pop('session_id', None)
    return jsonify({"status": "success", "message": "Logout berhasil!"}), 200

@app.route('/active_sessions', methods=['GET'])
def active_sessions():
    """Mengembalikan daftar sesi yang aktif."""
    session_info = []
    for session_id in clients:
        # Mengambil username dari session_id
        username = session_id  # Di sini kita menggunakan username sebagai session_id
        session_info.append({
            "session_id": session_id,
            "username": username
        })
    return jsonify({"status": "success", "sessions": session_info}), 200

# API Endpoint untuk Kirim Pesan Langsung
@app.route('/send_dm', methods=['POST'])
def send_dm():
    data = request.json
    session_id = data.get('session_id')
    cl = get_client(session_id)

    if cl is None:
        return jsonify({"status": "error", "message": "Session tidak ditemukan atau sudah expired!"}), 401

    recipient_username = data.get('to')
    message_text = data.get('message')

    try:
        user_id = cl.user_id_from_username(recipient_username)
        cl.direct_message(user_id, message_text)
        return jsonify({"status": "success", "message": "Direct message sent!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# API Endpoint untuk Dapatkan Pesan Langsung
@app.route('/get_dms', methods=['POST'])
def get_dms():
    data = request.json
    session_id = data.get('session_id')
    cl = get_client(session_id)

    if cl is None:
        return jsonify({"status": "error", "message": "Session tidak ditemukan atau sudah expired!"}), 401

    try:
        inbox = cl.direct_threads()
        messages = []
        for thread in inbox:
            for item in thread['items']:
                messages.append({
                    "id": item['id'],
                    "text": item['text'],
                    "from": item['user']['username'],
                    "timestamp": item['timestamp']
                })
        return jsonify({"status": "success", "messages": messages}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# API Endpoint untuk Comment
@app.route('/comment', methods=['POST'])
def comment():
    data = request.json
    session_id = data.get('session_id')
    cl = get_client(session_id)

    if cl is None:
        return jsonify({"status": "error", "message": "Session tidak ditemukan atau sudah expired!"}), 401

    url = data.get('url')
    comment_text = data.get('comment_text')
    try:
        media_id = cl.media_pk_from_url(url)
        cl.media_comment(media_id, comment_text)
        return jsonify({"status": "success", "message": "Komentar diposting!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# API Endpoint untuk Like Media
@app.route('/like', methods=['POST'])
def like_media():
    data = request.json
    session_id = data.get('session_id')
    cl = get_client(session_id)

    if cl is None:
        return jsonify({"status": "error", "message": "Session tidak ditemukan atau sudah expired!"}), 401

    url = data.get('url')
    try:
        media_id = cl.media_pk_from_url(url)
        cl.media_like(media_id)
        return jsonify({"status": "success", "message": "Media disukai!"}), 200
    except instagrapi.exceptions.MediaError:
        return jsonify({"status": "error", "message": "Terjadi kesalahan pada media dari Instagram"}), 400
    except instagrapi.exceptions.MediaNotFound:
        return jsonify({"status": "error", "message": "Media tidak ditemukan!"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# API Endpoint untuk Upload Post
@app.route('/upload_post', methods=['POST'])
def upload_post():
    data = request.json
    session_id = data.get('session_id')
    cl = get_client(session_id)

    if cl is None:
        return jsonify({"status": "error", "message": "Session tidak ditemukan atau sudah expired!"}), 401

    media_url = data.get('url')
    caption = data.get('caption')

    try:
        temp_path = download_file_from_url(media_url)
        cl.photo_upload(path=temp_path, caption=caption)
        os.remove(temp_path)
        return jsonify({"status": "success", "message": "Post diupload!"}), 200
    except instagrapi.exceptions.MediaError:
        return jsonify({"status": "error", "message": "Media tidak diupload!"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# API Endpoint untuk Upload Reel
@app.route('/upload_reel', methods=['POST'])
def upload_reel():
    data = request.json
    session_id = data.get('session_id')
    cl = get_client(session_id)

    if cl is None:
        return jsonify({"status": "error", "message": "Session tidak ditemukan atau sudah expired!"}), 401

    media_url = data.get('url')
    caption = data.get('caption')

    try:
        temp_path = download_file_from_url(media_url)
        cl.clip_upload(path=temp_path, caption=caption)
        os.remove(temp_path)
        return jsonify({"status": "success", "message": "Reel diupload!"}), 200
    except instagrapi.exceptions.MediaError:
        return jsonify({"status": "error", "message": "Reel tidak diupload!"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=40000)

