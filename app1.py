import os
from dotenv import load_dotenv
import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
import openai


# Load environment variables from .env
load_dotenv()

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("Medical Lab Report Parser")

# Upload PDF
uploaded_file = st.file_uploader("Upload Lab Report PDF", type="pdf")

if uploaded_file is not None:
    # Extract text from PDF
    try:
        # First try normal PDF text extraction
        with pdfplumber.open(uploaded_file) as pdf:
            text = ''
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'

        # If empty, use OCR
        if text.strip() == '':
            st.info("No text detected. Trying OCR...")
            images = convert_from_bytes(uploaded_file.read())
            text = ''
            for image in images:
                text += pytesseract.image_to_string(image) + '\n'

        st.subheader("Extracted Text")
        st.text_area("Text", text, height=300)

        # User clicks button to extract structured data
        if st.button("Extract JSON"):
            if text.strip() == '':
                st.warning("No text found to extract.")
            else:
                # Your prompt for OpenAI
                prompt = f"""
You are an AI assistant specialized in extracting structured data from medical lab reports. 

Given the input text, extract the following information in JSON format. 
If a field is missing, use null. Ensure the format is consistent.

{{
  "Lab_Details": {{
    "Lab_Name": "",
    "Phone": [],
    "Email": "",
    "Address": "",
    "Website": ""
  }},
  "Patient_Details": {{
    "Name": "",
    "Age": null,
    "Sex": "",
    "Patient_ID": "",
    "Sample_Collection_Time": "",
    "Registration_Time": "",
    "Report_Time": "",
    "Referring_Doctor": ""
  }},
  "Test_Details": [
    {{
      "Test_Name": "",
      "Sample_Type": "",
      "Parameters": [
        {{
          "Parameter": "",
          "Result": "",
          "Reference_Range": "",
          "Unit": "",
          "Flag": ""
        }}
      ],
      "Interpretation": ""
    }}
  ],
  "Lab_Staff": [
    {{
      "Name": "",
      "Designation": ""
    }}
  ]
}}

Instructions:
- Extract multiple phone numbers or emails into arrays.
- Extract all tests and parameters listed, including their units, reference values, and flags.
- Keep the JSON valid and properly nested.
- Ignore unrelated text like ads or slogans.

Text:
\"\"\"{text}\"\"\"
"""

                # Call OpenAI
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",  # or "gpt-4" if you have access
                    messages=[
                        {"role": "system", "content": "You are an AI assistant specialized in extracting structured data from medical lab reports."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0
                )

                json_result = response.choices[0].message.content.strip()
                st.subheader("Extracted JSON")
                st.code(json_result, language="json")

    except Exception as e:
        st.error(f"Error reading PDF: {e}")
