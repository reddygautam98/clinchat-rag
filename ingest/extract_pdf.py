#!/usr/bin/env python3
"""
PDF Text Extraction Module for ClinChat-RAG
Extracts page-level text from PDF documents using PyMuPDF
Integrated with unified database system for Google Gemini & Groq APIs
"""

import fitz  # PyMuPDF
import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFExtractor:
    """Enhanced PDF text extraction with metadata and error handling"""
    
    def __init__(self, output_dir: str = "data/processed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of PDF file for tracking changes"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def detect_scanned_document(self, doc: fitz.Document) -> Tuple[bool, float]:
        """
        Detect if document is scanned by analyzing image content vs text
        Returns: (is_scanned, image_ratio)
        """
        total_pages = len(doc)
        pages_with_images = 0
        total_text_length = 0
        total_image_area = 0
        
        for page in doc:
            # Check text content
            text = page.get_text("text").strip()
            total_text_length += len(text)
            
            # Check for images
            image_list = page.get_images()
            if image_list:
                pages_with_images += 1
                # Calculate image coverage
                for img_index, img in enumerate(image_list):
                    try:
                        rect = page.get_image_bbox(img[0])
                        total_image_area += rect.width * rect.height
                    except:
                        pass
        
        # Calculate metrics
        image_ratio = pages_with_images / total_pages if total_pages > 0 else 0
        avg_text_per_page = total_text_length / total_pages if total_pages > 0 else 0
        
        # Heuristics for scanned document detection
        is_scanned = (
            image_ratio > 0.7 and avg_text_per_page < 100  # High image ratio, low text
            or avg_text_per_page < 50  # Very low text content
        )
        
        return is_scanned, image_ratio
    
    def extract_metadata(self, doc: fitz.Document, file_path: str) -> Dict:
        """Extract comprehensive document metadata"""
        metadata = doc.metadata or {}
        file_stats = os.stat(file_path)
        
        is_scanned, image_ratio = self.detect_scanned_document(doc)
        
        return {
            "file_name": os.path.basename(file_path),
            "file_path": str(file_path),
            "file_size": file_stats.st_size,
            "file_hash": self.calculate_file_hash(file_path),
            "created_date": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
            "modified_date": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            "processed_date": datetime.now().isoformat(),
            "total_pages": len(doc),
            "pdf_metadata": {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", "")
            },
            "document_analysis": {
                "is_scanned": is_scanned,
                "image_ratio": image_ratio,
                "requires_ocr": is_scanned
            }
        }
    
    def extract_text_from_page(self, page: fitz.Page, page_num: int) -> Dict:
        """Extract text and metadata from a single page"""
        try:
            # Extract plain text
            text = page.get_text("text")
            
            # Extract text with formatting info
            text_dict = page.get_text("dict")
            
            # Calculate page metrics
            page_rect = page.rect
            text_length = len(text.strip())
            
            # Count images on page
            images = page.get_images()
            image_count = len(images)
            
            # Extract links
            links = page.get_links()
            
            page_data = {
                "page_number": page_num,
                "text": text,
                "text_length": text_length,
                "dimensions": {
                    "width": page_rect.width,
                    "height": page_rect.height
                },
                "images_count": image_count,
                "links_count": len(links),
                "has_content": text_length > 10,  # Threshold for meaningful content
                "formatting_info": text_dict if text_dict else None
            }
            
            # Add image details if present
            if images:
                page_data["images"] = [
                    {
                        "image_index": i,
                        "bbox": list(page.get_image_bbox(img[0])) if hasattr(page, 'get_image_bbox') else None
                    }
                    for i, img in enumerate(images[:5])  # Limit to first 5 images
                ]
            
            return page_data
            
        except Exception as e:
            logger.error(f"Error extracting from page {page_num}: {str(e)}")
            return {
                "page_number": page_num,
                "text": "",
                "text_length": 0,
                "error": str(e),
                "has_content": False
            }
    
    def extract_text(self, file_path: str) -> Dict:
        """
        Extract text from PDF with comprehensive metadata
        Returns structured data ready for database storage
        """
        try:
            logger.info(f"Processing PDF: {file_path}")
            
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            # Open PDF document
            doc = fitz.open(file_path)
            
            # Extract metadata
            metadata = self.extract_metadata(doc, file_path)
            
            # Extract pages
            pages = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_data = self.extract_text_from_page(page, page_num + 1)
                pages.append(page_data)
            
            doc.close()
            
            # Compile extraction results
            extraction_result = {
                "metadata": metadata,
                "pages": pages,
                "extraction_summary": {
                    "total_pages": len(pages),
                    "pages_with_content": sum(1 for p in pages if p.get("has_content", False)),
                    "total_text_length": sum(p.get("text_length", 0) for p in pages),
                    "total_images": sum(p.get("images_count", 0) for p in pages),
                    "extraction_status": "success"
                }
            }
            
            logger.info(f"Successfully extracted {len(pages)} pages from {os.path.basename(file_path)}")
            return extraction_result
            
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            return {
                "metadata": {"file_name": os.path.basename(file_path), "file_path": file_path},
                "pages": [],
                "extraction_summary": {
                    "extraction_status": "failed",
                    "error": str(e)
                }
            }
    
    def save_extraction_results(self, extraction_result: Dict, output_name: str = None) -> str:
        """Save extraction results to JSON file"""
        if output_name is None:
            file_name = extraction_result["metadata"].get("file_name", "unknown")
            output_name = Path(file_name).stem
        
        # Create output directory
        output_dir = self.output_dir / output_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main extraction results
        output_file = output_dir / "pages.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(extraction_result, f, indent=2, ensure_ascii=False)
        
        # Save metadata separately for easy access
        metadata_file = output_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(extraction_result["metadata"], f, indent=2, ensure_ascii=False)
        
        # Save plain text for each page (useful for search)
        pages_dir = output_dir / "pages"
        pages_dir.mkdir(exist_ok=True)
        
        for page in extraction_result["pages"]:
            page_num = page["page_number"]
            page_text_file = pages_dir / f"page_{page_num:03d}.txt"
            with open(page_text_file, "w", encoding="utf-8") as f:
                f.write(page["text"])
        
        logger.info(f"Saved extraction results to: {output_file}")
        return str(output_file)


def extract_text(path: str) -> List[Dict]:
    """
    Simple interface function for backward compatibility
    Matches the original specification
    """
    extractor = PDFExtractor()
    result = extractor.extract_text(path)
    return result["pages"]


def main():
    """Main function to process sample PDFs"""
    extractor = PDFExtractor()
    
    # Sample PDF processing (if files exist)
    sample_pdfs = [
        "data/raw/protocol.pdf",
        "data/raw/clinical_study.pdf",
        "data/raw/patient_report.pdf"
    ]
    
    for pdf_path in sample_pdfs:
        if os.path.exists(pdf_path):
            logger.info(f"Processing: {pdf_path}")
            
            # Extract text and metadata
            result = extractor.extract_text(pdf_path)
            
            # Save results
            output_name = Path(pdf_path).stem
            extractor.save_extraction_results(result, output_name)
            
            # Print summary
            summary = result["extraction_summary"]
            print(f"\n📄 {os.path.basename(pdf_path)}:")
            print(f"   Pages: {summary['total_pages']}")
            print(f"   Pages with content: {summary['pages_with_content']}")
            print(f"   Total text length: {summary['total_text_length']:,} chars")
            print(f"   Status: {summary['extraction_status']}")
            
            if result["metadata"]["document_analysis"]["is_scanned"]:
                print(f"   ⚠️  Scanned document detected - OCR recommended")
        else:
            logger.info(f"Sample PDF not found: {pdf_path}")
    
    print(f"\n✅ PDF extraction complete!")
    print(f"📁 Results saved to: {extractor.output_dir}")


if __name__ == "__main__":
    # Original simple interface
    src = "data/raw/protocol.pdf"
    if os.path.exists(src):
        pages = extract_text(src)
        os.makedirs("data/processed/protocol", exist_ok=True)
        with open("data/processed/protocol/pages.json", "w") as f:
            json.dump(pages, f, indent=2)
        print(f"✅ Extracted {len(pages)} pages from protocol.pdf")
    else:
        print("ℹ️  Running comprehensive extraction demo...")
        main()