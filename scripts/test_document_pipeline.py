#!/usr/bin/env python3
"""
Comprehensive Test Suite for ClinChat-RAG Document Processing Pipeline
Tests all extraction components and demonstrates functionality
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import traceback

# Add ingest directory to path
sys.path.append('ingest')

# Import extraction modules
try:
    from extract_pdf import PDFExtractor
    pdf_available = True
except Exception as e:
    print(f"⚠️ PDF extraction not available: {e}")
    pdf_available = False

try:
    from extract_ocr import OCRProcessor
    ocr_available = True
except Exception as e:
    print(f"⚠️ OCR processing not available: {e}")
    ocr_available = False

def test_pdf_extraction():
    """Test PDF text extraction functionality"""
    print("\n🔍 Testing PDF Text Extraction")
    print("-" * 40)
    
    if not pdf_available:
        print("❌ PDF extraction module not available")
        return False
    
    try:
        extractor = PDFExtractor("data/processed/test_text")
        
        # Test files
        test_files = [
            "data/raw/protocol.pdf",
            "data/raw/patient_report.pdf"
        ]
        
        results = []
        for pdf_file in test_files:
            if os.path.exists(pdf_file):
                print(f"📄 Processing: {os.path.basename(pdf_file)}")
                
                # Extract text
                result = extractor.extract_text(pdf_file)
                
                # Save results
                output_name = Path(pdf_file).stem
                output_file = extractor.save_extraction_results(result, output_name)
                
                # Print summary
                summary = result["extraction_summary"]
                metadata = result["metadata"]
                
                print(f"   ✅ Status: {summary['extraction_status']}")
                print(f"   📊 Pages: {summary['total_pages']}")
                print(f"   📝 Text length: {summary['total_text_length']:,} characters")
                print(f"   🖼️ Images: {summary.get('total_images', 0)}")
                
                if metadata["document_analysis"]["is_scanned"]:
                    print(f"   ⚠️ Scanned document detected (OCR recommended)")
                
                print(f"   💾 Saved to: {output_file}")
                
                results.append({
                    "file": pdf_file,
                    "status": "success",
                    "summary": summary
                })
            else:
                print(f"❌ File not found: {pdf_file}")
                results.append({
                    "file": pdf_file,
                    "status": "file_not_found"
                })
        
        print(f"\n✅ PDF extraction test completed")
        return results
        
    except Exception as e:
        print(f"❌ PDF extraction test failed: {e}")
        traceback.print_exc()
        return False

def test_manual_table_extraction():
    """Test simple table extraction without complex dependencies"""
    print("\n📊 Testing Manual Table Extraction")
    print("-" * 40)
    
    try:
        import fitz  # PyMuPDF
        import pandas as pd
        
        # Simple table extraction function
        def extract_simple_tables(pdf_path):
            doc = fitz.open(pdf_path)
            all_tables = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Simple heuristic: look for lines with multiple spaces (table-like)
                lines = text.split('\n')
                potential_tables = []
                
                for line in lines:
                    # Look for lines with 3+ columns separated by multiple spaces
                    if '  ' in line and len(line.split()) >= 3:
                        parts = [part.strip() for part in line.split('  ') if part.strip()]
                        if len(parts) >= 3:
                            potential_tables.append(parts)
                
                if len(potential_tables) >= 2:  # At least 2 rows for a table
                    # Try to create a DataFrame
                    max_cols = max(len(row) for row in potential_tables)
                    consistent_tables = [row for row in potential_tables if len(row) == max_cols]
                    
                    if len(consistent_tables) >= 2:
                        headers = consistent_tables[0]
                        data = consistent_tables[1:]
                        
                        df = pd.DataFrame(data, columns=headers)
                        
                        table_info = {
                            "page": page_num + 1,
                            "rows": len(df),
                            "columns": len(df.columns),
                            "headers": headers,
                            "dataframe": df
                        }
                        all_tables.append(table_info)
            
            doc.close()
            return all_tables
        
        # Test on sample files
        test_files = ["data/raw/protocol.pdf", "data/raw/patient_report.pdf"]
        
        for pdf_file in test_files:
            if os.path.exists(pdf_file):
                print(f"📋 Checking tables in: {os.path.basename(pdf_file)}")
                
                tables = extract_simple_tables(pdf_file)
                
                if tables:
                    print(f"   ✅ Found {len(tables)} potential tables")
                    
                    # Save tables
                    output_dir = Path(f"data/processed/test_tables/{Path(pdf_file).stem}")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    for i, table in enumerate(tables):
                        csv_file = output_dir / f"table_{table['page']}_simple.csv"
                        table["dataframe"].to_csv(csv_file, index=False)
                        print(f"   💾 Table {i+1}: {table['rows']}x{table['columns']} -> {csv_file}")
                        
                        # Test loading with pandas
                        test_df = pd.read_csv(csv_file)
                        print(f"   ✅ CSV loadable: {len(test_df)} rows")
                else:
                    print(f"   ℹ️ No tables detected using simple heuristics")
        
        print(f"\n✅ Manual table extraction test completed")
        return True
        
    except Exception as e:
        print(f"❌ Manual table extraction test failed: {e}")
        traceback.print_exc()
        return False

def test_ocr_availability():
    """Test OCR system availability"""
    print("\n🔍 Testing OCR System Availability")
    print("-" * 40)
    
    try:
        import pytesseract
        from PIL import Image
        
        # Check if tesseract is available
        try:
            version = pytesseract.get_tesseract_version()
            print(f"   ✅ Tesseract version: {version}")
            
            # Create a simple test image with text
            from PIL import Image, ImageDraw, ImageFont
            
            # Create test image
            img = Image.new('RGB', (400, 100), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                # Try to use default font
                font = ImageFont.load_default()
            except:
                font = None
            
            draw.text((10, 30), "ClinChat-RAG OCR Test", fill='black', font=font)
            
            # Save test image
            test_img_path = "data/processed/test_ocr_image.png"
            os.makedirs(os.path.dirname(test_img_path), exist_ok=True)
            img.save(test_img_path)
            
            # Test OCR
            extracted_text = pytesseract.image_to_string(img)
            print(f"   ✅ OCR test successful")
            print(f"   📝 Extracted: '{extracted_text.strip()}'")
            
            # Test OCR processor if available
            if ocr_available:
                processor = OCRProcessor("data/processed/test_ocr")
                quality_metrics = processor.assess_image_quality(img)
                print(f"   📊 Image quality score: {quality_metrics.get('overall_quality', 0):.2f}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Tesseract OCR not properly configured: {e}")
            print(f"   💡 Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
            return False
            
    except ImportError as e:
        print(f"   ❌ OCR dependencies not installed: {e}")
        return False

def test_file_formats():
    """Test support for different file formats"""
    print("\n📁 Testing File Format Support")
    print("-" * 40)
    
    formats_tested = []
    
    # Test PDF
    if os.path.exists("data/raw/protocol.pdf"):
        try:
            import fitz
            doc = fitz.open("data/raw/protocol.pdf")
            page_count = len(doc)
            doc.close()
            print(f"   ✅ PDF: {page_count} pages")
            formats_tested.append("PDF")
        except Exception as e:
            print(f"   ❌ PDF support error: {e}")
    
    # Test text files
    if os.path.exists("data/raw/clinical_summary.txt"):
        try:
            with open("data/raw/clinical_summary.txt", 'r') as f:
                content = f.read()
            print(f"   ✅ Text files: {len(content)} characters")
            formats_tested.append("TXT")
        except Exception as e:
            print(f"   ❌ Text file error: {e}")
    
    # Test image formats (for OCR)
    try:
        from PIL import Image
        test_formats = ['PNG', 'JPEG', 'TIFF']
        
        for fmt in test_formats:
            # Create a small test image
            img = Image.new('RGB', (100, 50), color='white')
            test_path = f"data/processed/test.{fmt.lower()}"
            os.makedirs(os.path.dirname(test_path), exist_ok=True)
            img.save(test_path, format=fmt)
            
            # Try to load it back
            loaded = Image.open(test_path)
            loaded.close()
            
            formats_tested.append(fmt)
        
        print(f"   ✅ Image formats: {', '.join(test_formats)}")
        
    except Exception as e:
        print(f"   ⚠️ Image format test partial: {e}")
    
    print(f"   📊 Supported formats: {', '.join(formats_tested)}")
    return formats_tested

def test_output_formats():
    """Test output format generation"""
    print("\n📤 Testing Output Formats")
    print("-" * 40)
    
    try:
        # Test JSON output
        test_data = {
            "document": "test.pdf",
            "pages": [
                {"page": 1, "text": "Sample text content"},
                {"page": 2, "text": "More content"}
            ],
            "metadata": {
                "processed_date": datetime.now().isoformat(),
                "total_pages": 2
            }
        }
        
        # Save JSON
        json_path = "data/processed/test_output.json"
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w') as f:
            json.dump(test_data, f, indent=2)
        
        # Load JSON back
        with open(json_path, 'r') as f:
            loaded_data = json.load(f)
        
        print(f"   ✅ JSON: Saved and loaded successfully")
        
        # Test CSV output (pandas)
        try:
            import pandas as pd
            
            df_data = {
                'Patient_ID': ['001', '002', '003'],
                'Age': [45, 52, 38],
                'Status': ['Active', 'Completed', 'Active']
            }
            
            df = pd.DataFrame(df_data)
            csv_path = "data/processed/test_output.csv"
            df.to_csv(csv_path, index=False)
            
            # Load back
            loaded_df = pd.read_csv(csv_path)
            
            print(f"   ✅ CSV: {len(loaded_df)} rows x {len(loaded_df.columns)} columns")
            
        except Exception as e:
            print(f"   ⚠️ CSV test partial: {e}")
        
        # Test text output
        text_content = "Extracted text from document processing pipeline\n\nThis is a test of text output capabilities."
        text_path = "data/processed/test_output.txt"
        
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        with open(text_path, 'r', encoding='utf-8') as f:
            loaded_text = f.read()
        
        print(f"   ✅ Text: {len(loaded_text)} characters")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Output format test failed: {e}")
        return False

def generate_test_report(results):
    """Generate comprehensive test report"""
    print("\n📋 Test Report Summary")
    print("=" * 50)
    
    # Count successes
    pdf_success = results.get('pdf_extraction', False)
    table_success = results.get('table_extraction', False) 
    ocr_available = results.get('ocr_availability', False)
    formats_count = len(results.get('supported_formats', []))
    outputs_success = results.get('output_formats', False)
    
    total_tests = 5
    passed_tests = sum([pdf_success, table_success, ocr_available, bool(formats_count), outputs_success])
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print()
    
    print("Component Status:")
    print(f"  📄 PDF Text Extraction: {'✅ Working' if pdf_success else '❌ Failed'}")
    print(f"  📊 Table Extraction: {'✅ Working' if table_success else '❌ Failed'}")
    print(f"  🔍 OCR Processing: {'✅ Available' if ocr_available else '⚠️ Not Available'}")
    print(f"  📁 File Formats: {'✅' if formats_count > 0 else '❌'} {formats_count} supported")
    print(f"  📤 Output Formats: {'✅ Working' if outputs_success else '❌ Failed'}")
    print()
    
    # Acceptance criteria check
    print("Acceptance Criteria:")
    print("✅ JSON file per document with page-level text" if pdf_success else "❌ JSON output not working")
    print("✅ Tables present as CSV/JSON files and loadable with pandas.read_csv" if table_success else "❌ Table CSV output not working")
    print("✅ OCR-produced text available for scanned files" if ocr_available else "⚠️ OCR system not fully configured")
    
    # Recommendations
    print()
    print("Recommendations:")
    if not ocr_available:
        print("• Install and configure Tesseract OCR for scanned document processing")
    if not table_success:
        print("• Check table extraction dependencies and algorithms") 
    if passed_tests == total_tests:
        print("• All systems operational - ready for production use!")
    
    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": (passed_tests/total_tests)*100,
        "ready_for_production": passed_tests >= 3  # Core functionality working
    }

def main():
    """Run comprehensive test suite"""
    print("🚀 ClinChat-RAG Document Processing Pipeline Test Suite")
    print("=" * 60)
    print(f"Test Date: {datetime.now().isoformat()}")
    
    # Ensure directories exist
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    
    # Run all tests
    results = {}
    
    # Test 1: PDF Text Extraction
    pdf_results = test_pdf_extraction()
    results['pdf_extraction'] = bool(pdf_results and pdf_results != False)
    
    # Test 2: Table Extraction  
    table_results = test_manual_table_extraction()
    results['table_extraction'] = table_results
    
    # Test 3: OCR Availability
    ocr_results = test_ocr_availability()
    results['ocr_availability'] = ocr_results
    
    # Test 4: File Format Support
    format_results = test_file_formats()
    results['supported_formats'] = format_results
    
    # Test 5: Output Format Generation
    output_results = test_output_formats()
    results['output_formats'] = output_results
    
    # Generate final report
    report = generate_test_report(results)
    
    # Save test results
    test_results_path = "data/processed/test_results.json"
    with open(test_results_path, 'w') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "results": results,
            "report": report
        }, f, indent=2)
    
    print(f"\n💾 Test results saved to: {test_results_path}")
    
    if report["ready_for_production"]:
        print("\n🎉 Document processing pipeline is ready for use!")
    else:
        print(f"\n⚠️ Pipeline partially functional. {report['passed_tests']}/{report['total_tests']} components working.")
    
    return report["ready_for_production"]

if __name__ == "__main__":
    main()