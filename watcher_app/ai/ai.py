from openai import OpenAI
import PyPDF2
import os
from dotenv import load_dotenv

load_dotenv()

# Function to extract text from PDF


def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

# Function to analyze the extracted text using OpenAI API with completion


def analyze_pdf_text(pre_text, text):
    client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": "You are finance specialist."
            },
            {
                "role": "user",
                "content": f"{pre_text} - {text}."
            }
        ]
    )

    # print(response.choices[0].message.content)
    return response.choices[0].message.content

# Main function to process PDF and get analysis as JSON


def analyze_pdf(pre_text, pdf_path):
    # Extract text from the PDF
    pdf_text = extract_text_from_pdf(pdf_path)

    # Call OpenAI to analyze the text
    analysis_result = analyze_pdf_text(pre_text, pdf_text)

    return analysis_result


def analyze_doc(pre_text, file_path):
    print("analyzing", file_path, "...")
    analysis_result = analyze_pdf(pre_text, file_path)
    # print(analysis_result)
    return analysis_result
