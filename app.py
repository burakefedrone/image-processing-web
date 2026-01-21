from flask import Flask, render_template_string
import cv2
import os

app = Flask(__name__)

VIDEO_INPUT = "static/videos/sample.mp4"
VIDEO_GRAY = "static/videos/video_gray.mp4"
VIDEO_EDGE = "static/videos/video_edge.mp4"

# ---------------- VIDEO PROCESSING ----------------
def process_video_grayscale():
    cap = cv2.VideoCapture(VIDEO_INPUT)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(VIDEO_GRAY, fourcc, fps, (w, h), isColor=False)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        out.write(gray)

    cap.release()
    out.release()

def process_video_edge():
    cap = cv2.VideoCapture(VIDEO_INPUT)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(VIDEO_EDGE, fourcc, fps, (w, h), isColor=False)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        out.write(edges)

    cap.release()
    out.release()

# ---------------- HTML ----------------
VIDEO_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Video Processing</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

<div class="container py-4">
    <h4 class="mb-3">Video Processing</h4>

    <video width="720" controls class="mb-3">
        <source src="/{{ video }}" type="video/mp4">
    </video>

    <div class="mb-3">
        <form method="get" action="/video/original" class="d-inline">
            <button class="btn btn-secondary">Original</button>
        </form>

        <form method="post" action="/video/gray" class="d-inline">
            <button class="btn btn-primary">Grayscale</button>
        </form>

        <form method="post" action="/video/edge" class="d-inline">
            <button class="btn btn-warning">Edge Detection</button>
        </form>
    </div>

    <a href="/" class="btn btn-outline-dark">Back</a>
</div>

</body>
</html>
"""

# ---------------- ROUTES ----------------
@app.route("/video")
def video():
    return render_template_string(VIDEO_HTML, video=VIDEO_INPUT)

@app.route("/video/original")
def video_original():
    return render_template_string(VIDEO_HTML, video=VIDEO_INPUT)

@app.route("/video/gray", methods=["POST"])
def video_gray():
    process_video_grayscale()
    return render_template_string(VIDEO_HTML, video=VIDEO_GRAY)

@app.route("/video/edge", methods=["POST"])
def video_edge():
    process_video_edge()
    return render_template_string(VIDEO_HTML, video=VIDEO_EDGE)

# ---------------- RUN ----------------
app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 5000)),
    debug=True
)
