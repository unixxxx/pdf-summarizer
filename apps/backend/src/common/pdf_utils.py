"""PDF utility functions."""

import io

import PyPDF2


async def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text content from a PDF file."""
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text_content = []
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text_content.append(page.extract_text())
        
        return "\n".join(text_content)
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

