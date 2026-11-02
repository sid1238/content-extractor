import os
import mysql.connector

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt

from rag.retriever import extract_text_from_file, extract_text_from_upload
from rag.generator import generate_questions
from rag.matcher import fetch_job_posting, match_resume_to_job, JobFetchError

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

# ---- File Upload Config ----
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---- Database Config ----
db_config = {
    "host": "localhost",
    "user": "root",          # change this
    "password": "password",  # change this
    "database": "rag_users"
}

def get_db():
    return mysql.connector.connect(**db_config)

# ---- Helpers ----
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ====================
# AUTH ROUTES
# ====================

@app.route("/signup", methods=["POST"])
def signup():
    ''' Handles Sign Up Route  '''
    data = request.json
    conn = get_db()
    cursor = conn.cursor()

    hashed_pw = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    sql = """INSERT INTO users 
        (first_name, last_name, email, password_hash, address, city, state, country, pincode, 
        education, work_experience, authorized_work, sponsorship_required, gender, community, protected_veteran) 
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    values = (
        data["first_name"], data["last_name"], data["email"], hashed_pw,
        data.get("address"), data.get("city"), data.get("state"), data.get("country"), data.get("pincode"),
        data.get("education"), data.get("work_experience"), data.get("authorized_work"),
        data.get("sponsorship_required"), data.get("gender"), data.get("community"), data.get("protected_veteran")
    )

    try:
        cursor.execute(sql, values)
        conn.commit()
        return jsonify({"message": "User registered successfully!"}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (data["email"],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and bcrypt.check_password_hash(user["password_hash"], data["password"]):
        del user["password_hash"]  # don’t send hash
        return jsonify({"message": "Login successful", "user": user})
    else:
        return jsonify({"error": "Invalid email or password"}), 401

@app.route("/profile/<email>", methods=["GET"])
def profile(email):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        del user["password_hash"]
        return jsonify(user)
    else:
        return jsonify({"error": "User not found"}), 404

# ====================
# RAG ROUTES
# ====================

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        text = extract_text_from_file(filepath)
        questions = generate_questions(text)

        return jsonify({"questions": questions})

    return jsonify({"error": "Invalid file format. Use .txt, .pdf, or .docx"}), 400

# ====================
# JOB MATCH ROUTE
# ====================

@app.route('/match', methods=['POST'])
def match_job():
    ''' Compares an uploaded resume against the job posting at job_url '''
    file = request.files.get('resume')
    job_url = (request.form.get('job_url') or '').strip()

    if not file or not file.filename:
        return jsonify({"error": "Upload a resume first."}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file format. Use .txt, .pdf, or .docx"}), 400
    if not job_url:
        return jsonify({"error": "Enter a job URL."}), 400

    try:
        resume_text = extract_text_from_upload(file)
    except Exception:
        return jsonify({"error": "Could not read the resume file."}), 400
    if len(resume_text.strip()) < 50:
        return jsonify({"error": "No text found in the resume. If it is a scanned PDF, upload a text-based PDF or .docx."}), 400

    try:
        job = fetch_job_posting(job_url)
    except JobFetchError as err:
        return jsonify({"error": str(err)}), 422

    result = match_resume_to_job(resume_text, job)
    result["job"]["url"] = job_url
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)