import pdfplumber
import fitz # PyMuPDF
import pytesseract
from PIL import Image
import io

pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

def extract_text_from_pdf(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
                

        # If text is empty, fallback to OCR
        if not text.strip():
            return ocr_pdf(pdf_file)
        
        return text.strip()
    
    except Exception as e:
        return None
    
def ocr_pdf(pdf_file):
    pdf_text = ""
    
    with fitz.open(stream = pdf_file.read(), filetype = "pdf") as pdf:
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            
            pdf_text += pytesseract.image_to_string(img)
    return pdf_text.strip()

