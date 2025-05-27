import PyPDF2
import io
import streamlit as st

def extract_text_from_pdf(uploaded_file):
    """
    Extract text content from uploaded PDF file
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        str: Extracted text content from the PDF
        
    Raises:
        Exception: If PDF processing fails
    """
    try:
        # Read the uploaded file
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        
        # Check if PDF is encrypted
        if pdf_reader.is_encrypted:
            raise Exception("The PDF is password protected. Please upload an unprotected PDF.")
        
        # Extract text from all pages
        text_content = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            
            if page_text:
                text_content += page_text + "\n"
        
        # Clean up the text
        text_content = clean_extracted_text(text_content)
        
        if not text_content.strip():
            raise Exception("No readable text found in the PDF. The PDF might contain only images or scanned content.")
        
        return text_content
        
    except Exception as e:
        raise Exception(f"Failed to process PDF: {str(e)}")

def clean_extracted_text(text):
    """
    Clean and normalize extracted text from PDF
    
    Args:
        text (str): Raw extracted text
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace and normalize line breaks
    import re
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Replace multiple newlines with single newline
    text = re.sub(r'\n+', '\n', text)
    
    # Remove extra spaces around newlines
    text = re.sub(r' *\n *', '\n', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

def validate_pdf_content(text, min_length=100):
    """
    Validate if extracted PDF content is sufficient for question generation
    
    Args:
        text (str): Extracted text content
        min_length (int): Minimum required text length
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "No text content found in the PDF."
    
    if len(text.strip()) < min_length:
        return False, f"PDF content is too short (minimum {min_length} characters required)."
    
    # Check if text contains meaningful content (not just special characters)
    import re
    meaningful_chars = re.sub(r'[^\w\s]', '', text)
    if len(meaningful_chars) < min_length * 0.7:  # At least 70% should be meaningful characters
        return False, "PDF content doesn't contain enough readable text."
    
    return True, ""

def get_text_statistics(text):
    """
    Get basic statistics about the extracted text
    
    Args:
        text (str): Extracted text content
        
    Returns:
        dict: Statistics including word count, character count, etc.
    """
    if not text:
        return {
            'characters': 0,
            'words': 0,
            'sentences': 0,
            'paragraphs': 0
        }
    
    import re
    
    # Count characters (excluding whitespace)
    char_count = len(re.sub(r'\s', '', text))
    
    # Count words
    word_count = len(text.split())
    
    # Count sentences (rough estimation)
    sentence_count = len(re.split(r'[.!?]+', text))
    
    # Count paragraphs
    paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
    
    return {
        'characters': char_count,
        'words': word_count,
        'sentences': sentence_count,
        'paragraphs': paragraph_count
    }
