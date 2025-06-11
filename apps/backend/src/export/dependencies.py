"""Dependencies for Export module."""

from typing import Annotated

from fastapi import Depends

from .service import PDFExporter


def get_pdf_exporter() -> PDFExporter:
    """Get PDF exporter instance."""
    return PDFExporter()


PDFExporterDep = Annotated[PDFExporter, Depends(get_pdf_exporter)]