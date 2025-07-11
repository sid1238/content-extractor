from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from rag.retriever import extract_text_from_file
from rag.generator import generate_questions

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(filepath)

        text = extract_text_from_file(filepath)
        questions = generate_questions(text)

        return jsonify({"questions": questions})

    return jsonify({"error": "Invalid file format. Use .txt, .pdf, or .docx"}), 400

if __name__ == '__main__':
    app.run(debug=True)