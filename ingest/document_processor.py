#!/usr/bin/env python3
"""
Unified Document Processing Pipeline for ClinChat-RAG
Combines PDF text extraction, table extraction, and OCR processing
Integrated with database system for Google Gemini & Groq APIs
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging
import hashlib

# Import our extraction modules
from .extract_pdf import PDFExtractor
from .extract_tables import TableExtractor
from .extract_ocr import OCRProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Unified document processing pipeline combining all extraction methods
    """
    
    def __init__(self, output_dir: str = "data/processed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize extractors
        self.pdf_extractor = PDFExtractor(str(self.output_dir / "text"))
        self.table_extractor = TableExtractor(str(self.output_dir / "tables"))
        self.ocr_processor = OCRProcessor(str(self.output_dir / "ocr"))
        
        # Processing statistics
        self.stats = {
            "documents_processed": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "total_pages": 0,
            "total_tables": 0,
            "ocr_pages": 0
        }
    
    def calculate_document_hash(self, file_path: str) -> str:
        """Calculate hash for document versioning"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def should_process_document(self, file_path: str, force_reprocess: bool = False) -> bool:
        """
        Check if document should be processed based on hash and existing outputs
        """
        if force_reprocess:
            return True
        
        document_name = Path(file_path).stem
        manifest_file = self.output_dir / document_name / "processing_manifest.json"
        
        if not manifest_file.exists():
            return True
        
        try:
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            current_hash = self.calculate_document_hash(file_path)
            stored_hash = manifest.get("document_hash", "")
            
            return current_hash != stored_hash
        except Exception:
            return True
    
    def process_single_document(self, pdf_path: str, options: Dict = None) -> Dict:
        """
        Process a single PDF document through complete pipeline
        
        Args:
            pdf_path: Path to PDF file
            options: Processing options dict with keys:
                - enable_ocr: bool (default True)
                - enable_tables: bool (default True)
                - force_reprocess: bool (default False)
                - ocr_languages: list (default ['eng'])
        """
        if options is None:
            options = {}
        
        # Default options
        default_options = {
            "enable_ocr": True,
            "enable_tables": True,
            "force_reprocess": False,
            "ocr_languages": ['eng']
        }
        options = {**default_options, **options}
        
        logger.info(f"Processing document: {os.path.basename(pdf_path)}")
        
        # Check if processing is needed
        if not self.should_process_document(pdf_path, options["force_reprocess"]):
            logger.info(f"Document already processed and unchanged: {os.path.basename(pdf_path)}")
            return self._load_existing_results(pdf_path)
        
        processing_start = datetime.now()
        document_name = Path(pdf_path).stem
        
        # Initialize results structure
        results = {
            "document_info": {
                "file_name": os.path.basename(pdf_path),
                "file_path": pdf_path,
                "document_hash": self.calculate_document_hash(pdf_path),
                "processing_start": processing_start.isoformat(),
                "processing_options": options
            },
            "extraction_results": {
                "text_extraction": None,
                "table_extraction": None,
                "ocr_processing": None
            },
            "processing_summary": {
                "status": "in_progress",
                "errors": [],
                "warnings": []
            }
        }
        
        try:
            # Step 1: Basic PDF text extraction
            logger.info("Step 1: Extracting text and metadata...")
            text_results = self.pdf_extractor.extract_text(pdf_path)
            results["extraction_results"]["text_extraction"] = text_results
            
            # Check if document is scanned (needs OCR)
            is_scanned = text_results["metadata"]["document_analysis"]["is_scanned"]
            total_text_length = text_results["extraction_summary"]["total_text_length"]
            
            # Step 2: Table extraction
            if options["enable_tables"]:
                logger.info("Step 2: Extracting tables...")
                try:
                    table_results = self.table_extractor.extract_tables_from_pdf(pdf_path)
                    results["extraction_results"]["table_extraction"] = table_results
                    self.stats["total_tables"] += table_results["extraction_summary"]["total_tables"]
                except Exception as e:
                    error_msg = f"Table extraction failed: {str(e)}"
                    results["processing_summary"]["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # Step 3: OCR processing (if needed or requested)
            if options["enable_ocr"] and (is_scanned or total_text_length < 100):
                logger.info("Step 3: Processing with OCR (scanned document detected)...")
                try:
                    ocr_results = self.ocr_processor.process_pdf_with_ocr(pdf_path)
                    results["extraction_results"]["ocr_processing"] = ocr_results
                    self.stats["ocr_pages"] += ocr_results["processing_summary"]["pages_with_ocr"]
                    
                    # If OCR produced better results, use OCR text
                    ocr_text_length = ocr_results["processing_summary"]["total_text_length"]
                    if ocr_text_length > total_text_length * 1.5:  # OCR produced significantly more text
                        results["processing_summary"]["warnings"].append(
                            "OCR produced significantly more text than native extraction"
                        )
                except Exception as e:
                    error_msg = f"OCR processing failed: {str(e)}"
                    results["processing_summary"]["errors"].append(error_msg)
                    logger.error(error_msg)
            elif options["enable_ocr"]:
                logger.info("Step 3: Skipping OCR (good native text extraction)")
            
            # Update statistics
            self.stats["documents_processed"] += 1
            self.stats["total_pages"] += text_results["extraction_summary"]["total_pages"]
            
            # Finalize processing
            processing_end = datetime.now()
            processing_duration = (processing_end - processing_start).total_seconds()
            
            results["document_info"]["processing_end"] = processing_end.isoformat()
            results["document_info"]["processing_duration_seconds"] = processing_duration
            
            results["processing_summary"]["status"] = "completed"
            results["processing_summary"]["pages_processed"] = text_results["extraction_summary"]["total_pages"]
            results["processing_summary"]["extraction_methods_used"] = self._get_used_methods(results)
            
            # Save results
            self._save_processing_results(results, document_name)
            
            self.stats["successful_extractions"] += 1
            logger.info(f"Successfully processed {os.path.basename(pdf_path)} in {processing_duration:.1f} seconds")
            
            return results
            
        except Exception as e:
            self.stats["failed_extractions"] += 1
            error_msg = f"Failed to process {os.path.basename(pdf_path)}: {str(e)}"
            logger.error(error_msg)
            
            results["processing_summary"]["status"] = "failed"
            results["processing_summary"]["errors"].append(error_msg)
            
            return results
    
    def process_directory(self, directory_path: str, pattern: str = "*.pdf", options: Dict = None) -> Dict:
        """
        Process all PDF files in a directory
        """
        directory_path = Path(directory_path)
        pdf_files = list(directory_path.glob(pattern))
        
        logger.info(f"Found {len(pdf_files)} PDF files in {directory_path}")
        
        batch_results = {
            "batch_info": {
                "directory": str(directory_path),
                "pattern": pattern,
                "files_found": len(pdf_files),
                "processing_start": datetime.now().isoformat()
            },
            "individual_results": [],
            "batch_summary": {
                "successful": 0,
                "failed": 0,
                "total_pages": 0,
                "total_tables": 0,
                "total_ocr_pages": 0
            }
        }
        
        for pdf_file in pdf_files:
            try:
                result = self.process_single_document(str(pdf_file), options)
                batch_results["individual_results"].append(result)
                
                if result["processing_summary"]["status"] == "completed":
                    batch_results["batch_summary"]["successful"] += 1
                else:
                    batch_results["batch_summary"]["failed"] += 1
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
                batch_results["batch_summary"]["failed"] += 1
        
        # Finalize batch summary
        batch_results["batch_info"]["processing_end"] = datetime.now().isoformat()
        batch_results["batch_summary"]["total_pages"] = sum(
            r.get("extraction_results", {}).get("text_extraction", {}).get("extraction_summary", {}).get("total_pages", 0)
            for r in batch_results["individual_results"]
        )
        
        # Save batch results
        batch_file = self.output_dir / f"batch_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Batch processing complete. Results saved to: {batch_file}")
        return batch_results
    
    def _get_used_methods(self, results: Dict) -> List[str]:
        """Get list of extraction methods that were used"""
        methods = []
        
        if results["extraction_results"]["text_extraction"]:
            methods.append("pdf_text_extraction")
        
        if results["extraction_results"]["table_extraction"]:
            table_count = results["extraction_results"]["table_extraction"]["extraction_summary"]["total_tables"]
            if table_count > 0:
                methods.append("table_extraction")
        
        if results["extraction_results"]["ocr_processing"]:
            ocr_pages = results["extraction_results"]["ocr_processing"]["processing_summary"]["pages_with_ocr"]
            if ocr_pages > 0:
                methods.append("ocr_processing")
        
        return methods
    
    def _save_processing_results(self, results: Dict, document_name: str):
        """Save comprehensive processing results"""
        # Create document-specific directory
        doc_output_dir = self.output_dir / document_name
        doc_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main processing results
        main_results_file = doc_output_dir / "complete_processing_results.json"
        with open(main_results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save individual component results using their specific savers
        try:
            # Save text extraction results
            if results["extraction_results"]["text_extraction"]:
                self.pdf_extractor.save_extraction_results(
                    results["extraction_results"]["text_extraction"], 
                    document_name
                )
            
            # Save table extraction results
            if results["extraction_results"]["table_extraction"]:
                # Need to restore DataFrame objects for CSV saving
                table_results = results["extraction_results"]["table_extraction"]
                for table in table_results["tables"]:
                    if "raw_data" in table and table["raw_data"]:
                        # Reconstruct DataFrame from raw_data
                        import pandas as pd
                        table["dataframe"] = pd.DataFrame(table["raw_data"])
                
                self.table_extractor.save_tables_to_csv(table_results, document_name)
            
            # Save OCR results
            if results["extraction_results"]["ocr_processing"]:
                self.ocr_processor.save_ocr_results(
                    results["extraction_results"]["ocr_processing"], 
                    document_name
                )
        
        except Exception as e:
            logger.error(f"Error saving component results: {e}")
        
        # Create processing manifest for future reference
        manifest = {
            "document_hash": results["document_info"]["document_hash"],
            "processing_date": results["document_info"]["processing_start"],
            "processing_options": results["document_info"]["processing_options"],
            "extraction_methods": results["processing_summary"]["extraction_methods_used"],
            "status": results["processing_summary"]["status"],
            "output_files": {
                "main_results": str(main_results_file)
            }
        }
        
        manifest_file = doc_output_dir / "processing_manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
    
    def _load_existing_results(self, pdf_path: str) -> Dict:
        """Load existing processing results for a document"""
        document_name = Path(pdf_path).stem
        results_file = self.output_dir / document_name / "complete_processing_results.json"
        
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading existing results: {e}")
            return {"error": f"Could not load existing results: {e}"}
    
    def get_processing_statistics(self) -> Dict:
        """Get current processing statistics"""
        return {
            "statistics": self.stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_processing_report(self) -> str:
        """Generate a human-readable processing report"""
        report = []
        report.append("ClinChat-RAG Document Processing Report")
        report.append("=" * 50)
        report.append("")
        
        stats = self.stats
        report.append(f"Documents Processed: {stats['documents_processed']}")
        report.append(f"Successful Extractions: {stats['successful_extractions']}")
        report.append(f"Failed Extractions: {stats['failed_extractions']}")
        report.append(f"Total Pages: {stats['total_pages']}")
        report.append(f"Total Tables Extracted: {stats['total_tables']}")
        report.append(f"Pages Processed with OCR: {stats['ocr_pages']}")
        report.append("")
        
        if stats['documents_processed'] > 0:
            success_rate = (stats['successful_extractions'] / stats['documents_processed']) * 100
            report.append(f"Success Rate: {success_rate:.1f}%")
            
            if stats['total_pages'] > 0:
                avg_pages = stats['total_pages'] / stats['documents_processed']
                report.append(f"Average Pages per Document: {avg_pages:.1f}")
                
                if stats['total_tables'] > 0:
                    avg_tables = stats['total_tables'] / stats['documents_processed']
                    report.append(f"Average Tables per Document: {avg_tables:.1f}")
        
        return "\n".join(report)


def main():
    """Main function demonstrating the unified processing pipeline"""
    print("🚀 ClinChat-RAG Document Processing Pipeline")
    print("=" * 50)
    
    # Initialize processor
    processor = DocumentProcessor()
    
    # Define sample documents and processing options
    sample_documents = [
        "data/raw/protocol.pdf",
        "data/raw/clinical_study.pdf", 
        "data/raw/patient_report.pdf",
        "data/raw/scanned_document.pdf"
    ]
    
    processing_options = {
        "enable_ocr": True,
        "enable_tables": True,
        "force_reprocess": False,
        "ocr_languages": ['eng']
    }
    
    # Process individual documents
    print("\n📄 Processing Individual Documents:")
    print("-" * 30)
    
    for doc_path in sample_documents:
        if os.path.exists(doc_path):
            print(f"\nProcessing: {os.path.basename(doc_path)}")
            result = processor.process_single_document(doc_path, processing_options)
            
            status = result["processing_summary"]["status"]
            methods = result["processing_summary"].get("extraction_methods_used", [])
            
            print(f"  Status: {status}")
            print(f"  Methods used: {', '.join(methods)}")
            
            if result["extraction_results"]["text_extraction"]:
                text_summary = result["extraction_results"]["text_extraction"]["extraction_summary"]
                print(f"  Pages: {text_summary['total_pages']}")
                print(f"  Text length: {text_summary['total_text_length']:,} chars")
            
            if result["extraction_results"]["table_extraction"]:
                table_summary = result["extraction_results"]["table_extraction"]["extraction_summary"]
                print(f"  Tables: {table_summary['total_tables']}")
            
            if result["extraction_results"]["ocr_processing"]:
                ocr_summary = result["extraction_results"]["ocr_processing"]["processing_summary"]
                print(f"  OCR pages: {ocr_summary['pages_with_ocr']}")
                print(f"  OCR confidence: {ocr_summary['average_confidence']:.1f}%")
        else:
            print(f"❌ File not found: {doc_path}")
    
    # Process directory if raw data exists
    raw_dir = Path("data/raw")
    if raw_dir.exists() and any(raw_dir.glob("*.pdf")):
        print(f"\n📁 Processing Directory: {raw_dir}")
        print("-" * 30)
        
        batch_results = processor.process_directory(str(raw_dir), options=processing_options)
        batch_summary = batch_results["batch_summary"]
        
        print(f"Files processed: {batch_summary['successful'] + batch_summary['failed']}")
        print(f"Successful: {batch_summary['successful']}")
        print(f"Failed: {batch_summary['failed']}")
        print(f"Total pages: {batch_summary['total_pages']}")
    
    # Generate and display final report
    print("\n📊 Final Processing Report:")
    print("-" * 30)
    print(processor.generate_processing_report())
    
    print(f"\n✅ Processing complete!")
    print(f"📁 Results saved to: {processor.output_dir}")


if __name__ == "__main__":
    main()