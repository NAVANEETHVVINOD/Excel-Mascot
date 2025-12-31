from flask import Flask, send_from_directory, render_template_string, request, jsonify
import os
import threading
import socket

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTO_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "photos"))
STATIC_DIR = os.path.join(BASE_DIR, "static")
if not os.path.exists(STATIC_DIR): os.makedirs(STATIC_DIR)

# Global State for Filter
current_filter = "NORMAL"
current_mode = "SINGLE"

def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

ip_addr = get_ip_address()
gallery_url = f"http://{ip_addr}:5000/gallery"
print(f"Server IP: {ip_addr}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mascot Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #050505;
            --grid: #1a1a1a;
            --primary: #FFD700; /* Gold */
            --secondary: #FF8C00; /* Orange */
            --accent: #00f3ff; /* Cyan */
            --text: #e0e0e0;
            --surface: #0a0a0a;
            --border: #333;
        }
        
        body {
            /* Tech Grid Background */
            background-color: var(--bg);
            background-image: 
                linear-gradient(var(--grid) 1px, transparent 1px),
                linear-gradient(90deg, var(--grid) 1px, transparent 1px);
            background-size: 30px 30px;
            color: var(--text);
            font-family: 'Share Tech Mono', monospace;
            padding: 20px;
            text-align: center;
        }

        h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.5em;
            color: white;
            text-transform: uppercase;
            letter-spacing: 4px;
            margin-bottom: 5px;
            text-shadow: 2px 2px 0px var(--secondary);
        }

        .subtitle {
            color: var(--primary);
            font-size: 1.0em;
            margin-bottom: 30px;
            letter-spacing: 2px;
            text-transform: uppercase;
        }

        /* Controls Section - Tech Panel */
        .controls {
            display: flex; justify-content: center; gap: 10px; margin-bottom: 30px; flex-wrap: wrap;
            background: rgba(10, 10, 10, 0.8);
            border: 1px solid var(--border);
            border-left: 4px solid var(--primary);
            padding: 20px;
            backdrop-filter: blur(5px);
            max-width: 800px;
            margin: 0 auto 40px auto;
        }
        
        .panel-label {
            width: 100%; text-align: left; color: #666; font-size: 0.8em; margin-bottom: 10px; border-bottom: 1px solid #222;
        }

        .btn {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text);
            padding: 10px 20px;
            cursor: pointer;
            font-family: 'Share Tech Mono', monospace;
            text-transform: uppercase;
            transition: all 0.2s;
            position: relative;
        }

        .btn:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--primary);
            color: var(--primary);
            box-shadow: 0 0 10px rgba(255, 215, 0, 0.2);
        }

        .btn.active {
            background: var(--primary);
            color: black;
            border-color: var(--primary);
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
            font-weight: bold;
        }

        /* Gallery Grid */
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }

        /* Tech Card */
        .tech-card {
            background: rgba(20, 20, 20, 0.9);
            border: 1px solid #333;
            padding: 10px;
            position: relative;
            transition: transform 0.3s;
        }
        
        .tech-card:hover { border-color: var(--accent); transform: translateY(-5px); }

        .image-frame {
            background: #000;
            width: 100%;
            aspect-ratio: 1;
            overflow: hidden;
            border: 1px solid #222;
            margin-bottom: 10px;
        }

        .image-frame img {
            width: 100%; height: 100%; object-fit: cover;
        }
        
        .card-info {
            font-size: 0.8em; color: #666; display: flex; justify-content: space-between; margin-bottom: 5px;
        }
        
        .actions {
            display: flex; justify-content: space-between; gap: 10px;
        }
        
        .action-link {
            flex: 1;
            text-decoration: none;
            padding: 5px;
            font-size: 0.8em;
            text-transform: uppercase;
            border: 1px solid #333;
            color: #aaa;
            transition: 0.2s;
        }
        
        .download-btn:hover { background: var(--accent); color: black; border-color: var(--accent); }
        .delete-btn:hover { background: #d32f2f; color: white; border-color: #d32f2f; }
        
    </style>
    <script>
        function setFilter(mode) {
            fetch('/set_filter/' + mode)
            .then(response => response.json())
            .then(data => {
                console.log(data); 
                document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
                document.getElementById('btn-' + mode).classList.add('active');
            });
        }
        
        function setMode(mode) {
            fetch('/set_mode/' + mode)
            .then(response => response.json())
            .then(data => {
                console.log(data); 
                document.querySelectorAll('.btn-mode').forEach(b => b.classList.remove('active'));
                document.getElementById('mode-' + mode).classList.add('active');
            });
        }

        function deletePhoto(filename) {
            if(confirm("Confirm deletion?")) {
                fetch('/delete/' + filename)
                .then(r => r.json())
                .then(d => {
                    if(d.status === 'ok') {
                        document.getElementById('card-' + filename).remove();
                    }
                });
            }
        }
        
        let knownFiles = new Set();
        
        function loadGallery() {
            fetch('/api/photos')
            .then(r => r.json())
            .then(files => {
                const gallery = document.getElementById('gallery-container');
                
                // Remove deleted
                // Simplified: Just reload all for now or optimize later. 
                // For now, let's keep it simple: clear and rebuild or just prepend new?
                // The original code prepended. Let's simple check.
                
                files.reverse().forEach(file => {
                     if (!knownFiles.has(file)) {
                        knownFiles.add(file);
                        
                        const card = document.createElement('div');
                        card.className = 'tech-card';
                        card.id = 'card-' + file;
                        card.innerHTML = `
                            <div class="card-info">
                                <span>IMG_LOG</span>
                                <span>DATA</span>
                            </div>
                            <div class="image-frame">
                                <img src="/photos/${file}" loading="lazy">
                            </div>
                            <div class="actions">
                                <a href="/photos/${file}" download class="action-link download-btn">DOWN</a>
                                <div onclick="deletePhoto('${file}')" class="action-link delete-btn" style="cursor: pointer;">DEL</div>
                            </div>
                        `;
                        // Prepend
                        if(gallery.firstChild) {
                             gallery.insertBefore(card, gallery.firstChild);
                        } else {
                             gallery.appendChild(card);
                        }
                    }
                });
            });
        }
        
        setInterval(loadGallery, 3000);
        window.onload = loadGallery;
    </script>
</head>
<body>
    <h1>MASCOT CONTROL</h1>
    <div class="subtitle">EXCEL TECHFEST 2025 // SYSTEM V2.0</div>
    
    <div class="controls">
        <div class="panel-label">/// FILTERS_MODULE</div>
        <!-- Filter Buttons -->
        <!-- These IDs match Python var naming usually -->
        <button id="btn-NORMAL" class="btn btn-filter" onclick="setFilter('NORMAL')">RESET</button>
        <button id="btn-GLITCH" class="btn btn-filter" onclick="setFilter('GLITCH')">GLITCH</button>
        <button id="btn-CYBERPUNK" class="btn btn-filter" onclick="setFilter('CYBERPUNK')">NEON</button>
        <button id="btn-PASTEL" class="btn btn-filter" onclick="setFilter('PASTEL')">DREAMY</button>
        <button id="btn-BW" class="btn btn-filter" onclick="setFilter('BW')">NOIR</button>
        <button id="btn-POLAROID" class="btn btn-filter" onclick="setFilter('POLAROID')">RETRO</button>
    </div>
    
    <div class="controls">
         <div class="panel-label">/// CAPTURE_MODE</div>
        <button id="mode-SINGLE" class="btn btn-mode" onclick="setMode('SINGLE')">[ SINGLE ]</button>
        <button id="mode-BURST" class="btn btn-mode" onclick="setMode('BURST')">[ BURST ]</button>
        <button id="mode-GIF" class="btn btn-mode" onclick="setMode('GIF')">[ GIF ]</button>
    </div>

    <div class="gallery" id="gallery-container">
    </div>

    <script>
        // Init active state
        fetch('/get_filter').then(r=>r.json()).then(d => {
            if(d.filter) {
                let id = 'btn-' + d.filter;
                let el = document.getElementById(id);
                if(el) el.classList.add('active');
            }
            if(d.mode) {
                let id = 'mode-' + d.mode;
                let el = document.getElementById(id);
                if(el) el.classList.add('active');
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def gallery():
    return render_template_string(HTML_TEMPLATE)

@app.route('/gallery')
def gallery_view():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/photos')
def api_photos():
    files = [f for f in os.listdir(PHOTO_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    # Sort by modification time
    files.sort(key=lambda x: os.path.getmtime(os.path.join(PHOTO_DIR, x)))
    return jsonify(files)

@app.route('/photos/<path:filename>')
def photos(filename):
    return send_from_directory(PHOTO_DIR, filename)

@app.route('/set_filter/<mode>')
def set_filter(mode):
    global current_filter
    current_filter = mode
    print(f"Filter set to: {mode}")
    return jsonify({"status": "ok", "filter": mode})

@app.route('/set_mode/<mode>')
def set_mode_route(mode):
    global current_mode
    current_mode = mode
    print(f"Mode set to: {mode}")
    return jsonify({"status": "ok", "mode": mode})

@app.route('/get_filter')
def get_filter():
    return jsonify({"filter": current_filter, "mode": current_mode})

@app.route('/delete/<filename>')
def delete_file(filename):
    try:
        os.remove(os.path.join(PHOTO_DIR, filename))
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def start_gallery_server():
    # Run on 0.0.0.0 to be accessible
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def start_gallery_thread():
    t = threading.Thread(target=start_gallery_server, daemon=True)
    t.start()
