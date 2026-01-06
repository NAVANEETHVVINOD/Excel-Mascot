import os
import glob
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# CONFIGURATION
PHOTO_DIR = r"E:\mascot"

# Ensure directory exists
os.makedirs(PHOTO_DIR, exist_ok=True)

@app.route('/api/photos', methods=['GET'])
def get_photos():
    """Return a list of photo filenames sorted by newest first."""
    # Pattern to match image files
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif']
    files = []
    
    for ext in extensions:
        files.extend(glob.glob(os.path.join(PHOTO_DIR, ext)))
        
    # Sort files by modification time (newest first)
    files.sort(key=os.path.getmtime, reverse=True)
    
    # Extract just the filenames
    photo_list = []
    for f in files:
        filename = os.path.basename(f)
        # Create a simple object structure compatible with what the frontend expects
        photo_list.append({
            'id': filename,
            'url': f"http://localhost:5000/photos/{filename}",
            'name': filename,
            'created_at': os.path.getmtime(f)
        })
        
    return jsonify(photo_list)

@app.route('/photos/<path:filename>')
def serve_photo(filename):
    """Serve the actual image file."""
    return send_from_directory(PHOTO_DIR, filename)

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "Mascot Local Server Running", "photos_dir": PHOTO_DIR})

if __name__ == '__main__':
    print(f"Starting Mascot Local Server on port 5000...")
    print(f"Serving photos from: {PHOTO_DIR}")
    app.run(host='0.0.0.0', port=5000, debug=False)
