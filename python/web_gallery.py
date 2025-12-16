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

def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

ip_addr = get_ip_address()
gallery_url = f"http://{ip_addr}:5000/gallery"
print(f"Server IP: {ip_addr}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mascot Gallery</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&display=swap" rel="stylesheet">
    <style>
        :root {
            --paper: #fdfbf7;
            --ink: #2b2b2b;
            --red: #d32f2f;
        }
        
        body {
            /* Corkboard Pattern */
            background-color: #5c4033;
            background-image: repeating-linear-gradient(45deg, #6b4c3e 25%, transparent 25%, transparent 75%, #6b4c3e 75%, #6b4c3e), repeating-linear-gradient(45deg, #6b4c3e 25%, #5c4033 25%, #5c4033 75%, #6b4c3e 75%, #6b4c3e);
            background-position: 0 0, 10px 10px;
            background-size: 20px 20px;
            
            color: var(--ink);
            font-family: 'Permanent Marker', cursive;
            margin: 0; padding: 10px; /* Reduced padding for mobile */
            min-height: 100vh;
        }

        h1 {
            font-size: 2.5em; /* Smaller base size */
            text-align: center;
            color: #ffeb3b; 
            text-shadow: 3px 3px 0px #000;
            margin-bottom: 5px;
            transform: rotate(-2deg);
        }
        
        .subtitle {
            text-align: center; color: #ddd; margin-bottom: 20px; font-size: 1.0em;
            text-shadow: 2px 2px 0px #000;
        }

        /* Controls Section - Sticker Style */
        .controls {
            display: flex; justify-content: center; gap: 10px; margin-bottom: 30px; flex-wrap: wrap;
        }
        
        .btn {
            background: #fff;
            border: 2px solid #000;
            color: #000;
            padding: 8px 15px; /* Smaller padding */
            cursor: pointer;
            font-family: 'Permanent Marker', cursive;
            font-size: 1.0em;
            transform: rotate(2deg);
            box-shadow: 2px 2px 0px rgba(0,0,0,0.5);
            transition: 0.2s;
            flex: 0 1 auto; /* Mobile friendly flex */
        }
        
        .btn:hover {
            transform: scale(1.1) rotate(0deg);
            background: #ffeb3b;
        }
        
        .btn.active {
            background: #00e5ff;
            transform: rotate(-3deg) scale(1.1);
            box-shadow: 4px 4px 0px #000;
        }

        /* Gallery Grid */
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); /* Smaller min width for mobile 2-col */
            gap: 20px;
            padding: 10px;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        @media (min-width: 600px) {
             .gallery { grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 40px; }
             h1 { font-size: 3.5em; }
             .btn { padding: 10px 25px; font-size: 1.2em; }
        }

        /* Polaroid Card */
        .photo-card {
            background: white;
            padding: 10px 10px 50px 10px;
            box-shadow: 5px 5px 10px rgba(0,0,0,0.4);
            transform: rotate(-1deg);
            transition: transform 0.3s;
            position: relative;
            text-align: center;
        }
        
        .photo-card:nth-child(even) { transform: rotate(1deg); }
        .photo-card:hover { 
            transform: scale(1.02); 
            z-index: 10; 
            box-shadow: 10px 10px 20px rgba(0,0,0,0.6);
        }
        
        /* Tape effect */
        .photo-card:before {
            content: '';
            position: absolute;
            top: -10px; left: 50%; transform: translateX(-50%);
            width: 60px; height: 25px;
            background: rgba(255,255,255,0.4);
            border-left: 1px dashed rgba(0,0,0,0.1);
            border-right: 1px dashed rgba(0,0,0,0.1);
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .photo-card img {
            width: 100%;
            height: auto;
            border: 1px solid #ddd;
            filter: contrast(110%); 
        }
        
        .caption {
            position: absolute;
            bottom: 25px; left: 0; right: 0;
            text-align: center;
            font-size: 1.0em;
            color: #555;
        }
        
        .actions {
            position: absolute;
            bottom: 5px; left: 0; right: 0;
            display: flex; justify-content: space-around;
            padding: 0 10px;
        }
        
        .action-link {
            text-decoration: none;
            font-size: 0.8em;
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 3px;
            font-family: sans-serif; /* Clean font for buttons */
        }
        
        .download-btn { color: #fff; background: #2196F3; }
        .delete-btn { color: #fff; background: var(--red); cursor: pointer; }
        
    </style>
    <script>
        function setFilter(mode) {
            fetch('/set_filter/' + mode)
            .then(response => response.json())
            .then(data => {
                document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
                document.getElementById('btn-' + mode).classList.add('active');
            });
        }
        
        function setMode(mode) {
            fetch('/set_mode/' + mode)
            .then(response => response.json())
            .then(data => {
                document.querySelectorAll('[id^=mode-]').forEach(b => b.classList.remove('active'));
                document.getElementById('mode-' + mode).classList.add('active');
            });
        }
        
        function deletePhoto(filename) {
            if(confirm("Confirm Delete?")) {
                fetch('/delete_photo/' + filename)
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
                // Check for deleted files (if we want to sync removal automatically, 
                // we'd need to check if DOM elements exist that are NOT in 'files')
                // For now, simpler to just add new ones.
                
                files.forEach(file => {
                    if(!knownFiles.has(file)) {
                        knownFiles.add(file);
                        const card = document.createElement('div');
                        card.className = 'photo-card';
                        card.id = 'card-' + file;
                        card.innerHTML = `
                            <img src="/photos/${file}">
                            <div class="caption">Mascot 2025</div>
                            <div class="actions">
                                <a href="/photos/${file}" download="MascotPolaroid.jpg" class="action-link download-btn">DOWNLOAD</a>
                                <span onclick="deletePhoto('${file}')" class="action-link delete-btn">DELETE</span>
                            </div>
                        `;
                        gallery.insertBefore(card, gallery.firstChild);
                    }
                });
            });
        }
        
        setInterval(loadGallery, 3000);
        window.onload = loadGallery;
    </script>
</head>
<body>
    <h1>MASCOT MEMORIES</h1>
    <div class="subtitle">Tech Fest 2k25</div>
    
    <div class="controls">
        <span style="width: 100%; text-align: center; color: #fff; text-shadow: 1px 1px 0 #000; margin-bottom: 5px;">FILTERS</span>
        <button id="btn-NORMAL" class="btn" onclick="setFilter('NORMAL')">Color</button>
        <button id="btn-BW" class="btn" onclick="setFilter('BW')">B&W</button>
        <button id="btn-VINTAGE" class="btn" onclick="setFilter('VINTAGE')">Sepia</button>
        <button id="btn-POLAROID" class="btn" onclick="setFilter('POLAROID')">Polaroid</button>
    </div>

    <div class="controls" style="margin-top: -15px;">
        <span style="width: 100%; text-align: center; color: #fff; text-shadow: 1px 1px 0 #000; margin-bottom: 5px;">MODE</span>
        <button id="mode-SINGLE" class="btn" onclick="setMode('SINGLE')">Single</button>
        <button id="mode-BURST" class="btn" onclick="setMode('BURST')">Burst</button>
        <button id="mode-GIF" class="btn" onclick="setMode('GIF')">GIF</button>
        <!-- <button id="mode-COUNTDOWN" class="btn" onclick="toggleCountdown()">Timer</button> -->
    </div>

    <div class="gallery" id="gallery-container">
    </div>

    <script>
        fetch('/get_filter').then(r=>r.json()).then(d => {
            if(d.filter) {
                let id = 'btn-' + d.filter;
                let el = document.getElementById(id);
                if(el) el.classList.add('active');
            }
        });
        
        fetch('/get_mode').then(r=>r.json()).then(d => {
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

@app.route("/gallery")
def gallery():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/photos")
def api_photos():
    if not os.path.exists(PHOTO_DIR): return jsonify([])
    files = sorted([f for f in os.listdir(PHOTO_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
                   key=lambda x: os.path.getmtime(os.path.join(PHOTO_DIR, x)))
    return jsonify(files) 

@app.route("/photos/<path:filename>")
def photos(filename):
    return send_from_directory(PHOTO_DIR, filename)

@app.route("/delete_photo/<path:filename>")
def delete_photo(filename):
    try:
        path = os.path.join(PHOTO_DIR, filename)
        if os.path.exists(path):
            os.remove(path)
            return jsonify({"status": "ok"})
    except:
        pass
    return jsonify({"status": "error"})

@app.route("/set_filter/<mode>")
def set_filter(mode):
    global current_filter
    if mode in ["NORMAL", "CARTOON", "VINTAGE", "BW", "POLAROID"]:
        current_filter = mode
    return jsonify({"status": "ok", "filter": current_filter})

@app.route("/get_filter")
def get_filter():
    return jsonify({"filter": current_filter})

# Global State for Capture Mode
current_mode = "SINGLE"

@app.route("/set_mode/<mode>")
def set_mode(mode):
    global current_mode
    if mode in ["SINGLE", "BURST", "GIF"]:
        current_mode = mode
    return jsonify({"status": "ok", "mode": current_mode})

@app.route("/get_mode")
def get_mode():
    return jsonify({"mode": current_mode})

def run_server(port=5000):
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def start_gallery_thread():
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    return t
