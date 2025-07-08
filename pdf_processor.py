# pdf_processor.py
# An advanced PDF processing script that uses a hybrid approach:
# 1. Tries intelligent direct text extraction for digitally native PDFs.
# 2. Falls back to advanced OCR for scanned/image-based PDFs.

import shutil
import logging
from pathlib import Path
import sys

# Third-party libraries - install from requirements.txt
import cv2
import fitz  # This is PyMuPDF
import numpy as np
import pytesseract

# --- Configuration ---
# Set the path to the Tesseract executable if it's not in your system's PATH
# For Windows:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# For Linux/macOS, it's often in the PATH by default after installation.

# Define input and output directories
INPUT_DIR = Path("input_pdfs")
OUTPUT_DIR = Path("output")
PROCESSED_DIR = OUTPUT_DIR / "processed_successfully"
FAILED_LOCKED_DIR = OUTPUT_DIR / "failed_locked"
FAILED_OCR_DIR = OUTPUT_DIR / "failed_ocr"
# Increased threshold for more reliable fallback detection
MIN_TEXT_LENGTH_PER_PAGE = 50 

# --- Setup Logging ---
# This will create a log file and also print messages to the console.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler(OUTPUT_DIR / "processing.log"),
        logging.StreamHandler()
    ]
)

def create_directories():
    """Creates the necessary input and output directories."""
    INPUT_DIR.mkdir(exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FAILED_LOCKED_DIR.mkdir(parents=True, exist_ok=True)
    FAILED_OCR_DIR.mkdir(parents=True, exist_ok=True)

def is_tesseract_installed():
    """Checks if the Tesseract executable can be found."""
    try:
        pytesseract.get_tesseract_version()
        return True
    except pytesseract.TesseractNotFoundError:
        logging.error("Tesseract is not installed or not in your PATH.")
        logging.error("Please install Tesseract-OCR from https://github.com/tesseract-ocr/tesseract")
        return False

def is_pdf_locked(pdf_path: Path) -> bool:
    """Checks if a PDF is encrypted using PyMuPDF."""
    try:
        with fitz.open(pdf_path) as doc:
            if doc.is_encrypted:
                logging.warning(f"'{pdf_path.name}' is password-protected.")
                return True
    except Exception as e:
        logging.error(f"Could not open '{pdf_path.name}'. It may be corrupt. Error: {e}")
        return True
    return False

def extract_text_with_hybrid_approach(pdf_path: Path) -> str:
    """
    Extracts text from a PDF using a hybrid strategy.
    1. Tries intelligent direct text extraction via PyMuPDF.
    2. If that fails, falls back to OCR with preprocessing.
    """
    full_text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for i, page in enumerate(doc):
                # --- Stage 1: Attempt Intelligent Direct Text Extraction ---
                # Using "simple" preserves layout better than the default "text".
                # sort=True maintains the natural reading order.
                direct_text = page.get_text("simple", sort=True).strip()
                
                if len(direct_text) > MIN_TEXT_LENGTH_PER_PAGE:
                    logging.info(f"  - Page {i+1}: Direct text extraction successful.")
                    full_text += f"\n--- Page {i+1} ---\n{direct_text}"
                else:
                    # --- Stage 2: Fallback to OCR ---
                    logging.warning(f"  - Page {i+1}: Direct extraction found little text. Falling back to OCR.")
                    pix = page.get_pixmap(dpi=300)
                    img_cv = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                    
                    if img_cv.shape[2] == 4:
                        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGRA2GRAY)
                    else:
                        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

                    thresh_image = cv2.threshold(img_cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                    denoised_image = cv2.medianBlur(thresh_image, 3)
                    
                    ocr_text = pytesseract.image_to_string(denoised_image, lang='eng', config='--psm 6')
                    full_text += f"\n--- Page {i+1} (OCR) ---\n{ocr_text.strip()}"
        
        return full_text.strip()

    except Exception as e:
        logging.error(f"Text extraction process failed for '{pdf_path.name}'. Error: {e}")
        return ""

def main():
    """Main function to orchestrate the PDF processing pipeline."""
    create_directories()
    logging.info("Starting PDF processing pipeline...")
    
    if not is_tesseract_installed():
        sys.exit(1) # Exit if Tesseract is not available for the OCR fallback.

    pdf_files = list(INPUT_DIR.glob("*.pdf"))
    if not pdf_files:
        logging.info(f"No PDF files found in '{INPUT_DIR}'. Waiting for new files.")
        return

    logging.info(f"Found {len(pdf_files)} PDF(s) to process.")

    for pdf_path in pdf_files:
        logging.info(f"--- Processing '{pdf_path.name}' ---")

        if is_pdf_locked(pdf_path):
            shutil.move(pdf_path, FAILED_LOCKED_DIR / pdf_path.name)
            continue

        extracted_text = extract_text_with_hybrid_approach(pdf_path)

        if extracted_text:
            text_file_path = PROCESSED_DIR / f"{pdf_path.stem}.txt"
            with open(text_file_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            
            shutil.move(pdf_path, PROCESSED_DIR / pdf_path.name)
            logging.info(f"Successfully processed '{pdf_path.name}'.")
        else:
            logging.error(f"Failed to extract any text from '{pdf_path.name}'. Moving to failed folder.")
            shutil.move(pdf_path, FAILED_OCR_DIR / pdf_path.name)

    logging.info("PDF processing pipeline finished.")


if __name__ == "__main__":
    main()
