from flask import Flask, request, render_template, redirect, url_for, jsonify
import os
from werkzeug.utils import secure_filename
from extract_text import extract_text  # Import your extract function
from parser import extract_contact_info

app = Flask(__name__,template_folder='templates')

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/resume_parser", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"

        file = request.files["file"]

        if file.filename == "":
            return "No selected file"

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            extracted_text = extract_text(filepath)  # Call your function

            # Extract structured work experience
            info = extract_contact_info(extracted_text)

            #return render_template("result.html", text=extracted_text, info=info)
            return jsonify({"extracted_text": extracted_text}), 200

    return render_template("upload.html")


if __name__ == "__main__":
    app.run(debug=True)
