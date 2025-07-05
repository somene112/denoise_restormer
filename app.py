from flask import Flask, request, render_template
from pdf2image import convert_from_bytes
from PIL import Image
import os
import time
import img2pdf
import requests
from restormer_model import load_restormer_model, denoise_image
import gc
import torch

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
UPLOAD_FOLDER = "static/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MODEL_PATH = "gaussian_color_denoising_blind.pth"
MODEL_URL = "https://huggingface.co/ndhphuc2005/restormer-checkpoint/resolve/main/gaussian_color_denoising_blind.pth"
print(f"🔥 Using device: {device}")

def get_model(device=device):
    print("🔥 get_model called")
    if not hasattr(get_model, "_model"):
        print("📥 Model not loaded yet, checking path...")
        gc.collect()
        if not os.path.exists(MODEL_PATH):
            print("⬇️ Downloading model...")
            r = requests.get(MODEL_URL)
            with open(MODEL_PATH, "wb") as f:
                f.write(r.content)
        print("📦 Loading model with torch...")
        get_model._model = load_restormer_model(pth_path=MODEL_PATH, device=device)
        print(f"🔥 Using device: {device}")
    return get_model._model

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    if request.method == "POST":
        print("🟡 Received POST request")
        files = request.files.getlist("files")
        blend_factor = float(request.form.get("blend_factor", 0.7))
        sharpen = bool(request.form.get("sharpen"))
        device = device
        print(f"🔥 Using device: {device}")
        for file in files:
            filename = file.filename
            timestamp = int(time.time())
            if filename.endswith(".pdf"):
                pages = convert_from_bytes(file.read())[:3]
                output_paths = []
                for i, page in enumerate(pages):
                    out_name = f"{filename[:-4]}_page{i+1}_denoised_{timestamp}.jpg"
                    out_path = os.path.join(UPLOAD_FOLDER, out_name)
                    page_rgb = page.convert("RGB")
                    model = get_model(device)
                    denoised = denoise_image(page_rgb, model, device, blend_factor, sharpen)
                    denoised.save(out_path)
                    output_paths.append(out_path)
                pdf_name = f"{filename[:-4]}_denoised_{timestamp}.pdf"
                pdf_path = os.path.join(UPLOAD_FOLDER, pdf_name)
                with open(pdf_path, "wb") as f:
                    f.write(img2pdf.convert(output_paths))
                results.append({"type": "pdf", "filename": pdf_name})
            elif filename.lower().endswith((".jpg", ".jpeg", ".png")):
                img = Image.open(file.stream).convert("RGB")
                original_name = f"{filename[:-4]}_original_{timestamp}.jpg"
                output_name = f"{filename[:-4]}_denoised_{timestamp}.jpg"
                original_path = os.path.join(UPLOAD_FOLDER, original_name)
                output_path = os.path.join(UPLOAD_FOLDER, output_name)
                img.save(original_path)
                model = get_model(device)
                denoised = denoise_image(img, model, device, blend_factor, sharpen)
                denoised.save(output_path)
                results.append({"type": "image", "original": original_name, "denoised": output_name})
    return render_template("index.html", results=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)