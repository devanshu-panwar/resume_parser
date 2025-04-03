from flask import Flask, request, render_template, redirect, url_for, jsonify
import os
from werkzeug.utils import secure_filename
from extract_text import extract_text  # Import your extract function
from parser import extract_contact_info
import requests  # Import the requests library
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__, template_folder='templates')

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/resume_parser", methods=["GET", "POST"])
def upload_file():
    # ... (Your existing resume parser code remains the same)
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

            return render_template("result.html", text=extracted_text, info=info)

    return render_template("upload.html")

# --- Reusable function to make POST requests to external APIs ---
def make_external_post_request(api_url_env_var):
    api_url = os.getenv(api_url_env_var)
    data = request.get_json()
    try:
        response = requests.post(api_url, json=data)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error communicating with external API: {e}"}), 500

# --- Integration of External APIs (using .env variables) with POST method ---

@app.route("/api/external/user_info", methods=["POST"])
def post_external_user_info():
    return make_external_post_request("USER_INFO_API_URL")

@app.route("/api/external/education", methods=["POST"])
def post_external_education():
    return make_external_post_request("EDUCATION_API_URL")

@app.route("/api/external/projects", methods=["POST"])
def post_external_projects():
    return make_external_post_request("PROJECTS_API_URL")

@app.route("/api/external/skills_list", methods=["POST"])
def post_external_skills_list():
    return make_external_post_request("SKILLS_LIST_API_URL")

@app.route("/api/external/work_experience", methods=["POST"])
def post_external_work_experience():
    return make_external_post_request("WORK_EXPERIENCE_API_URL")

if __name__ == "__main__":
    app.run(debug=True)