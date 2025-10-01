import streamlit as st
import requests
from pdf2image import convert_from_path
import pytesseract
import re
import tempfile
import pandas as pd

# ===========================
# OCR Function
# ===========================
def extract_text_from_pdf_url(pdf_url):
    # Download PDF into a temporary file
    response = requests.get(pdf_url)
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_pdf.write(response.content)
    temp_pdf.close()

    # Convert PDF pages to images
    pages = convert_from_path(temp_pdf.name)

    # OCR all pages
    full_text = ""
    for i, page in enumerate(pages):
        text = pytesseract.image_to_string(page)
        full_text += f"\n--- Page {i+1} ---\n{text}\n"
    return full_text


# ===========================
# Test Extraction Function
# ===========================
def extract_all_tests(ocr_text):
    results = []

    pattern = re.compile(
        r"([A-Za-z\s\(\)\/%]+?)\s+([\d.,]+(?:\s*Low|\s*High|\s*Borderline)?)\s+([\d\.]+-?[\d\.]+)?\s*([a-zA-Z%\/]+)?",
        re.IGNORECASE
    )

    for match in pattern.finditer(ocr_text):
        test_name = match.group(1).strip()
        result = match.group(2).strip()
        reference = match.group(3).strip() if match.group(3) else None
        unit = match.group(4).strip() if match.group(4) else None

        if len(test_name.split()) < 2:
            continue

        # Determine status
        status = None
        try:
            if reference and "-" in reference:
                low, high = reference.split("-")
                low, high = float(low), float(high)
                result_value = float(re.findall(r"[\d.]+", result)[0])

                if result_value < low:
                    status = "Low"
                elif result_value > high:
                    status = "High"
                else:
                    status = "Normal"
        except:
            status = None

        results.append({
            "Test": test_name,
            "Result": result,
            "Unit": unit,
            "Reference Range": reference,
            "Status": status
        })

    return pd.DataFrame(results)


# ===========================
# Streamlit UI
# ===========================
st.title("🧪 Medical Lab Report Extractor")
st.write("Upload a PDF via URL and extract test results automatically.")

# Input URL
pdf_url = st.text_input("Enter PDF URL:")

if pdf_url:
    with st.spinner("Processing PDF... Please wait ⏳"):
        ocr_text = extract_text_from_pdf_url(pdf_url)
        df = extract_all_tests(ocr_text)

    if not df.empty:
        st.success("✅ Extraction Complete!")
        st.dataframe(df)

        # Download option
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download as CSV", csv, "lab_results.csv", "text/csv")
    else:
        st.warning("⚠️ No valid test results found in the PDF.")
