"""Document export functionality."""

from datetime import datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


class DocumentExporter:
    """Export documents to various formats."""
    
    def __init__(self, page_size=letter):
        self.page_size = page_size
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1a202c'),
            spaceAfter=30,
            alignment=1  # Center alignment
        ))
        
        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#718096'),
            spaceAfter=12,
            alignment=1  # Center alignment
        ))
        
        # Content style
        self.styles.add(ParagraphStyle(
            name='DocumentContent',
            parent=self.styles['Normal'],
            fontSize=12,
            leading=18,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=12,
            firstLineIndent=0,
            alignment=4  # Justify alignment
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2b6cb0'),
            spaceAfter=12,
            spaceBefore=20
        ))
    
    async def export_document_as_pdf(
        self,
        content: str,
        metadata: dict[str, Any],
        summary: str | None = None,
    ) -> bytes:
        """Export a document to PDF format."""
        # Create a BytesIO buffer
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for the 'Flowable' objects
        story = []
        
        # Add title
        title = metadata.get('filename', 'Document')
        story.append(Paragraph(title, self.styles['CustomTitle']))
        
        # Add metadata
        created_at = metadata.get('created_at', datetime.now().isoformat())
        file_size = metadata.get('file_size', 0)
        
        if isinstance(created_at, str):
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                formatted_date = created_date.strftime('%B %d, %Y at %I:%M %p')
            except (ValueError, AttributeError):
                formatted_date = created_at
        else:
            formatted_date = created_at.strftime('%B %d, %Y at %I:%M %p')
        
        metadata_text = f"Created on {formatted_date}<br/>Size: {file_size:,} bytes"
        story.append(Paragraph(metadata_text, self.styles['Metadata']))
        story.append(Spacer(1, 0.5*inch))
        
        # Add summary if provided
        if summary:
            story.append(Paragraph("Summary", self.styles['SectionHeader']))
            
            # Process summary text into paragraphs
            paragraphs = summary.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), self.styles['DocumentContent']))
            
            story.append(Spacer(1, 0.5*inch))
        
        # Add document content header
        story.append(Paragraph("Document Content", self.styles['SectionHeader']))
        
        # Process content text into paragraphs
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                # Handle bullet points
                if para.strip().startswith('- ') or para.strip().startswith('• '):
                    # Convert to proper bullet points
                    lines = para.strip().split('\n')
                    for line in lines:
                        if line.strip().startswith('- ') or line.strip().startswith('• '):
                            bullet_text = '• ' + line.strip()[2:]
                            story.append(Paragraph(bullet_text, self.styles['DocumentContent']))
                else:
                    story.append(Paragraph(para.strip(), self.styles['DocumentContent']))
        
        # Add footer
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#a0aec0'),
            alignment=1
        )
        story.append(Paragraph("Generated by DocuLearn", footer_style))
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def export_document_as_markdown(
        self,
        content: str,
        metadata: dict[str, Any],
        summary: str | None = None,
    ) -> str:
        """Export document as markdown."""
        filename = metadata.get('filename', 'Document')
        created_at = metadata.get('created_at', datetime.now().isoformat())
        
        markdown = f"# {filename}\n\n"
        markdown += f"_Created: {created_at}_\n\n"
        
        if summary:
            markdown += "## Summary\n\n"
            markdown += f"{summary}\n\n"
        
        markdown += "## Content\n\n"
        markdown += content
        
        markdown += "\n\n---\n"
        markdown += "_Generated by DocuLearn_"
        
        return markdown
    
    def export_document_as_text(
        self,
        content: str,
        metadata: dict[str, Any],
        summary: str | None = None,
    ) -> str:
        """Export document as plain text."""
        filename = metadata.get('filename', 'Document')
        created_at = metadata.get('created_at', datetime.now().isoformat())
        
        text = f"{filename}\n"
        text += "=" * len(filename) + "\n\n"
        text += f"Created: {created_at}\n\n"
        
        if summary:
            text += "SUMMARY\n"
            text += "-" * 7 + "\n"
            text += f"{summary}\n\n"
        
        text += "CONTENT\n"
        text += "-" * 7 + "\n"
        text += content
        
        text += "\n\n---\n"
        text += "Generated by DocuLearn"
        
        return text