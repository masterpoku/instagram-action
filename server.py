import threading
from flask import Flask, request, jsonify, session
from flask_session import Session
import instagrapi
import os
import requests
import tempfile
from PIL import Image
import time

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

def getdata(api_url):
    try:
        # Send GET request
        response = requests.get(api_url)

        # Check if the request was successful (HTTP status code 200)
        if response.status_code == 200:
            # Parse and return the response JSON data
            return response.json()
        else:
            # If the request was not successful, return the status code and reason
            return {"error": response.status_code, "message": response.reason}
    except requests.exceptions.RequestException as e:
        # Handle any exceptions that occur during the request
        return {"error": "Request failed", "message": str(e)}

def continuous_loop():
    """Fungsi untuk menjalankan loop secara kontinu."""
    api_url = "https://e33b-36-71-171-112.ngrok-free.app/slt/api.php?function=getLikerWithStatusZero&func=count"
    last_id = None

    while True:
        print("Fetching data from API")
        result = getdata(api_url)

        # Check for errors or empty data
        if 'error' in result or not result or 'id' not in result:
            print("No data loaded or error encountered. Skipping initial loop.")
            print("done")
            time.sleep(10)  # Wait for 10 seconds before retrying
            continue  # Continue to the next iteration of the loop

        # print(result)

        # Loop through each available session to like the media
        for session_id, cl in clients.items():
            print(f"Using session: {session_id}")

           
            try:
                media_id = cl.media_pk_from_url(result['url'])
                cl.media_like(media_id)
                print(f"Media liked successfully with session {session_id}: {result['url']}")
            except instagrapi.exceptions.MediaError:
                print(f"Error with media from Instagram: {result['url']}")
            except instagrapi.exceptions.MediaNotFound:
                print(f"Media not found: {result['url']}")
            except Exception as e:
                print(f"Error: {str(e)}")

            # Store the ID from the result
            if 'id' in result:
                last_id = result['id']

            # Optional: delay between requests to avoid spamming the server (e.g., wait 1 second)
            time.sleep(30)  # Wait for 1 second before the next request

        # Check if last_id is valid before making the update request
        if last_id:
            api_update = f"https://e33b-36-71-171-112.ngrok-free.app/slt/api.php?function=getLikerWithStatusZero&func=update&id={last_id}"
            print("\nMaking the update request...")
            update_result = getdata(api_update)

            # Check for errors in the update result
            if 'error' in update_result or not update_result:
                print("Error encountered during update request or no data to update.")
            else:
                print(update_result)

            # Reset the last_id after update
            last_id = None

        # Optional: delay between iterations to avoid overwhelming the server
        time.sleep(10)  # Wait for 10 seconds before the next iteration


if __name__ == '__main__':
    # Start the continuous loop in a separate thread
    loop_thread = threading.Thread(target=continuous_loop)
    loop_thread.daemon = True  # This ensures the loop thread will exit when the main program exits
    loop_thread.start()

    # Start the Flask app
    app.run(debug=True, port=40000)
