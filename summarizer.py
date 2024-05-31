import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic
from pdfminer.high_level import extract_text

client = anthropic.Client(api_key='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')

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def serve_index():
    return send_from_directory('templates', 'index.html')

@app.route('/summarize', methods=['POST'])
def summarize_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
    uploaded_file.save(file_path)

    try:
        text = extract_text_from_pdf(file_path)
        summary_text = generate_summary(text)
        return jsonify({'summary': summary_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def extract_text_from_pdf(pdf_file):
    with open(pdf_file, 'rb') as file:
        text = extract_text(file)
    return text

def generate_summary(text):
    prompt = "You are a helpful AI assistant that summarizes text."
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        system="Respond in technical English language",
        messages=[
            {"role": "user", "content": f"{prompt}\n\nHuman: Summarize the following text (maximum 10 points):\n\n{text}\n\nAssistant:"}
        ]
    )
    response_text = message.content[0].text
    summary_lines = [f"• {line.strip()}" for line in response_text.strip().split("\n") if line.strip()]
    summary_text = "\n".join(summary_lines[:10])  # Limit to 10 points
    return summary_text

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question')
    context = data.get('context',"")
    prompt = f"Context: {context}\n\nQuestion: {question}\n\nAnswer:"
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        system="Respond in technical English language",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    answer = message.result["output"]
    return jsonify({'answer': answer})

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)


    