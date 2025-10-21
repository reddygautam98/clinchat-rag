#!/usr/bin/env python3
"""
Enhanced Document Processing Pipeline with De-identification
============================================================

This module extends the existing document processor to include PHI detection 
and de-identification capabilities for clinical documents.

Features:
- Integrated PDF/table/OCR extraction
- Automatic PHI detection and de-identification
- Secure encrypted mapping storage
- HIPAA-compliant output to data/processed/deid/
- Comprehensive audit logging

Author: ClinChat-RAG Team
License: MIT
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import hashlib
import shutil

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import existing extraction modules
try:
    from ingest.extract_pdf import PDFExtractor
    from ingest.extract_tables import TableExtractor
    from ingest.extract_ocr import OCRProcessor
    from nlp.deid import DeIdentifier, DeIDResult
except ImportError as e:
    logging.error(f"Import error: {e}")
    raise

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnhancedDocumentProcessor:
    """
    Enhanced document processor with de-identification capabilities
    """
    
    def __init__(self, 
                 output_dir: str = "data/processed",
                 deid_password: str = None,
                 enable_deid: bool = True):
        """
        Initialize enhanced document processor
        
        Args:
            output_dir: Base output directory
            deid_password: Password for secure PHI mapping encryption
            enable_deid: Whether to enable de-identification
        """
        
        self.output_dir = Path(output_dir)
        self.deid_output_dir = self.output_dir / "deid"
        self.raw_output_dir = self.output_dir / "raw"
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.deid_output_dir.mkdir(parents=True, exist_ok=True)
        self.raw_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize extractors
        self.pdf_extractor = PDFExtractor(str(self.raw_output_dir / "text"))
        self.table_extractor = TableExtractor(str(self.raw_output_dir / "tables"))
        self.ocr_processor = OCRProcessor(str(self.raw_output_dir / "ocr"))
        
        # Initialize de-identification
        self.enable_deid = enable_deid
        if self.enable_deid:
            try:
                self.deidentifier = DeIdentifier(
                    secure_password=deid_password or "clinchat_deid_2024",
                    output_dir=str(self.deid_output_dir)
                )
                logger.info("✅ De-identification engine initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize de-identifier: {e}")
                self.enable_deid = False
        
        # Processing statistics
        self.stats = {
            "documents_processed": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "deid_processed": 0,
            "deid_failed": 0,
            "total_pages": 0,
            "total_tables": 0,
            "ocr_pages": 0,
            "phi_entities_detected": 0
        }
    
    def calculate_document_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of document for tracking"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]
    
    def extract_document_content(self, file_path: str) -> Dict[str, Any]:
        """Extract content from document using all available methods"""
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        document_hash = self.calculate_document_hash(str(file_path))
        
        logger.info(f"📄 Processing document: {file_path.name}")
        
        extraction_results = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "document_hash": document_hash,
            "timestamp": datetime.now().isoformat(),
            "extraction_methods": {},
            "combined_text": "",
            "tables": [],
            "metadata": {}
        }
        
        # Try PDF extraction first
        if file_path.suffix.lower() == '.pdf':
            try:
                logger.info("🔍 Attempting PDF text extraction...")
                pdf_result = self.pdf_extractor.extract_pdf(str(file_path))
                
                if pdf_result and pdf_result.get('success', False):
                    extraction_results["extraction_methods"]["pdf"] = pdf_result
                    extraction_results["combined_text"] += pdf_result.get('text', '')
                    extraction_results["metadata"].update(pdf_result.get('metadata', {}))
                    
                    self.stats["total_pages"] += pdf_result.get('metadata', {}).get('page_count', 0)
                    logger.info("✅ PDF text extraction successful")
                else:
                    logger.warning("⚠️ PDF text extraction yielded no content")
                
            except Exception as e:
                logger.error(f"❌ PDF extraction failed: {e}")
                extraction_results["extraction_methods"]["pdf"] = {"success": False, "error": str(e)}
            
            # Try table extraction
            try:
                logger.info("📊 Attempting table extraction...")
                table_result = self.table_extractor.extract_tables(str(file_path))
                
                if table_result and table_result.get('success', False):
                    extraction_results["extraction_methods"]["tables"] = table_result
                    extraction_results["tables"] = table_result.get('tables', [])
                    
                    # Add table text to combined text
                    for table_info in table_result.get('tables', []):
                        if 'text_content' in table_info:
                            extraction_results["combined_text"] += f"\n\nTable {table_info.get('table_id', '')}:\n"
                            extraction_results["combined_text"] += table_info['text_content']
                    
                    self.stats["total_tables"] += len(table_result.get('tables', []))
                    logger.info(f"✅ Table extraction found {len(table_result.get('tables', []))} tables")
                
            except Exception as e:
                logger.error(f"❌ Table extraction failed: {e}")
                extraction_results["extraction_methods"]["tables"] = {"success": False, "error": str(e)}
            
            # Try OCR if no significant text was extracted
            if len(extraction_results["combined_text"].strip()) < 100:
                try:
                    logger.info("🔍 Attempting OCR processing (low text content detected)...")
                    ocr_result = self.ocr_processor.process_pdf(str(file_path))
                    
                    if ocr_result and ocr_result.get('success', False):
                        extraction_results["extraction_methods"]["ocr"] = ocr_result
                        extraction_results["combined_text"] += ocr_result.get('text', '')
                        
                        self.stats["ocr_pages"] += ocr_result.get('pages_processed', 0)
                        logger.info("✅ OCR processing successful")
                    
                except Exception as e:
                    logger.error(f"❌ OCR processing failed: {e}")
                    extraction_results["extraction_methods"]["ocr"] = {"success": False, "error": str(e)}
        
        # Update statistics
        if extraction_results["combined_text"].strip():
            self.stats["successful_extractions"] += 1
        else:
            self.stats["failed_extractions"] += 1
        
        return extraction_results
    
    def deidentify_content(self, extraction_results: Dict[str, Any]) -> Dict[str, Any]:
        """Apply de-identification to extracted content"""
        
        if not self.enable_deid:
            logger.warning("⚠️ De-identification disabled, skipping...")
            return extraction_results
        
        if not extraction_results["combined_text"].strip():
            logger.warning("⚠️ No text content to de-identify")
            return extraction_results
        
        try:
            logger.info("🔒 Applying de-identification...")
            
            # Create document ID
            doc_id = f"{extraction_results['file_name']}_{extraction_results['document_hash']}"
            
            # Process with de-identifier
            deid_result = self.deidentifier.process_text(
                extraction_results["combined_text"],
                document_id=doc_id
            )
            
            # Update extraction results with de-identified content
            extraction_results["deid_results"] = {
                "deidentified_text": deid_result.deidentified_text,
                "mapping_id": deid_result.mapping_id,
                "phi_entities": len(deid_result.phi_entities),
                "processing_time": deid_result.processing_time,
                "stats": deid_result.stats
            }
            
            # Update statistics
            self.stats["deid_processed"] += 1
            self.stats["phi_entities_detected"] += len(deid_result.phi_entities)
            
            logger.info(f"✅ De-identification complete: {len(deid_result.phi_entities)} PHI entities detected")
            
        except Exception as e:
            logger.error(f"❌ De-identification failed: {e}")
            self.stats["deid_failed"] += 1
            extraction_results["deid_results"] = {
                "error": str(e),
                "success": False
            }
        
        return extraction_results
    
    def save_results(self, results: Dict[str, Any], save_deid: bool = True) -> Dict[str, str]:
        """Save extraction and de-identification results"""
        
        output_paths = {}
        
        # Create filenames based on document
        base_name = f"{results['file_name']}_{results['document_hash']}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw extraction results
        raw_json_path = self.raw_output_dir / f"{base_name}_raw.json"
        raw_text_path = self.raw_output_dir / f"{base_name}_raw.txt"
        
        # Save raw JSON
        with open(raw_json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        output_paths['raw_json'] = str(raw_json_path)
        
        # Save raw text
        with open(raw_text_path, 'w', encoding='utf-8') as f:
            f.write(results['combined_text'])
        output_paths['raw_text'] = str(raw_text_path)
        
        # Save de-identified results if available and requested
        if save_deid and 'deid_results' in results and 'deidentified_text' in results['deid_results']:
            deid_text_path = self.deid_output_dir / f"{base_name}_deid.txt"
            deid_json_path = self.deid_output_dir / f"{base_name}_deid.json"
            
            # Save de-identified text
            with open(deid_text_path, 'w', encoding='utf-8') as f:
                f.write(results['deid_results']['deidentified_text'])
            output_paths['deid_text'] = str(deid_text_path)
            
            # Save de-identification metadata
            deid_metadata = {
                'original_file': results['file_name'],
                'document_hash': results['document_hash'],
                'timestamp': timestamp,
                'mapping_id': results['deid_results'].get('mapping_id'),
                'phi_entities': results['deid_results'].get('phi_entities', 0),
                'processing_time': results['deid_results'].get('processing_time', 0),
                'stats': results['deid_results'].get('stats', {}),
                'extraction_methods': list(results['extraction_methods'].keys())
            }
            
            with open(deid_json_path, 'w', encoding='utf-8') as f:
                json.dump(deid_metadata, f, indent=2, default=str)
            output_paths['deid_json'] = str(deid_json_path)
        
        # Save tables if extracted
        if results.get('tables'):
            tables_dir = self.deid_output_dir / "tables" if save_deid else self.raw_output_dir / "tables"
            tables_dir.mkdir(exist_ok=True)
            
            for i, table in enumerate(results['tables']):
                table_path = tables_dir / f"{base_name}_table_{i+1}.csv"
                if 'csv_content' in table:
                    with open(table_path, 'w', encoding='utf-8') as f:
                        f.write(table['csv_content'])
                    
                    if save_deid:
                        output_paths[f'deid_table_{i+1}'] = str(table_path)
                    else:
                        output_paths[f'raw_table_{i+1}'] = str(table_path)
        
        return output_paths
    
    def process_single_document(self, 
                              file_path: str, 
                              save_results: bool = True,
                              enable_deid: bool = None) -> Dict[str, Any]:
        """Process a single document through the complete pipeline"""
        
        if enable_deid is None:
            enable_deid = self.enable_deid
        
        logger.info(f"🔄 Processing document: {Path(file_path).name}")
        
        try:
            # Extract content
            results = self.extract_document_content(file_path)
            
            # Apply de-identification if enabled
            if enable_deid:
                results = self.deidentify_content(results)
            
            # Save results if requested
            output_paths = {}
            if save_results:
                output_paths = self.save_results(results, save_deid=enable_deid)
                results['output_paths'] = output_paths
            
            # Update statistics
            self.stats["documents_processed"] += 1
            
            logger.info(f"✅ Document processing complete: {Path(file_path).name}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Document processing failed for {Path(file_path).name}: {e}")
            self.stats["failed_extractions"] += 1
            return {
                "file_path": file_path,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def batch_process_documents(self, 
                              input_dir: str, 
                              pattern: str = "*.pdf",
                              enable_deid: bool = None) -> List[Dict[str, Any]]:
        """Process multiple documents in batch"""
        
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        files = list(input_path.glob(pattern))
        logger.info(f"📁 Found {len(files)} files to process in {input_dir}")
        
        if not files:
            logger.warning(f"⚠️ No files matching pattern '{pattern}' found in {input_dir}")
            return []
        
        results = []
        for file_path in files:
            try:
                result = self.process_single_document(str(file_path), enable_deid=enable_deid)
                results.append(result)
                
                # Log progress
                processed = len([r for r in results if r.get('success', True)])
                logger.info(f"📊 Progress: {processed}/{len(files)} documents processed")
                
            except Exception as e:
                logger.error(f"❌ Failed to process {file_path.name}: {e}")
                results.append({
                    "file_path": str(file_path),
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get summary of processing statistics"""
        return {
            "processing_stats": self.stats.copy(),
            "timestamp": datetime.now().isoformat(),
            "deid_enabled": self.enable_deid,
            "output_directories": {
                "raw": str(self.raw_output_dir),
                "deid": str(self.deid_output_dir) if self.enable_deid else None
            }
        }
    
    def create_audit_report(self) -> str:
        """Create processing audit report"""
        
        report_path = self.output_dir / f"processing_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        audit_data = {
            "audit_timestamp": datetime.now().isoformat(),
            "processing_summary": self.get_processing_summary(),
            "compliance_notes": {
                "deid_enabled": self.enable_deid,
                "phi_detection": self.stats["phi_entities_detected"] if self.enable_deid else "N/A",
                "secure_storage": "Encrypted mapping files created" if self.enable_deid else "N/A",
                "output_separation": "Raw and de-identified content stored separately"
            }
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, indent=2, default=str)
        
        logger.info(f"📋 Audit report created: {report_path}")
        return str(report_path)

