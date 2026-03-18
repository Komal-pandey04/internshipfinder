#used for uploading file in byte format , remove extraspaces and written simple clean text


import io                                #handling byte data
from pdfminer.high_level import extract_text   #extracting text from PDF files
import re                                #cleaning text using regular expressions


# # Purpose:  Extracts and cleans text from a PDF file
def extract_text_from_pdf(file_bytes) -> str:
    # file_bytes: contains the bytes of the uploaded PDF file

    # Convert the byte data into a file-like object that PDFMiner can read
    with io.BytesIO(file_bytes) as fh:
        # Extract all readable text from the PDF
        text = extract_text(fh)

    # Clean the text by replacing multiple spaces, tabs, or newlines with a single space
    text = re.sub(r'\s+', ' ', text)

    # Return the clean text as a normal string
    return text


# Purpose:  Makes a filename safe for saving by removing bad characters

def sanitize_filename(name: str) -> str:
    # Replace any character that is not a letter, number, dot, hyphen, or underscore
    # with an underscore (_) to avoid invalid or unsafe filenames
    return re.sub(r'[^A-Za-z0-9_.-]', '_', name)
