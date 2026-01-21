from flask import Flask, render_template_string, request
import cv2
import numpy as np
import os

app = Flask(__name__)

IMAGES = {
    "drone": "static/images/drone.jpg",
    "nature": "static/images/nature.jpg",
    "forest": "static/images/forest.jpg"
}

current_image = "drone"

def out_path(name):
    return f"static/images/out_{name}.jpg"

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Web-Based Image Manipulation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .group-title {
            color: #4a90e2;
            font-size: 0.85rem;
            font-weight: 600;
        }
    </style>
</head>
<body class="bg-light">

<div class="container-fluid py-3">
    <h3 class="text-center mb-4">Web-Based Image Manipulation</h3>

    <div class="row">

        <div class="col-md-3">
            <div class="card p-3 shadow-sm mb-3">
                <h6 class="mb-2">Select Image</h6>

                <form method="post" action="/select" class="mb-1">
                    <input type="hidden" name="img" value="drone">
                    <button class="btn btn-outline-primary w-100">Drone</button>
                </form>

                <form method="post" action="/select" class="mb-1">
                    <input type="hidden" name="img" value="nature">
                    <button class="btn btn-outline-success w-100">Nature</button>
                </form>

                <form method="post" action="/select">
                    <input type="hidden" name="img" value="forest">
                    <button class="btn btn-outline-dark w-100">Forest</button>
                </form>
            </div>

            <div class="card p-3 shadow-sm">
                <h6 class="mb-2">Manipulations</h6>

                <div class="group-title">Basic Operations</div>
                <form method="post" action="/gray"><button class="btn btn-primary w-100 btn-sm mb-1">Grayscale</button></form>
                <form method="post" action="/blur"><button class="btn btn-primary w-100 btn-sm mb-1">Blur</button></form>
                <form method="post" action="/thresh"><button class="btn btn-primary w-100 btn-sm mb-2">Threshold</button></form>

                <div class="group-title">Edge / Feature</div>
                <form method="post" action="/edge"><button class="btn btn-primary w-100 btn-sm mb-2">Edge Detection</button></form>

                <div class="group-title">Geometric</div>
                <form method="post" action="/resize"><button class="btn btn-secondary w-100 btn-sm mb-1">Resize</button></form>
                <form method="post" action="/rotate"><button class="btn btn-secondary w-100 btn-sm mb-2">Rotate</button></form>

                <div class="group-title">Enhancement</div>
                <form method="post" action="/bright"><button class="btn btn-warning w-100 btn-sm mb-1">Brightness</button></form>
                <form method="post" action="/noise"><button class="btn btn-warning w-100 btn-sm mb-1">Noise</button></form>
                <form method="post" action="/sharp"><button class="btn btn-warning w-100 btn-sm">Sharpen</button></form>
            </div>
        </div>

        <div class="col-md-9 d-flex align-items-center justify-content-center">
            <img src="/{{ image }}" class="img-fluid rounded shadow" style="max-height:600px;">
        </div>

    </div>
</div>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML, image=IMAGES[current_image])

@app.route("/select", methods=["POST"])
def select():
    global current_image
    current_image = request.form["img"]
    return render_template_string(HTML, image=IMAGES[current_image])

def process(func, name):
    img = cv2.imread(IMAGES[current_image])
    out = func(img)
    path = out_path(name)
    cv2.imwrite(path, out)
    return render_template_string(HTML, image=path)

@app.route("/gray", methods=["POST"])
def gray():
    return process(lambda i: cv2.cvtColor(i, cv2.COLOR_BGR2GRAY), "gray")

@app.route("/blur", methods=["POST"])
def blur():
    return process(lambda i: cv2.GaussianBlur(i, (15,15), 0), "blur")

@app.route("/edge", methods=["POST"])
def edge():
    g = cv2.cvtColor(cv2.imread(IMAGES[current_image]), cv2.COLOR_BGR2GRAY)
    out = cv2.Canny(g, 100, 200)
    path = out_path("edge")
    cv2.imwrite(path, out)
    return render_template_string(HTML, image=path)

@app.route("/thresh", methods=["POST"])
def thresh():
    g = cv2.cvtColor(cv2.imread(IMAGES[current_image]), cv2.COLOR_BGR2GRAY)
    _, out = cv2.threshold(g, 127, 255, cv2.THRESH_BINARY)
    path = out_path("thresh")
    cv2.imwrite(path, out)
    return render_template_string(HTML, image=path)

@app.route("/resize", methods=["POST"])
def resize():
    return process(lambda i: cv2.resize(i, (300,300)), "resize")

@app.route("/rotate", methods=["POST"])
def rotate():
    img = cv2.imread(IMAGES[current_image])
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w//2, h//2), 45, 1)
    out = cv2.warpAffine(img, M, (w, h))
    path = out_path("rotate")
    cv2.imwrite(path, out)
    return render_template_string(HTML, image=path)

@app.route("/bright", methods=["POST"])
def bright():
    return process(lambda i: cv2.convertScaleAbs(i, alpha=1.2, beta=40), "bright")

@app.route("/noise", methods=["POST"])
def noise():
    img = cv2.imread(IMAGES[current_image])
    n = np.random.normal(0, 25, img.shape).astype(np.uint8)
    out = cv2.add(img, n)
    path = out_path("noise")
    cv2.imwrite(path, out)
    return render_template_string(HTML, image=path)

@app.route("/sharp", methods=["POST"])
def sharp():
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    return process(lambda i: cv2.filter2D(i, -1, kernel), "sharp")

app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 5000)),
    debug=True
)