# Example usage and testing
if __name__ == "__main__":
    # Initialize enhanced processor
    processor = EnhancedDocumentProcessor(
        output_dir="data/processed",
        deid_password="clinchat_secure_deid_2024",
        enable_deid=True
    )
    
    print("🏥 ClinChat-RAG Enhanced Document Processing Pipeline")
    print("=" * 60)
    
    # Create a test medical document
    test_doc_path = Path("data/test_medical_document.txt")
    test_doc_path.parent.mkdir(parents=True, exist_ok=True)
    
    test_content = """
    MEDICAL RECORD - CONFIDENTIAL
    
    Patient: Dr. John Smith
    DOB: 03/15/1975
    SSN: 123-45-6789
    MRN: MED-789456
    Phone: (555) 123-4567
    Address: 456 Oak Street, Springfield, IL 62701
    
    Date of Service: October 19, 2025
    Provider: Dr. Sarah Johnson, MD
    
    CHIEF COMPLAINT:
    Patient presents with acute chest pain and shortness of breath.
    
    ASSESSMENT:
    Recommend immediate cardiology consultation and EKG.
    Patient education provided regarding cardiac risk factors.
    
    PLAN:
    1. Order cardiac enzymes
    2. Schedule stress test 
    3. Follow up in 2 weeks
    
    Dr. Sarah Johnson, MD
    NPI: 1234567890
    """
    
    test_doc_path.write_text(test_content, encoding='utf-8')
    
    print(f"📄 Created test document: {test_doc_path}")
    
    # Process the test document
    try:
        result = processor.process_single_document(str(test_doc_path))
        
        print(f"\n✅ Processing Results:")
        print(f"   Document: {result.get('file_name', 'Unknown')}")
        print(f"   Text Length: {len(result.get('combined_text', ''))} characters")
        
        if 'deid_results' in result:
            deid = result['deid_results']
            print(f"   PHI Entities: {deid.get('phi_entities', 0)}")
            print(f"   De-id Time: {deid.get('processing_time', 0):.3f} seconds")
            print(f"   Mapping ID: {deid.get('mapping_id', 'N/A')}")
        
        if 'output_paths' in result:
            print(f"\n📁 Output Files Created:")
            for file_type, path in result['output_paths'].items():
                print(f"   {file_type}: {path}")
        
        # Generate audit report
        audit_path = processor.create_audit_report()
        print(f"\n📋 Audit Report: {audit_path}")
        
        # Show statistics
        summary = processor.get_processing_summary()
        print(f"\n📊 Processing Statistics:")
        for key, value in summary['processing_stats'].items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        
    # Clean up test file
    if test_doc_path.exists():
        test_doc_path.unlink()
        print(f"\n🧹 Cleaned up test file: {test_doc_path}")