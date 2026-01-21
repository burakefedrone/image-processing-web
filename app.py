from flask import Flask, render_template_string, request, redirect
import cv2
import numpy as np
import os
import sqlite3

app = Flask(__name__)

# ---------------- PATHS ----------------
IMAGES = {
    "drone": "static/images/drone.jpg",
    "nature": "static/images/nature.jpg",
    "forest": "static/images/forest.jpg"
}

VIDEO_INPUT = "static/videos/sample.mp4"
VIDEO_GRAY = "static/videos/video_gray.mp4"
VIDEO_EDGE = "static/videos/video_edge.mp4"

DB_PATH = "database.db"
current_image = "drone"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS operations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_name TEXT,
        operation TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def log_operation(image_name, operation):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO operations (image_name, operation) VALUES (?, ?)",
        (image_name, operation)
    )
    conn.commit()
    conn.close()

def get_recent_operations(limit=5):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT image_name, operation, timestamp FROM operations ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = c.fetchall()
    conn.close()
    return rows

# ---------------- IMAGE PROCESS ----------------
def out_path(name):
    return f"static/images/out_{name}.jpg"

def process_image(func, name):
    img = cv2.imread(IMAGES[current_image])
    out = func(img)
    path = out_path(name)
    cv2.imwrite(path, out)
    log_operation(current_image, name)
    return path

# ---------------- VIDEO PROCESS ----------------
def process_video_gray():
    cap = cv2.VideoCapture(VIDEO_INPUT)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(VIDEO_GRAY, fourcc, fps, (w, h), False)

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
    out = cv2.VideoWriter(VIDEO_EDGE, fourcc, fps, (w, h), False)

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
MAIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Image Processing</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container-fluid py-3">
<h4>Image Processing Dashboard</h4>
<div class="row">
<div class="col-md-3">
<form method="post" action="/select">
<button class="btn btn-outline-primary w-100 mb-1" name="img" value="drone">Drone</button>
<button class="btn btn-outline-success w-100 mb-1" name="img" value="nature">Nature</button>
<button class="btn btn-outline-dark w-100 mb-3" name="img" value="forest">Forest</button>
</form>

<form method="post" action="/gray"><button class="btn btn-primary w-100 mb-1">Grayscale</button></form>
<form method="post" action="/blur"><button class="btn btn-primary w-100 mb-1">Blur</button></form>
<form method="post" action="/edge"><button class="btn btn-primary w-100 mb-1">Edge</button></form>
<form method="post" action="/bright"><button class="btn btn-warning w-100 mb-1">Brightness</button></form>
<form method="post" action="/sharp"><button class="btn btn-warning w-100 mb-3">Sharpen</button></form>

<a href="/video" class="btn btn-secondary w-100">Go to Video</a>

<hr>
<b>Recent Operations</b>
{% for i,o,t in recent %}
<div style="font-size:12px">{{i}} → {{o}}<br><small>{{t}}</small></div>
{% endfor %}
</div>

<div class="col-md-9 text-center">
<img src="/{{ image }}" class="img-fluid shadow rounded" style="max-height:600px;">
</div>
</div>
</div>
</body>
</html>
"""

VIDEO_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Video Processing</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-4">
<h4>Video Processing</h4>

<video width="720" controls class="mb-3">
<source src="/{{ video }}" type="video/mp4">
</video>

<form method="get" action="/video"><button class="btn btn-secondary">Original</button></form>
<form method="post" action="/video/gray"><button class="btn btn-primary">Grayscale</button></form>
<form method="post" action="/video/edge"><button class="btn btn-warning">Edge</button></form>

<a href="/" class="btn btn-outline-dark mt-3">Back</a>
</div>
</body>
</html>
"""

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template_string(
        MAIN_HTML,
        image=IMAGES[current_image],
        recent=get_recent_operations()
    )

@app.route("/select", methods=["POST"])
def select():
    global current_image
    current_image = request.form["img"]
    return redirect("/")

@app.route("/gray", methods=["POST"])
def gray():
    return render_template_string(MAIN_HTML,
        image=process_image(lambda i: cv2.cvtColor(i, cv2.COLOR_BGR2GRAY), "grayscale"),
        recent=get_recent_operations()
    )

@app.route("/blur", methods=["POST"])
def blur():
    return render_template_string(MAIN_HTML,
        image=process_image(lambda i: cv2.GaussianBlur(i,(15,15),0), "blur"),
        recent=get_recent_operations()
    )

@app.route("/edge", methods=["POST"])
def edge():
    img = cv2.imread(IMAGES[current_image])
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    out = cv2.Canny(g,100,200)
    path = out_path("edge")
    cv2.imwrite(path,out)
    log_operation(current_image,"edge")
    return render_template_string(MAIN_HTML, image=path, recent=get_recent_operations())

@app.route("/bright", methods=["POST"])
def bright():
    return render_template_string(MAIN_HTML,
        image=process_image(lambda i: cv2.convertScaleAbs(i,1.2,40), "brightness"),
        recent=get_recent_operations()
    )

@app.route("/sharp", methods=["POST"])
def sharp():
    k = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    return render_template_string(MAIN_HTML,
        image=process_image(lambda i: cv2.filter2D(i,-1,k), "sharpen"),
        recent=get_recent_operations()
    )

@app.route("/video")
def video():
    return render_template_string(VIDEO_HTML, video=VIDEO_INPUT)

@app.route("/video/gray", methods=["POST"])
def video_gray():
    process_video_gray()
    return render_template_string(VIDEO_HTML, video=VIDEO_GRAY)

@app.route("/video/edge", methods=["POST"])
def video_edge():
    process_video_edge()
    return render_template_string(VIDEO_HTML, video=VIDEO_EDGE)

# ---------------- INIT + RUN ----------------
init_db()

app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=True)
