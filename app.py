from flask import Flask, request, render_template
from pdf2image import convert_from_bytes
from PIL import Image
import os
import time
import img2pdf
from restormer_model import load_restormer_model, denoise_image
import concurrent.futures
from io import BytesIO

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

UPLOAD_FOLDER = "static/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

device = "cpu"
model = load_restormer_model(device=device)

def process_pdf_page(page, model, device, blend_factor, sharpen, filename, index, timestamp):
    out_name = f"{filename[:-4]}_page{index+1}_denoised_{timestamp}.jpg"
    out_path = os.path.join(UPLOAD_FOLDER, out_name)
    page_rgb = page.convert("RGB")
    denoised = denoise_image(page_rgb, model, device, blend_factor, sharpen=sharpen)
    denoised.save(out_path)
    return out_path

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    if request.method == "POST":
        files = request.files.getlist("files")
        blend_factor = float(request.form.get("blend_factor", 0.7))
        sharpen = bool(request.form.get("sharpen"))
        for file in files:
            filename = file.filename
            timestamp = int(time.time())
            if filename.endswith(".pdf"):
                pages = convert_from_bytes(file.read())
                pages = pages[:3]
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = [
                        executor.submit(process_pdf_page, page, model, device, blend_factor, sharpen, filename, i, timestamp)
                        for i, page in enumerate(pages)
                    ]
                    output_paths = [f.result() for f in concurrent.futures.as_completed(futures)]
                pdf_name = f"{filename[:-4]}_denoised_{timestamp}.pdf"
                pdf_path = os.path.join(UPLOAD_FOLDER, pdf_name)
                pdf_bytes = img2pdf.convert(output_paths)
                pdf_buffer = BytesIO(pdf_bytes)
                with open(pdf_path, "wb") as f:
                    f.write(pdf_buffer.getvalue())
                results.append({"type": "pdf", "filename": pdf_name})
            elif filename.lower().endswith((".jpg", ".jpeg", ".png")):
                img = Image.open(file.stream).convert("RGB")
                original_name = f"{filename[:-4]}_original_{timestamp}.jpg"
                output_name = f"{filename[:-4]}_denoised_{timestamp}.jpg"
                original_path = os.path.join(UPLOAD_FOLDER, original_name)
                output_path = os.path.join(UPLOAD_FOLDER, output_name)
                img.save(original_path)
                denoised = denoise_image(img, model, device, blend_factor, sharpen=sharpen)
                denoised.save(output_path)
                results.append({"type": "image", "original": original_name, "denoised": output_name})
    return render_template("index.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)