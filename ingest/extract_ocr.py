#!/usr/bin/env python3
"""
OCR Fallback System for ClinChat-RAG
Tesseract OCR pipeline for scanned documents with quality detection
Integrated with PDF extraction and table processing
"""

import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging
import cv2

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Advanced OCR processing with quality detection and enhancement"""
    
    def __init__(self, output_dir: str = "data/processed/ocr"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if Tesseract is available
        try:
            pytesseract.get_tesseract_version()
            self.tesseract_available = True
            logger.info("Tesseract OCR is available")
        except Exception as e:
            self.tesseract_available = False
            logger.warning(f"Tesseract OCR not available: {e}")
    
    def assess_image_quality(self, image: Image.Image) -> Dict:
        """
        Assess image quality for OCR processing
        Returns metrics about image suitability for OCR
        """
        try:
            # Convert to numpy array for analysis
            img_array = np.array(image.convert('L'))  # Convert to grayscale
            
            # Calculate various quality metrics
            metrics = {
                "resolution": {
                    "width": image.width,
                    "height": image.height,
                    "total_pixels": image.width * image.height
                },
                "contrast": float(np.std(img_array)),
                "brightness": float(np.mean(img_array)),
                "sharpness": self._calculate_sharpness(img_array),
                "noise_level": self._estimate_noise(img_array),
                "text_area_ratio": self._estimate_text_coverage(img_array)
            }
            
            # Overall quality score (0-1)
            quality_score = self._calculate_quality_score(metrics)
            metrics["overall_quality"] = quality_score
            
            # Recommendations
            metrics["recommendations"] = self._get_enhancement_recommendations(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error assessing image quality: {e}")
            return {"error": str(e), "overall_quality": 0.0}
    
    def _calculate_sharpness(self, img_array: np.ndarray) -> float:
        """Calculate image sharpness using Laplacian variance"""
        try:
            laplacian = cv2.Laplacian(img_array, cv2.CV_64F)
            return float(laplacian.var())
        except Exception:
            # Fallback method
            kernel = np.array([[-1,-1,-1], [-1,8,-1], [-1,-1,-1]])
            filtered = cv2.filter2D(img_array, -1, kernel)
            return float(np.var(filtered))
    
    def _estimate_noise(self, img_array: np.ndarray) -> float:
        """Estimate noise level in the image"""
        try:
            # Use median filter to estimate noise
            filtered = cv2.medianBlur(img_array, 5)
            noise = np.std(img_array - filtered)
            return float(noise)
        except Exception:
            return 0.0
    
    def _estimate_text_coverage(self, img_array: np.ndarray) -> float:
        """Estimate what percentage of image contains text"""
        try:
            # Simple text area estimation using edge detection
            edges = cv2.Canny(img_array, 50, 150)
            text_pixels = np.sum(edges > 0)
            total_pixels = img_array.size
            return float(text_pixels / total_pixels) if total_pixels > 0 else 0.0
        except Exception:
            return 0.0
    
    def _calculate_quality_score(self, metrics: Dict) -> float:
        """Calculate overall quality score from individual metrics"""
        try:
            # Normalize metrics to 0-1 scale
            resolution_score = min(1.0, metrics["resolution"]["total_pixels"] / (1920 * 1080))
            contrast_score = min(1.0, metrics["contrast"] / 100)
            brightness_score = 1.0 - abs(metrics["brightness"] - 127) / 127  # Optimal around 127
            sharpness_score = min(1.0, metrics["sharpness"] / 1000)
            noise_score = max(0.0, 1.0 - metrics["noise_level"] / 50)
            
            # Weighted combination
            weights = {
                "resolution": 0.2,
                "contrast": 0.25,
                "brightness": 0.15,
                "sharpness": 0.25,
                "noise": 0.15
            }
            
            quality_score = (
                resolution_score * weights["resolution"] +
                contrast_score * weights["contrast"] +
                brightness_score * weights["brightness"] +
                sharpness_score * weights["sharpness"] +
                noise_score * weights["noise"]
            )
            
            return round(quality_score, 3)
            
        except Exception:
            return 0.5  # Default middle score
    
    def _get_enhancement_recommendations(self, metrics: Dict) -> List[str]:
        """Generate recommendations for image enhancement"""
        recommendations = []
        
        if metrics["contrast"] < 30:
            recommendations.append("increase_contrast")
        
        if metrics["brightness"] < 50 or metrics["brightness"] > 200:
            recommendations.append("adjust_brightness")
        
        if metrics["sharpness"] < 100:
            recommendations.append("enhance_sharpness")
        
        if metrics["noise_level"] > 20:
            recommendations.append("reduce_noise")
        
        if metrics["resolution"]["total_pixels"] < 300000:  # Less than ~550x550
            recommendations.append("increase_resolution")
        
        return recommendations
    
    def enhance_image_for_ocr(self, image: Image.Image, recommendations: List[str] = None) -> Image.Image:
        """
        Enhance image for better OCR results based on quality assessment
        """
        try:
            enhanced = image.copy()
            
            if recommendations is None:
                quality_metrics = self.assess_image_quality(image)
                recommendations = quality_metrics.get("recommendations", [])
            
            # Apply enhancements based on recommendations
            if "adjust_brightness" in recommendations:
                enhancer = ImageEnhance.Brightness(enhanced)
                enhanced = enhancer.enhance(1.2)  # Increase brightness slightly
            
            if "increase_contrast" in recommendations:
                enhancer = ImageEnhance.Contrast(enhanced)
                enhanced = enhancer.enhance(1.5)  # Increase contrast
            
            if "enhance_sharpness" in recommendations:
                enhancer = ImageEnhance.Sharpness(enhanced)
                enhanced = enhancer.enhance(2.0)  # Enhance sharpness
            
            if "reduce_noise" in recommendations:
                enhanced = enhanced.filter(ImageFilter.MedianFilter(size=3))
            
            # Convert to grayscale if not already
            if enhanced.mode != 'L':
                enhanced = enhanced.convert('L')
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            return image
    
    def extract_text_from_image(self, image: Image.Image, lang: str = 'eng') -> Dict:
        """
        Extract text from image using Tesseract OCR
        Returns text with confidence and word-level details
        """
        if not self.tesseract_available:
            return {
                "text": "",
                "confidence": 0.0,
                "error": "Tesseract OCR not available",
                "word_count": 0
            }
        
        try:
            # Configure Tesseract for better accuracy
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?;:()\-+= '
            
            # Extract text
            text = pytesseract.image_to_string(image, lang=lang, config=custom_config)
            
            # Get detailed data with confidence
            data = pytesseract.image_to_data(image, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Count words with decent confidence
            good_words = sum(1 for conf in confidences if conf > 30)
            
            # Extract word-level information
            words_info = []
            for i in range(len(data['text'])):
                if data['conf'][i] > 0 and data['text'][i].strip():
                    words_info.append({
                        "text": data['text'][i],
                        "confidence": data['conf'][i],
                        "bbox": {
                            "left": data['left'][i],
                            "top": data['top'][i],
                            "width": data['width'][i],
                            "height": data['height'][i]
                        }
                    })
            
            return {
                "text": text.strip(),
                "confidence": round(avg_confidence, 2),
                "word_count": good_words,
                "total_words_detected": len([w for w in data['text'] if w.strip()]),
                "words_info": words_info,
                "extraction_successful": len(text.strip()) > 0
            }
            
        except Exception as e:
            logger.error(f"Error during OCR extraction: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "error": str(e),
                "word_count": 0,
                "extraction_successful": False
            }
    
    def process_pdf_page_ocr(self, page: fitz.Page, page_num: int) -> Dict:
        """
        Process a single PDF page with OCR
        Handles both text and image content
        """
        page_result = {
            "page_number": page_num,
            "ocr_results": [],
            "combined_text": "",
            "processing_summary": {
                "images_processed": 0,
                "text_extracted": False,
                "average_confidence": 0.0
            }
        }
        
        try:
            # Get existing text first
            existing_text = page.get_text().strip()
            
            # If page has substantial text, OCR may not be needed
            if len(existing_text) > 50:
                page_result["combined_text"] = existing_text
                page_result["processing_summary"]["text_extracted"] = True
                page_result["processing_summary"]["source"] = "native_text"
                return page_result
            
            # Convert page to image for OCR
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_data))
            
            # Assess image quality
            quality_metrics = self.assess_image_quality(image)
            
            # Enhance image if needed
            enhanced_image = self.enhance_image_for_ocr(image, quality_metrics.get("recommendations", []))
            
            # Perform OCR
            ocr_result = self.extract_text_from_image(enhanced_image)
            
            ocr_result["quality_metrics"] = quality_metrics
            ocr_result["enhancement_applied"] = quality_metrics.get("recommendations", [])
            
            page_result["ocr_results"].append(ocr_result)
            page_result["combined_text"] = ocr_result["text"]
            page_result["processing_summary"]["images_processed"] = 1
            page_result["processing_summary"]["text_extracted"] = ocr_result["extraction_successful"]
            page_result["processing_summary"]["average_confidence"] = ocr_result["confidence"]
            page_result["processing_summary"]["source"] = "ocr"
            
        except Exception as e:
            logger.error(f"Error processing page {page_num} with OCR: {e}")
            page_result["error"] = str(e)
        
        return page_result
    
    def process_pdf_with_ocr(self, pdf_path: str) -> Dict:
        """
        Process entire PDF document with OCR fallback
        Automatically detects which pages need OCR
        """
        try:
            logger.info(f"Processing PDF with OCR: {pdf_path}")
            
            doc = fitz.open(pdf_path)
            all_pages = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_result = self.process_pdf_page_ocr(page, page_num + 1)
                all_pages.append(page_result)
            
            doc.close()
            
            # Compile results
            results = {
                "document_info": {
                    "file_name": os.path.basename(pdf_path),
                    "file_path": pdf_path,
                    "total_pages": len(all_pages),
                    "processing_date": datetime.now().isoformat()
                },
                "processing_summary": {
                    "pages_processed": len(all_pages),
                    "pages_with_ocr": sum(1 for p in all_pages if p["processing_summary"]["source"] == "ocr"),
                    "pages_with_native_text": sum(1 for p in all_pages if p["processing_summary"]["source"] == "native_text"),
                    "total_text_length": sum(len(p["combined_text"]) for p in all_pages),
                    "average_confidence": self._calculate_average_confidence(all_pages)
                },
                "pages": all_pages
            }
            
            logger.info(f"OCR processing complete: {len(all_pages)} pages processed")
            return results
            
        except Exception as e:
            logger.error(f"Error processing PDF with OCR: {e}")
            return {
                "document_info": {"file_name": os.path.basename(pdf_path), "error": str(e)},
                "processing_summary": {"error": str(e)},
                "pages": []
            }
    
    def _calculate_average_confidence(self, pages: List[Dict]) -> float:
        """Calculate average OCR confidence across all pages"""
        ocr_pages = [p for p in pages if p["processing_summary"]["source"] == "ocr"]
        if not ocr_pages:
            return 100.0  # If no OCR was used, assume high confidence
        
        confidences = [p["processing_summary"]["average_confidence"] for p in ocr_pages]
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def save_ocr_results(self, ocr_results: Dict, output_name: str = None) -> List[str]:
        """Save OCR results to files"""
        if output_name is None:
            output_name = Path(ocr_results["document_info"]["file_name"]).stem
        
        # Create output directory
        output_dir = self.output_dir / output_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        # Save complete results as JSON
        json_path = output_dir / "ocr_results.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ocr_results, f, indent=2, ensure_ascii=False)
        saved_files.append(str(json_path))
        
        # Save combined text file
        text_path = output_dir / "extracted_text.txt"
        with open(text_path, "w", encoding="utf-8") as f:
            for page in ocr_results["pages"]:
                f.write(f"=== Page {page['page_number']} ===\n")
                f.write(page["combined_text"])
                f.write("\n\n")
        saved_files.append(str(text_path))
        
        # Save individual page text files
        pages_dir = output_dir / "pages"
        pages_dir.mkdir(exist_ok=True)
        
        for page in ocr_results["pages"]:
            page_num = page["page_number"]
            page_file = pages_dir / f"page_{page_num:03d}_ocr.txt"
            with open(page_file, "w", encoding="utf-8") as f:
                f.write(page["combined_text"])
            saved_files.append(str(page_file))
        
        # Save processing summary
        summary_path = output_dir / "ocr_summary.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            summary = ocr_results["processing_summary"]
            f.write("OCR Processing Summary\n")
            f.write("====================\n\n")
            f.write(f"Document: {ocr_results['document_info']['file_name']}\n")
            f.write(f"Processing Date: {ocr_results['document_info']['processing_date']}\n")
            f.write(f"Total Pages: {summary['pages_processed']}\n")
            f.write(f"Pages with OCR: {summary['pages_with_ocr']}\n")
            f.write(f"Pages with Native Text: {summary['pages_with_native_text']}\n")
            f.write(f"Total Text Length: {summary['total_text_length']:,} characters\n")
            f.write(f"Average OCR Confidence: {summary['average_confidence']:.1f}%\n")
        
        saved_files.append(str(summary_path))
        
        logger.info(f"Saved OCR results to: {output_dir}")
        return saved_files


def main():
    """Main function to demonstrate OCR processing"""
    ocr_processor = OCRProcessor()
    
    if not ocr_processor.tesseract_available:
        print("⚠️ Tesseract OCR not available. Please install tesseract-ocr.")
        print("Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("Linux: sudo apt-get install tesseract-ocr")
        print("Mac: brew install tesseract")
        return
    
    # Sample PDFs for testing
    sample_pdfs = [
        "data/raw/protocol.pdf",
        "data/raw/scanned_document.pdf",
        "data/raw/mixed_content.pdf"
    ]
    
    for pdf_path in sample_pdfs:
        if os.path.exists(pdf_path):
            print(f"\n🔍 Processing with OCR: {os.path.basename(pdf_path)}")
            
            # Process with OCR
            results = ocr_processor.process_pdf_with_ocr(pdf_path)
            
            # Save results
            output_name = Path(pdf_path).stem
            saved_files = ocr_processor.save_ocr_results(results, output_name)
            
            # Print summary
            summary = results["processing_summary"]
            print(f"   Pages processed: {summary['pages_processed']}")
            print(f"   OCR pages: {summary['pages_with_ocr']}")
            print(f"   Native text pages: {summary['pages_with_native_text']}")
            print(f"   Total text: {summary['total_text_length']:,} chars")
            print(f"   OCR confidence: {summary['average_confidence']:.1f}%")
            print(f"   Files saved: {len(saved_files)}")
        else:
            logger.info(f"Sample PDF not found: {pdf_path}")
    
    print("\n✅ OCR processing complete!")
    print(f"📁 Results saved to: {ocr_processor.output_dir}")


if __name__ == "__main__":
    main()