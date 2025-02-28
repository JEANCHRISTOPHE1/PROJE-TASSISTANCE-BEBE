# -*- coding: utf-8 -*-
from flask import Flask, Response, request, jsonify, send_file, send_from_directory
import io
import time
from PIL import Image
import pygame
from picamera2 import Picamera2

app = Flask(__name__)

picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (320, 240)},
    lores={"size": (320, 240)},
    display="lores"
)
picam2.configure(config)
picam2.start()

def generate_frames():
    while True:
        frame = picam2.capture_array()
        image = Image.fromarray(frame).convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        frame_bytes = buffer.getvalue()
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
        )
        time.sleep(0.2)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/style.css')
def send_css():
    return send_from_directory(".", "style.css")

pygame.init()
pygame.mixer.init()

# Dictionnaire des fichiers musicaux disponibles
music_files = {
    "Berceuse": "/home/pi/musique1.mp3",
    "Nature": "/home/pi/musique2.mp3",
    "Calme": "/home/pi/musique3.mp3"
}

@app.route('/play', methods=['POST'])
def play_music():
    track = request.form.get("track")
    if track in music_files:
        try:
            pygame.mixer.music.load(music_files[track])
            pygame.mixer.music.play()
            return jsonify({"status": "playing", "track": track})
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500
    else:
        return jsonify({"status": "error", "error": "Invalid track"}), 400

@app.route('/stop', methods=['POST'])
def stop_music():
    pygame.mixer.music.stop()
    return jsonify({"status": "stopped"})

@app.route('/')
def index():
    return send_file('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
