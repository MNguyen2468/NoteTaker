from flask import Flask, render_template, request, jsonify, send_file, Response
from openai import OpenAI
from pdf_processing import extract_text_from_pdf
from fpdf import FPDF
from docx import Document
from dotenv import load_dotenv
import io, os

load_dotenv()

app = Flask(__name__)
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate_notes', methods=['POST'])
def generate_notes():
    if 'pdf' not in request.files:
        return jsonify({"error": "no file uploaded"}), 400

    pdf_file = request.files['pdf']
    format = request.form.get('format', 'txt')
    if format == 'pdf':
        format = 'txt'
    audience = request.form.get('audience', 'High School Student')  # Set default to match first option
    pdf_text = extract_text_from_pdf(pdf_file)
    if pdf_text is None:
        return jsonify({"error": "Could not extract text from PDF"}), 500

    if pdf_file:
        response = client.chat.completions.create(
            model = "gpt-4o-mini",
            messages = [{"role": "user", "content": f"I am a {audience}, Generate detailed notes for studying (make sure generated bullet points are correct) in {format} format based on this content and account for spelling errors. Filter out links and other non-text content (and remove the ```{format}``` part of the generated text):\n\n{pdf_text}"}]
        )
        notes = response.choices[0].message.content
        
        return jsonify({"notes": notes})
        
    return jsonify({"error": "Could not extract text from PDF"}), 500

@app.route('/generate_questions', methods=['POST'])
def generate_questions():
    if 'pdf' not in request.files:
        return jsonify({"error": "no file uploaded"}), 400

    pdf_file = request.files['pdf']
    format = request.form.get('format', 'txt')
    if format == 'pdf':
        format = 'txt'
    audience = request.form.get('audience', 'High School Student')  # Set default to match first option
    pdf_text = extract_text_from_pdf(pdf_file)
    if pdf_text is None:
        return jsonify({"error": "Could not extract text from PDF"}), 500

    questionType = request.form.get('questionType').split(",")
    formatedQuestionType = ""
    if questionType[0] == "true":
        if formatedQuestionType != "":
            formatedQuestionType += ", "
        formatedQuestionType += "Short Answer"
    if questionType[1] == "true":
        if formatedQuestionType != "":
            formatedQuestionType += ", "
        formatedQuestionType += "Multiple Choice"
    if questionType[2] == "true":
        if formatedQuestionType != "":
            formatedQuestionType += ", "
        formatedQuestionType += "True/False"
    if questionType[3] == "true":
        if formatedQuestionType != "":
            formatedQuestionType += ", "
        formatedQuestionType += "Logical Order (if applicable)"
    if questionType[4] == "true":
        if formatedQuestionType != "":
            formatedQuestionType += ", "
        formatedQuestionType += "Fill in the Blank"

    if formatedQuestionType != "":
        formatedQuestionType = " Have the questions only be " + formatedQuestionType + "."

    if pdf_file:
        response = client.chat.completions.create(
            model = "gpt-4o-mini", 
            messages = [{"role": "user", "content": f"I am a {audience}. Generate a comprehensive set of study questions with answers based on this content. Have the questions be in the top half of the page and the answers be in the bottom half of the page.{formatedQuestionType} Format it in {format} style and account for any spelling errors. Filter out links and other non-text content (and remove the ```{format}``` part of the generated text):\n\n{pdf_text}"}]
        )
        questions = response.choices[0].message.content
        
        return jsonify({"notes": questions})
        
    return jsonify({"error": "Could not extract text from PDF"}), 500

@app.route('/download_notes', methods=['POST'])
def download_notes():
    data = request.json
    notes = request.json.get('notes', '')
    format = data.get('format', 'txt')

    if format == 'pdf':
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, notes)
        
        pdf_output = io.BytesIO(pdf.output(dest='S').encode('latin1'))
        
        return send_file(
            pdf_output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='notes.pdf'
        )
    elif format == 'docx':
        doc = Document()
        doc.add_paragraph(notes)
        
        doc_output = io.BytesIO()
        doc.save(doc_output)
        doc_output.seek(0)
        
        return send_file(
            doc_output,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name='notes.docx'
        )
    elif format == 'html':
        return Response(
            notes,
            mimetype='text/html',
            headers={"Content-Disposition": "attachment; filename=notes.html"}
        )
    elif format == 'md':
        return send_file(
            io.BytesIO(notes.encode('utf-8')),
            mimetype='text/markdown',
            as_attachment=True,
            download_name='notes.md'
        )
    else:  # Default to .txt
        return send_file(
            io.BytesIO(notes.encode('utf-8')),
            mimetype='text/plain',
            as_attachment=True,
            download_name='notes.txt'
        )

if __name__ == '__main__':
    app.run(debug=True)