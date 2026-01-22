from flask import Flask, render_template_string, request, redirect
import cv2
import numpy as np
import sqlite3
import os, time

app = Flask(__name__)

# ---------------- PATHS ----------------
IMAGES = {
    "drone": "static/images/drone.jpg",
    "nature": "static/images/nature.jpg",
    "forest": "static/images/forest.jpg"
}

VIDEO_INPUT = "static/videos/sample.mp4"
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

def log_operation(img, op):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO operations (image_name, operation) VALUES (?, ?)",
        (img, op)
    )
    conn.commit()
    conn.close()

def get_recent_operations():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT image_name, operation, timestamp FROM operations ORDER BY id DESC LIMIT 5"
    )
    rows = c.fetchall()
    conn.close()
    return rows

# ---------------- IMAGE PROCESS ----------------
def out_path(name):
    return f"static/images/out_{name}.jpg"

def process_image(img, name):
    path = out_path(name)
    cv2.imwrite(path, img)
    log_operation(current_image, name)
    return path

# ---------------- VIDEO PROCESS (CACHE FIX) ----------------
def video_out(name):
    ts = int(time.time())
    return f"static/videos/{name}_{ts}.mp4"

def process_video_gray():
    outp = video_out("video_gray")
    cap = cv2.VideoCapture(VIDEO_INPUT)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(outp, fourcc, fps, (w, h), False)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        out.write(gray)

    cap.release()
    out.release()
    return outp

def process_video_edge():
    outp = video_out("video_edge")
    cap = cv2.VideoCapture(VIDEO_INPUT)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(outp, fourcc, fps, (w, h), False)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray,100,200)
        out.write(edges)

    cap.release()
    out.release()
    return outp

# ---------------- HTML ----------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Web-Based Image & Video Processing</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

<div class="container-fluid p-3">
<h3 class="fw-bold">Web-Based Image & Video Processing</h3>

<div class="row mt-3">

<div class="col-md-4">

<form method="post" action="/select">
<button class="btn btn-outline-primary w-100 mb-1" name="img" value="drone">Drone</button>
<button class="btn btn-outline-success w-100 mb-1" name="img" value="nature">Nature</button>
<button class="btn btn-outline-dark w-100 mb-3" name="img" value="forest">Forest</button>
</form>

<form method="post" action="/gray"><button class="btn btn-primary w-100 mb-1">Grayscale</button></form>
<form method="post" action="/blur"><button class="btn btn-primary w-100 mb-1">Blur</button></form>
<form method="post" action="/thresh"><button class="btn btn-primary w-100 mb-1">Threshold</button></form>
<form method="post" action="/edge"><button class="btn btn-primary w-100 mb-1">Edge</button></form>

<form method="post" action="/resize"><button class="btn btn-secondary w-100 mb-1">Resize</button></form>
<form method="post" action="/rotate"><button class="btn btn-secondary w-100 mb-1">Rotate</button></form>

<form method="post" action="/bright"><button class="btn btn-warning w-100 mb-1">Brightness</button></form>
<form method="post" action="/noise"><button class="btn btn-warning w-100 mb-1">Noise</button></form>
<form method="post" action="/sharp"><button class="btn btn-warning w-100 mb-2">Sharpen</button></form>

<a href="/video" class="btn btn-dark w-100">Go to Video Processing</a>

<hr>
<b>Recent Operations</b>
{% for i,o,t in recent %}
<div style="font-size:13px">{{i}} → {{o}} <small>{{t}}</small></div>
{% endfor %}

</div>

<div class="col-md-8 text-center">
<img src="/{{ image }}" class="img-fluid shadow rounded" style="max-height:550px;">
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

<div class="container p-4">
<h3 class="fw-bold">Video Processing</h3>

<video width="640" controls class="shadow rounded mb-3">
<source src="/{{ video }}" type="video/mp4">
</video>

<form method="post" action="/video/original"><button class="btn btn-secondary">Original</button></form>
<form method="post" action="/video/gray"><button class="btn btn-primary">Grayscale</button></form>
<form method="post" action="/video/edge"><button class="btn btn-dark">Edge Detection</button></form>

<a href="/" class="btn btn-outline-secondary mt-3">Back to Image</a>
</div>

</body>
</html>
"""

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template_string(
        HTML,
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
    img = cv2.imread(IMAGES[current_image])
    out = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return render_template_string(HTML, image=process_image(out,"grayscale"), recent=get_recent_operations())

@app.route("/blur", methods=["POST"])
def blur():
    img = cv2.imread(IMAGES[current_image])
    out = cv2.GaussianBlur(img,(15,15),0)
    return render_template_string(HTML, image=process_image(out,"blur"), recent=get_recent_operations())

@app.route("/thresh", methods=["POST"])
def thresh():
    img = cv2.imread(IMAGES[current_image],0)
    _, out = cv2.threshold(img,127,255,cv2.THRESH_BINARY)
    return render_template_string(HTML, image=process_image(out,"threshold"), recent=get_recent_operations())

@app.route("/edge", methods=["POST"])
def edge():
    img = cv2.imread(IMAGES[current_image],0)
    out = cv2.Canny(img,100,200)
    return render_template_string(HTML, image=process_image(out,"edge"), recent=get_recent_operations())

@app.route("/resize", methods=["POST"])
def resize():
    img = cv2.imread(IMAGES[current_image])
    out = cv2.resize(img,(200,200))
    return render_template_string(HTML, image=process_image(out,"resize"), recent=get_recent_operations())

@app.route("/rotate", methods=["POST"])
def rotate():
    img = cv2.imread(IMAGES[current_image])
    h,w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w//2,h//2),45,1)
    out = cv2.warpAffine(img,M,(w,h))
    return render_template_string(HTML, image=process_image(out,"rotate"), recent=get_recent_operations())

@app.route("/bright", methods=["POST"])
def bright():
    img = cv2.imread(IMAGES[current_image])
    out = cv2.convertScaleAbs(img,1.2,40)
    return render_template_string(HTML, image=process_image(out,"brightness"), recent=get_recent_operations())

@app.route("/noise", methods=["POST"])
def noise():
    img = cv2.imread(IMAGES[current_image])
    n = np.random.normal(0,25,img.shape).astype(np.uint8)
    out = cv2.add(img,n)
    return render_template_string(HTML, image=process_image(out,"noise"), recent=get_recent_operations())

@app.route("/sharp", methods=["POST"])
def sharp():
    img = cv2.imread(IMAGES[current_image])
    k = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    out = cv2.filter2D(img,-1,k)
    return render_template_string(HTML, image=process_image(out,"sharpen"), recent=get_recent_operations())

@app.route("/video")
def video():
    return render_template_string(VIDEO_HTML, video=VIDEO_INPUT)

@app.route("/video/original", methods=["POST"])
def video_original():
    return render_template_string(VIDEO_HTML, video=VIDEO_INPUT)

@app.route("/video/gray", methods=["POST"])
def video_gray():
    path = process_video_gray()
    return render_template_string(VIDEO_HTML, video=path)

@app.route("/video/edge", methods=["POST"])
def video_edge():
    path = process_video_edge()
    return render_template_string(VIDEO_HTML, video=path)

init_db()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=True)
