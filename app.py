import os
import cv2
from flask import Flask, render_template, request, url_for

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def process_video(filter_type):
    input_path = os.path.join(UPLOAD_FOLDER, 'input.mp4')
    output_path = os.path.join(UPLOAD_FOLDER, f'output_{filter_type}.mp4')
    
    cap = cv2.VideoCapture(input_path)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS)
    
    # mp4v tarayıcılar için en uyumlu genel codec'tir
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        if filter_type == 'grayscale':
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif filter_type == 'edge':
            edges = cv2.Canny(frame, 100, 200)
            frame = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        out.write(frame)
        
    cap.release()
    out.release()
    return f'uploads/output_{filter_type}.mp4'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process/<filter_type>')
def process(filter_type):
    video_url = process_video(filter_type)
    return render_template('index.html', video_url=video_url)

if __name__ == '__main__':
    app.run(debug=True)
