from flask import Blueprint, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

# Define the blueprint for routes
routes = Blueprint('routes', __name__)

UPLOAD_FOLDER = './app/uploads'
ALLOWED_EXTENSIONS = {'pdf'}

# Utility function to check if the file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for file upload
@routes.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({"error": "No file part"}), 400

    files = request.files.getlist('files')

    if not files:
        return jsonify({"error": "No file selected"}), 400

    filenames = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            filenames.append(filename)

    return jsonify({"message": f"Files {', '.join(filenames)} uploaded successfully!"}), 200

# Route for answering questions based on PDF
@routes.route('/ask', methods=['POST'])
def ask_question():
    question = request.json.get('question')

    if not question:
        return jsonify({"error": "No question provided"}), 400

    answer = "This is a mock answer based on your PDF content."

    return jsonify({"answer": answer}), 200
