#!/usr/bin/env python3
"""
ClinChat-RAG Text Chunking Module
================================

This module provides intelligent text chunking capabilities for medical documents
with semantic awareness and metadata preservation.
"""

import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, NamedTuple
from dataclasses import dataclass

@dataclass
class TextChunk:
    """Represents a text chunk with associated metadata"""
    text: str
    doc_id: str
    chunk_id: str
    start_char: int
    end_char: int
    page: Optional[int] = None
    section: Optional[str] = None
    word_count: int = 0
    char_count: int = 0
    
    def __post_init__(self):
        """Calculate derived fields after initialization"""
        if not self.word_count:
            self.word_count = len(self.text.split())
        if not self.char_count:
            self.char_count = len(self.text)

class MedicalChunker:
    """
    Intelligent chunker for medical documents with semantic awareness
    """
    
    def __init__(self, max_chars: int = 3000, min_chars: int = 100):
        """
        Initialize the chunker
        
        Args:
            max_chars: Maximum characters per chunk
            min_chars: Minimum characters per chunk (to avoid tiny chunks)
        """
        self.max_chars = max_chars
        self.min_chars = min_chars
        
        # Medical section headers to detect semantic boundaries
        self.section_patterns = [
            r'^(?:CHIEF COMPLAINT|CC):?',
            r'^(?:HISTORY OF PRESENT ILLNESS|HPI):?',
            r'^(?:PAST MEDICAL HISTORY|PMH):?',
            r'^(?:MEDICATIONS?|MEDS):?',
            r'^(?:ALLERGIES?):?',
            r'^(?:SOCIAL HISTORY|SH):?',
            r'^(?:FAMILY HISTORY|FH):?',
            r'^(?:REVIEW OF SYSTEMS|ROS):?',
            r'^(?:PHYSICAL EXAM?(?:INATION)?|PE):?',
            r'^(?:ASSESSMENT|IMPRESSION):?',
            r'^(?:PLAN|TREATMENT):?',
            r'^(?:DISCHARGE SUMMARY):?',
            r'^(?:HOSPITAL COURSE):?',
            r'^(?:LABORATORY|LAB):?',
            r'^(?:IMAGING|RADIOLOGY):?',
            r'^(?:VITAL SIGNS|VITALS):?',
            r'^(?:DISCHARGE MEDICATIONS?):?',
            r'^(?:FOLLOW[- ]?UP):?',
            r'^(?:DIAGNOSIS|DIAGNOSES):?',
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                                 for pattern in self.section_patterns]
    
    def detect_section(self, text: str) -> Optional[str]:
        """
        Detect the medical section type for a given text chunk
        
        Args:
            text: Text to analyze for section headers
            
        Returns:
            Section name if detected, None otherwise
        """
        # Look at the first few lines for section headers
        first_lines = text.strip().split('\n')[:3]
        header_text = '\n'.join(first_lines)
        
        for pattern in self.compiled_patterns:
            match = pattern.search(header_text)
            if match:
                # Extract clean section name
                section = match.group().upper().strip(':').strip()
                return section
        
        return None
    
    def chunk_text(self, text: str, doc_id: str, page: int = None) -> List[TextChunk]:
        """
        Chunk text using semantic and size-based splitting
        
        Args:
            text: Input text to chunk
            doc_id: Document identifier
            page: Optional page number
            
        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []
        
        # First, try to split by paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        if not paragraphs:
            # Fallback to single paragraph
            paragraphs = [text.strip()]
        
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_counter = 1
        
        for paragraph in paragraphs:
            # Check if adding this paragraph would exceed max_chars
            potential_chunk = (current_chunk + "\n\n" + paragraph).strip() if current_chunk else paragraph
            
            if len(potential_chunk) > self.max_chars and current_chunk:
                # Save current chunk and start new one
                if len(current_chunk.strip()) >= self.min_chars:
                    chunk = self._create_chunk(
                        text=current_chunk.strip(),
                        doc_id=doc_id,
                        chunk_counter=chunk_counter,
                        start_char=current_start,
                        page=page
                    )
                    chunks.append(chunk)
                    chunk_counter += 1
                
                # Start new chunk with current paragraph
                current_chunk = paragraph
                current_start = self._find_start_position(text, current_chunk, current_start)
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk = current_chunk + "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                    current_start = self._find_start_position(text, current_chunk, 0)
        
        # Add the last chunk if it exists
        if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chars:
            chunk = self._create_chunk(
                text=current_chunk.strip(),
                doc_id=doc_id,
                chunk_counter=chunk_counter,
                start_char=current_start,
                page=page
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, text: str, doc_id: str, chunk_counter: int, 
                     start_char: int, page: Optional[int] = None) -> TextChunk:
        """Create a TextChunk with computed metadata"""
        
        # Generate unique chunk ID
        chunk_id = f"{doc_id}_chunk_{chunk_counter:03d}"
        
        # Detect section
        section = self.detect_section(text)
        
        # Calculate end character position
        end_char = start_char + len(text)
        
        return TextChunk(
            text=text,
            doc_id=doc_id,
            chunk_id=chunk_id,
            start_char=start_char,
            end_char=end_char,
            page=page,
            section=section,
            word_count=len(text.split()),
            char_count=len(text)
        )
    
    def _find_start_position(self, full_text: str, chunk_text: str, start_from: int = 0) -> int:
        """Find the starting position of chunk_text in full_text"""
        try:
            # Look for the chunk text starting from the given position
            position = full_text.find(chunk_text.strip()[:50], start_from)
            return position if position != -1 else start_from
        except Exception:
            return start_from

class ChunkStorage:
    """Handles storage and retrieval of text chunks in JSONL format"""
    
    def __init__(self, output_dir: str = "data/processed/chunks"):
        """
        Initialize chunk storage
        
        Args:
            output_dir: Directory to store chunk files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_chunks(self, chunks: List[TextChunk], filename: str = None) -> Path:
        """
        Save chunks to JSONL file
        
        Args:
            chunks: List of TextChunk objects to save
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if not chunks:
            raise ValueError("No chunks to save")
        
        # Generate filename if not provided
        if not filename:
            doc_id = chunks[0].doc_id
            filename = f"{doc_id}_chunks.jsonl"
        
        output_file = self.output_dir / filename
        
        # Write chunks as JSONL (one JSON object per line)
        with open(output_file, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                chunk_dict = {
                    'text': chunk.text,
                    'doc_id': chunk.doc_id,
                    'chunk_id': chunk.chunk_id,
                    'start_char': chunk.start_char,
                    'end_char': chunk.end_char,
                    'page': chunk.page,
                    'section': chunk.section,
                    'word_count': chunk.word_count,
                    'char_count': chunk.char_count,
                    'metadata': {
                        'created_at': '2025-10-19T15:30:00Z',
                        'chunker_version': '1.0.0',
                        'max_chars': getattr(self, 'max_chars', 3000)
                    }
                }
                f.write(json.dumps(chunk_dict) + '\n')
        
        return output_file
    
    def load_chunks(self, filename: str) -> List[TextChunk]:
        """
        Load chunks from JSONL file
        
        Args:
            filename: Name of file to load
            
        Returns:
            List of TextChunk objects
        """
        file_path = self.output_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Chunk file not found: {file_path}")
        
        chunks = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    chunk = TextChunk(
                        text=data['text'],
                        doc_id=data['doc_id'],
                        chunk_id=data['chunk_id'],
                        start_char=data['start_char'],
                        end_char=data['end_char'],
                        page=data['page'],
                        section=data['section'],
                        word_count=data['word_count'],
                        char_count=data['char_count']
                    )
                    chunks.append(chunk)
        
        return chunks

def chunk_text(text: str, max_chars: int = 3000) -> List[str]:
    """
    Simple chunking function for backward compatibility
    
    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk
        
    Returns:
        List of text chunks
    """
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    chunks = []
    cur = ""
    
    for p in paragraphs:
        if len(cur) + len(p) > max_chars:
            if cur:
                chunks.append(cur.strip())
            cur = p
        else:
            cur = (cur + "\n\n" + p).strip() if cur else p
    
    if cur:
        chunks.append(cur.strip())
    
    return chunks

# Convenience functions
def create_chunker(max_chars: int = 3000, min_chars: int = 100) -> MedicalChunker:
    """Create a medical chunker with specified parameters"""
    return MedicalChunker(max_chars=max_chars, min_chars=min_chars)

def process_document(text: str, doc_id: str, output_dir: str = "data/processed/chunks", 
                    max_chars: int = 3000, page: int = None) -> List[TextChunk]:
    """
    Process a document into chunks and save to JSONL
    
    Args:
        text: Document text to process
        doc_id: Document identifier
        output_dir: Output directory for chunks
        max_chars: Maximum characters per chunk
        page: Optional page number
        
    Returns:
        List of created chunks
    """
    # Create chunker and storage
    chunker = create_chunker(max_chars=max_chars)
    storage = ChunkStorage(output_dir)
    
    # Generate chunks
    chunks = chunker.chunk_text(text, doc_id, page)
    
    # Save chunks
    if chunks:
        output_file = storage.save_chunks(chunks)
        print(f"Saved {len(chunks)} chunks to {output_file}")
    
    return chunks

if __name__ == "__main__":
    # Demo with medical text
    sample_medical_text = """
    PATIENT MEDICAL RECORD
    ======================
    
    CHIEF COMPLAINT:
    68 year old male presents with chest pain and shortness of breath.
    
    HISTORY OF PRESENT ILLNESS:
    Patient reports onset of substernal chest pain 3 hours ago while watching TV.
    Pain is described as crushing, 8/10 severity, radiating to left arm.
    Associated with diaphoresis and nausea. No relief with rest.
    
    PAST MEDICAL HISTORY:
    - Hypertension (diagnosed 2010)
    - Type 2 Diabetes Mellitus (diagnosed 2015) 
    - Hyperlipidemia
    - Former smoker (quit 2018, 40 pack-year history)
    
    MEDICATIONS:
    - Metformin 500mg BID
    - Lisinopril 10mg daily
    - Atorvastatin 40mg HS
    - Aspirin 81mg daily
    
    PHYSICAL EXAMINATION:
    VITALS: BP 165/95, HR 102, RR 22, T 98.6°F, O2 94% on RA
    
    GENERAL: Diaphoretic, anxious appearing male in moderate distress
    CARDIOVASCULAR: Tachycardic, regular rhythm, no murmurs
    PULMONARY: Mild bibasilar crackles
    
    ASSESSMENT AND PLAN:
    1. Acute coronary syndrome - STEMI
       - Emergent cardiac catheterization
       - ASA 325mg, Plavix 600mg loading dose
       - Heparin per protocol
    
    2. Diabetes mellitus
       - Continue home medications
       - Monitor glucose closely
    """
    
    print("🔧 Testing ClinChat-RAG Chunking System")
    print("=" * 45)
    
    # Test chunking
    chunks = process_document(
        text=sample_medical_text,
        doc_id="sample_medical_record",
        max_chars=800  # Smaller chunks for demo
    )
    
    # Display results
    print(f"\n📊 Chunking Results:")
    print(f"Total chunks created: {len(chunks)}")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- Chunk {i} ---")
        print(f"ID: {chunk.chunk_id}")
        print(f"Section: {chunk.section or 'Unknown'}")
        print(f"Characters: {chunk.char_count}")
        print(f"Words: {chunk.word_count}")
        print(f"Position: {chunk.start_char}-{chunk.end_char}")
        print(f"Preview: {chunk.text[:100]}{'...' if len(chunk.text) > 100 else ''}")
    
    print(f"\n✅ Chunking system test completed!")
    print(f"📁 Chunks saved to: data/processed/chunks/")