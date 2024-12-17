from flask import Flask
from flask_cors import CORS
from flask import Blueprint, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import re
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from io import BytesIO
import openai
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from pypdf import PdfReader
from typing import Tuple, List
import asyncio
from langchain.docstore.document import Document

session_state = {}
# Define the blueprint for routes
routes = Blueprint('routes', __name__)

UPLOAD_FOLDER = './app/uploads'
ALLOWED_EXTENSIONS = {'pdf'}

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

import PyPDF2

def parse_pdf(file: BytesIO, filename: str) -> Tuple[List[str], str]:
    """Extract text from PDF and clean it."""
    pdf = PdfReader(file)
    output = []
    for page in pdf.pages:
        text = page.extract_text()
        # Clean and process text
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
        text = re.sub(r"(?<!\n\s)\n(?!\s\n)", " ", text.strip())
        text = re.sub(r"\n\s*\n", "\n\n", text)
        output.append(text)
    return output, filename


def text_to_docs(text: List[str], filename: str) -> List[Document]:
    """Convert text into LangChain Document objects with metadata."""
    if isinstance(text, str):
        text = [text]
    page_docs = [Document(page_content=page) for page in text]
    for i, doc in enumerate(page_docs):
        doc.metadata["page"] = i + 1

    # Split text into chunks
    doc_chunks = []
    for doc in page_docs:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            separators=["\n\n", "\n", ".", "!", "?", ",", " "],
            chunk_overlap=200,
        )
        chunks = text_splitter.split_text(doc.page_content)
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "page": doc.metadata["page"],
                    "chunk": i,
                    "filename": filename,  # Include filename in metadata
                },
            )
            doc.metadata["source"] = f"{doc.metadata['page']}-{doc.metadata['chunk']}"
            doc_chunks.append(doc)
    return doc_chunks



def docs_to_index(docs, openai_api_key):
    """Create FAISS index from LangChain Document objects."""
    embeddings = OpenAIEmbeddings(api_key=openai_api_key)
    index = FAISS.from_documents(docs, embeddings)
    return index


def get_index_for_pdf(pdf_files, pdf_names, openai_api_key):
    """Create a FAISS index for multiple PDFs."""
    documents = []
    for pdf_file, pdf_name in zip(pdf_files, pdf_names):
        text, filename = parse_pdf(BytesIO(pdf_file), pdf_name)
        documents += text_to_docs(text, filename)
    print("document",documents)
    index = docs_to_index(documents, openai_api_key)
    return index

# Utility function to check if the file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_vectordb(files, filenames):
    # Show a spinner while creating the vectordb
    print("files : ",files)
    vectordb = get_index_for_pdf(
        [file.getvalue() for file in files], filenames, openai.api_key
    )
    return vectordb

# Route for file upload
@routes.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('files')
    filenames = [file.filename for file in files]
    vectordb = create_vectordb(files, filenames)
    session_state["vectordb"] = vectordb
    return jsonify({"message": "PDFs uploaded and indexed successfully"}), 200

prompt_template = """
    You are a helpful Assistant who answers user questions based on multiple contexts given to you.

    Keep your answer short and to the point.

    The evidence is the context of the PDF extract with metadata.

    Carefully focus on the metadata, especially 'filename' and 'page', whenever answering.

    Make sure to add filename and page number at the end of the sentence you are citing to.

    Reply "Not applicable" if the text is irrelevant.

    The PDF content is:
    {pdf_extract}
"""

# Route for answering questions based on PDF
@routes.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({"error": "Missing 'query' in request body"}), 400
        
        query = data['question']
        # Simulate query processing
        response = f"Response to: {query}"  # Replace with your actual logic

        search_results = session_state['vectordb'].similarity_search(query, k=3)
        pdf_extract = "\n".join([result.page_content for result in search_results])

        prompt = session_state.get("prompt", [{"role": "system", "content": "none"}])

        prompt[0] = {
            "role": "system",
            "content": prompt_template.format(pdf_extract=pdf_extract),
        }


        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=prompt,
            stream=False
        )

        result = response.choices[0].message.content

        return jsonify({"response": result}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 400



 # Import the routes blueprint

# Initialize the Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Register the blueprint for routes
app.register_blueprint(routes)

def create_app():
    return app
