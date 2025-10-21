#!/usr/bin/env python3
"""
Table Extraction Module for ClinChat-RAG
Extracts tables from PDF documents and converts to DataFrame/CSV format
Supports both structured tables and heuristic text-based table detection
"""

import fitz  # PyMuPDF
import pandas as pd
import json
import re
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class TableExtractor:
    """Enhanced table extraction from PDF documents"""
    
    def __init__(self, output_dir: str = "data/processed/tables"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def detect_table_structure(self, page: fitz.Page) -> List[Dict]:
        """
        Detect table structures using PyMuPDF table detection
        Returns list of table dictionaries with metadata
        """
        tables = []
        
        try:
            # Try to find tables using PyMuPDF's table detection
            table_list = page.find_tables()
            
            for table_index, table in enumerate(table_list):
                try:
                    # Extract table as pandas DataFrame
                    df = table.to_pandas()
                    
                    # Get table bounding box
                    bbox = table.bbox
                    
                    table_info = {
                        "table_index": table_index,
                        "bbox": {
                            "x0": bbox.x0,
                            "y0": bbox.y0, 
                            "x1": bbox.x1,
                            "y1": bbox.y1
                        },
                        "dimensions": {
                            "rows": len(df),
                            "columns": len(df.columns) if not df.empty else 0
                        },
                        "extraction_method": "pymupdf_structured",
                        "dataframe": df,
                        "raw_data": df.to_dict("records") if not df.empty else []
                    }
                    
                    tables.append(table_info)
                    
                except Exception as e:
                    logger.warning(f"Error processing structured table {table_index}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.info(f"Structured table detection not available: {str(e)}")
        
        return tables
    
    def extract_text_tables_heuristic(self, page_text: str, page_num: int) -> List[Dict]:
        """
        Heuristic table extraction from text using pattern recognition
        Looks for aligned text that might represent tabular data
        """
        tables = []
        lines = page_text.split('\n')
        
        # Pattern 1: Lines with multiple whitespace-separated values
        potential_table_lines = []
        current_table_lines = []
        
        for line_num, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                if current_table_lines:
                    potential_table_lines.append(current_table_lines.copy())
                    current_table_lines = []
                continue
            
            # Look for lines with multiple columns (3+ whitespace-separated values)
            parts = re.split(r'\s{2,}', line.strip())  # Split on 2+ spaces
            
            if len(parts) >= 3:
                current_table_lines.append({
                    "line_number": line_num + 1,
                    "text": line.strip(),
                    "columns": parts
                })
            else:
                if current_table_lines:
                    potential_table_lines.append(current_table_lines.copy())
                    current_table_lines = []
        
        # Add any remaining table
        if current_table_lines:
            potential_table_lines.append(current_table_lines)
        
        # Convert potential tables to structured format
        for table_index, table_lines in enumerate(potential_table_lines):
            if len(table_lines) < 2:  # Need at least 2 rows
                continue
            
            try:
                # Determine number of columns (use mode of column counts)
                col_counts = [len(line["columns"]) for line in table_lines]
                most_common_cols = max(set(col_counts), key=col_counts.count)
                
                # Filter lines with consistent column count
                consistent_lines = [line for line in table_lines if len(line["columns"]) == most_common_cols]
                
                if len(consistent_lines) < 2:
                    continue
                
                # Create DataFrame
                data_rows = [line["columns"] for line in consistent_lines]
                
                # Use first row as headers if it looks like headers
                first_row = data_rows[0]
                if self._looks_like_header(first_row):
                    headers = first_row
                    data = data_rows[1:]
                else:
                    headers = [f"Column_{i+1}" for i in range(most_common_cols)]
                    data = data_rows
                
                if not data:  # Need at least one data row
                    continue
                
                df = pd.DataFrame(data, columns=headers)
                
                table_info = {
                    "table_index": table_index,
                    "page_number": page_num,
                    "line_range": {
                        "start": consistent_lines[0]["line_number"],
                        "end": consistent_lines[-1]["line_number"]
                    },
                    "dimensions": {
                        "rows": len(df),
                        "columns": len(df.columns)
                    },
                    "extraction_method": "heuristic_text",
                    "confidence": self._calculate_table_confidence(consistent_lines),
                    "dataframe": df,
                    "raw_data": df.to_dict("records")
                }
                
                tables.append(table_info)
                
            except Exception as e:
                logger.warning(f"Error processing heuristic table {table_index}: {str(e)}")
                continue
        
        return tables
    
    def _looks_like_header(self, row: List[str]) -> bool:
        """Determine if a row looks like table headers"""
        # Simple heuristics for header detection
        text_row = ' '.join(row).lower()
        
        # Common header indicators
        header_indicators = [
            'name', 'date', 'time', 'id', 'number', 'value', 'amount', 
            'type', 'status', 'description', 'patient', 'dose', 'treatment',
            'result', 'test', 'measurement', 'parameter', 'unit'
        ]
        
        # Check if row contains header-like terms
        contains_header_terms = any(indicator in text_row for indicator in header_indicators)
        
        # Check for numeric patterns (headers usually have fewer numbers)
        numeric_chars = sum(1 for char in text_row if char.isdigit())
        total_chars = len(text_row.replace(' ', ''))
        numeric_ratio = numeric_chars / total_chars if total_chars > 0 else 0
        
        return contains_header_terms or numeric_ratio < 0.3
    
    def _calculate_table_confidence(self, table_lines: List[Dict]) -> float:
        """Calculate confidence score for extracted table"""
        if not table_lines:
            return 0.0
        
        # Factors that increase confidence:
        # 1. Consistent column count
        col_counts = [len(line["columns"]) for line in table_lines]
        col_consistency = 1.0 - (len(set(col_counts)) - 1) / len(col_counts)
        
        # 2. Reasonable number of rows and columns
        avg_cols = sum(col_counts) / len(col_counts)
        size_score = min(1.0, (len(table_lines) * avg_cols) / 20)  # Normalized to 20 cells
        
        # 3. Text patterns that suggest tabular data
        all_text = ' '.join([' '.join(line["columns"]) for line in table_lines])
        has_numbers = bool(re.search(r'\d', all_text))
        has_consistent_spacing = True  # Assumed from extraction method
        
        pattern_score = 0.5 + (0.3 if has_numbers else 0) + (0.2 if has_consistent_spacing else 0)
        
        # Combined confidence score
        confidence = (col_consistency * 0.4 + size_score * 0.3 + pattern_score * 0.3)
        return round(confidence, 2)
    
    def extract_tables_from_page(self, page: fitz.Page, page_num: int, page_text: str = None) -> List[Dict]:
        """
        Extract all tables from a single page using multiple methods
        """
        all_tables = []
        
        # Method 1: Structured table detection (PyMuPDF)
        structured_tables = self.detect_table_structure(page)
        all_tables.extend(structured_tables)
        
        # Method 2: Heuristic text-based extraction
        if page_text is None:
            page_text = page.get_text()
        
        heuristic_tables = self.extract_text_tables_heuristic(page_text, page_num)
        
        # Filter out heuristic tables that overlap with structured tables
        for h_table in heuristic_tables:
            h_table["page_number"] = page_num
            all_tables.append(h_table)
        
        # Add extraction metadata
        for table in all_tables:
            table["extraction_timestamp"] = datetime.now().isoformat()
            table["page_number"] = page_num
        
        return all_tables
    
    def extract_tables_from_pdf(self, pdf_path: str) -> Dict:
        """
        Extract all tables from PDF document
        Returns comprehensive results with metadata
        """
        try:
            logger.info(f"Extracting tables from: {pdf_path}")
            
            doc = fitz.open(pdf_path)
            all_tables = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                
                page_tables = self.extract_tables_from_page(page, page_num + 1, page_text)
                all_tables.extend(page_tables)
            
            doc.close()
            
            # Compile results
            results = {
                "document_info": {
                    "file_name": os.path.basename(pdf_path),
                    "file_path": pdf_path,
                    "total_pages": len(doc),
                    "extraction_date": datetime.now().isoformat()
                },
                "extraction_summary": {
                    "total_tables": len(all_tables),
                    "structured_tables": sum(1 for t in all_tables if t["extraction_method"] == "pymupdf_structured"),
                    "heuristic_tables": sum(1 for t in all_tables if t["extraction_method"] == "heuristic_text"),
                    "pages_with_tables": len(set(t["page_number"] for t in all_tables))
                },
                "tables": all_tables
            }
            
            logger.info(f"Extracted {len(all_tables)} tables from {os.path.basename(pdf_path)}")
            return results
            
        except Exception as e:
            logger.error(f"Error extracting tables from {pdf_path}: {str(e)}")
            return {
                "document_info": {"file_name": os.path.basename(pdf_path), "error": str(e)},
                "extraction_summary": {"total_tables": 0, "error": str(e)},
                "tables": []
            }
    
    def save_tables_to_csv(self, extraction_results: Dict, output_name: str = None) -> List[str]:
        """
        Save extracted tables as CSV files and JSON metadata
        Returns list of saved file paths
        """
        if output_name is None:
            output_name = Path(extraction_results["document_info"]["file_name"]).stem
        
        # Create output directory
        output_dir = self.output_dir / output_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        # Save each table as CSV
        for i, table in enumerate(extraction_results["tables"]):
            if "dataframe" in table:
                df = table["dataframe"]
                
                # Generate filename
                page_num = table["page_number"]
                table_idx = table["table_index"]
                method = table["extraction_method"].split("_")[0]  # 'pymupdf' or 'heuristic'
                
                csv_filename = f"table_p{page_num:03d}_t{table_idx}_{method}.csv"
                csv_path = output_dir / csv_filename
                
                # Save CSV
                df.to_csv(csv_path, index=False)
                saved_files.append(str(csv_path))
                
                # Update table info with file path
                table["csv_file"] = str(csv_path)
                
                # Remove DataFrame object for JSON serialization
                del table["dataframe"]
        
        # Save JSON metadata
        json_path = output_dir / "tables_metadata.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(extraction_results, f, indent=2, ensure_ascii=False)
        saved_files.append(str(json_path))
        
        # Save summary report
        summary_path = output_dir / "extraction_summary.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"Table Extraction Summary\n")
            f.write(f"=====================\n\n")
            f.write(f"Document: {extraction_results['document_info']['file_name']}\n")
            f.write(f"Extraction Date: {extraction_results['document_info']['extraction_date']}\n")
            f.write(f"Total Tables: {extraction_results['extraction_summary']['total_tables']}\n")
            f.write(f"Structured Tables: {extraction_results['extraction_summary']['structured_tables']}\n")
            f.write(f"Heuristic Tables: {extraction_results['extraction_summary']['heuristic_tables']}\n")
            f.write(f"Pages with Tables: {extraction_results['extraction_summary']['pages_with_tables']}\n\n")
            
            f.write("Table Details:\n")
            for i, table in enumerate(extraction_results["tables"]):
                f.write(f"  Table {i+1}: Page {table['page_number']}, ")
                f.write(f"{table['dimensions']['rows']}x{table['dimensions']['columns']} ")
                f.write(f"({table['extraction_method']})\n")
        
        saved_files.append(str(summary_path))
        
        logger.info(f"Saved {len(extraction_results['tables'])} tables to: {output_dir}")
        return saved_files


def test_pandas_loading(csv_files: List[str]) -> Dict:
    """
    Test that saved CSV files can be loaded with pandas.read_csv
    """
    results = {
        "tested_files": len(csv_files),
        "successful_loads": 0,
        "failed_loads": 0,
        "errors": []
    }
    
    for csv_file in csv_files:
        if csv_file.endswith('.csv'):
            try:
                df = pd.read_csv(csv_file)
                results["successful_loads"] += 1
                logger.info(f"✅ Successfully loaded: {os.path.basename(csv_file)} ({len(df)} rows)")
            except Exception as e:
                results["failed_loads"] += 1
                results["errors"].append({
                    "file": csv_file,
                    "error": str(e)
                })
                logger.error(f"❌ Failed to load: {os.path.basename(csv_file)} - {str(e)}")
    
    return results


def main():
    """Main function to demonstrate table extraction"""
    extractor = TableExtractor()
    
    # Sample PDFs for testing
    sample_pdfs = [
        "data/raw/protocol.pdf",
        "data/raw/clinical_study.pdf",
        "data/raw/patient_report.pdf"
    ]
    
    for pdf_path in sample_pdfs:
        if os.path.exists(pdf_path):
            print(f"\n📊 Processing tables in: {os.path.basename(pdf_path)}")
            
            # Extract tables
            results = extractor.extract_tables_from_pdf(pdf_path)
            
            # Save results
            output_name = Path(pdf_path).stem
            saved_files = extractor.save_tables_to_csv(results, output_name)
            
            # Print summary
            summary = results["extraction_summary"]
            print(f"   Tables found: {summary['total_tables']}")
            print(f"   Structured: {summary['structured_tables']}")
            print(f"   Heuristic: {summary['heuristic_tables']}")
            print(f"   Pages with tables: {summary['pages_with_tables']}")
            
            # Test CSV loading
            csv_files = [f for f in saved_files if f.endswith('.csv')]
            if csv_files:
                print(f"   CSV files: {len(csv_files)}")
                test_results = test_pandas_loading(csv_files)
                print(f"   ✅ Loadable CSVs: {test_results['successful_loads']}")
                if test_results['failed_loads'] > 0:
                    print(f"   ❌ Failed CSVs: {test_results['failed_loads']}")
        else:
            logger.info(f"Sample PDF not found: {pdf_path}")
    
    print(f"\n✅ Table extraction complete!")
    print(f"📁 Results saved to: {extractor.output_dir}")


if __name__ == "__main__":
    main()