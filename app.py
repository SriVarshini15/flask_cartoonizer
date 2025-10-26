import os
import io
import uuid
import sys
import yaml
import logging
import traceback

from flask import Flask, render_template, flash, request
from PIL import Image
from werkzeug.utils import secure_filename
import numpy as np
import cv2

# Load config
with open('config.yaml', 'r') as f:
    opts = yaml.safe_load(f)

# Import cartoonizer
sys.path.insert(0, './white_box_cartoonizer/')
from cartoonize import WB_Cartoonize

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Folder setup
app.config['UPLOAD_FOLDER_VIDEOS'] = 'static/uploaded_videos'
app.config['CARTOONIZED_FOLDER'] = 'static/cartoonized_videos'
os.makedirs(app.config['UPLOAD_FOLDER_VIDEOS'], exist_ok=True)
os.makedirs(app.config['CARTOONIZED_FOLDER'], exist_ok=True)

# Initialize cartoonizer
wb_cartoonizer = WB_Cartoonize(os.path.abspath("white_box_cartoonizer/saved_models/"), opts['gpu'])

# Logging setup
logging.basicConfig(level=logging.DEBUG)

def convert_bytes_to_image(img_bytes):
    pil_image = Image.open(io.BytesIO(img_bytes))
    if pil_image.mode == "RGBA":
        background = Image.new("RGB", pil_image.size, (255, 255, 255))
        background.paste(pil_image, mask=pil_image.split()[3])
        image = background
    else:
        image = pil_image.convert('RGB')
    return np.array(image)

@app.route('/')
def home():
    return render_template("index_cartoonized.html")

@app.route('/cartoonize_image', methods=["POST"])
def cartoonize_image():
    try:
        file = request.files.get('image')
        if not file or file.filename.strip() == '':
            flash("No image file selected")
            return render_template("index_cartoonized.html")

        image = convert_bytes_to_image(file.read())
        filename = secure_filename(f"{uuid.uuid4()}.jpg")
        output_path = os.path.join(app.config['CARTOONIZED_FOLDER'], filename)

        cartoon_image = wb_cartoonizer.infer(image)
        cv2.imwrite(output_path, cv2.cvtColor(cartoon_image, cv2.COLOR_RGB2BGR))

        return render_template("index_cartoonized.html", cartoonized_image=output_path)

    except Exception:
        logging.error("Image cartoonization error:\n%s", traceback.format_exc())
        flash("Failed to cartoonize image.")
        return render_template("index_cartoonized.html")

@app.route('/cartoonize_video', methods=["POST"])
def cartoonize_video():
    try:
        video_file = request.files.get('video')
        if not video_file or video_file.filename.strip() == '':
            flash("No video file selected")
            return render_template("index_cartoonized.html")

        base_filename = str(uuid.uuid4())
        original_path = os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], f"{base_filename}.mp4")
        resized_path = os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], f"{base_filename}_resized.mp4")
        audio_path = os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], f"{base_filename}_audio.aac")
        final_output_path = os.path.join(app.config['CARTOONIZED_FOLDER'], f"{base_filename}_final.mp4")

        video_file.save(original_path)

        resize_width = opts.get("resize-dim", 720)
        frame_rate = opts.get("output_frame_rate", "24/1").split('/')[0]
        trim_time = opts.get("trim-video-length", 15) if opts.get("trim-video", True) else None

        trim_cmd = f"-t {trim_time}" if trim_time else ""
        os.system(f"ffmpeg -hide_banner -loglevel error -ss 0 -i \"{original_path}\" {trim_cmd} "
                  f"-vf scale={resize_width}:-2 -r {frame_rate} -c:v libx264 -preset veryfast -y \"{resized_path}\"")

        os.system(f"ffmpeg -hide_banner -loglevel error -i \"{resized_path}\" -vn -acodec copy -y \"{audio_path}\"")

        cartoonized_output = wb_cartoonizer.process_video(resized_path, frame_rate)

        if not cartoonized_output or not os.path.exists(cartoonized_output):
            logging.error("Cartoonized video not created or file missing: %s", cartoonized_output)
            flash("Failed to cartoonize video.")
            return render_template("index_cartoonized.html")

        os.system(f"ffmpeg -hide_banner -loglevel error -i \"{cartoonized_output}\" -i \"{audio_path}\" "
                  f"-c:v copy -c:a aac -strict experimental -shortest -y \"{final_output_path}\"")

        for path in [original_path, resized_path, audio_path, cartoonized_output]:
            if os.path.exists(path):
                os.remove(path)

        return render_template("index_cartoonized.html", cartoonized_video=final_output_path)

    except Exception:
        logging.error("Video cartoonization error:\n%s", traceback.format_exc())
        flash("Failed to cartoonize video.")
        return render_template("index_cartoonized.html")

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8080)
