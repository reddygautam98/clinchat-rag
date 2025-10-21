"""
Table-Aware Numeric Reasoning Module
Detects and processes numeric queries on medical tables and lab data
"""

import re
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MULTI_SPACE_PATTERN = r'\s{2,}'

class TableProcessor:
    """
    Handles detection and processing of table-based numeric queries
    """
    
    def __init__(self):
        self.setup_numeric_patterns()
        self.setup_table_patterns()
    
    def setup_numeric_patterns(self):
        """Setup patterns for detecting numeric queries"""
        
        # Numeric keywords that indicate table-based queries
        self.numeric_keywords = [
            'mean', 'average', 'avg',
            'median', 'middle',
            'mode', 'most common',
            'sum', 'total',
            'count', 'number of',
            'min', 'minimum', 'lowest',
            'max', 'maximum', 'highest',
            'range', 'spread',
            'standard deviation', 'std', 'stddev',
            'variance', 'var',
            'percentile', 'quartile',
            'lab value', 'lab values', 'laboratory',
            'blood test', 'blood work',
            'vital signs', 'vitals',
            'measurement', 'measurements',
            'reading', 'readings',
            'result', 'results',
            'level', 'levels',
            'rate', 'rates',
            'pressure', 'temperature',
            'glucose', 'cholesterol',
            'hemoglobin', 'hematocrit',
            'white blood cell', 'wbc',
            'red blood cell', 'rbc',
            'platelet', 'plt'
        ]
        
        # Medical table indicators
        self.table_indicators = [
            'table', 'chart', 'data',
            'lab report', 'lab panel',
            'blood panel', 'chemistry panel',
            'cbc', 'complete blood count',
            'bmp', 'basic metabolic panel',
            'cmp', 'comprehensive metabolic panel',
            'lipid panel', 'liver function',
            'thyroid function', 'cardiac markers'
        ]
    
    def setup_table_patterns(self):
        """Setup regex patterns for table detection"""
        
        # Common table delimiters
        self.table_delimiters = [
            r'\|',  # Pipe-separated
            r'\t',  # Tab-separated
            r',',   # Comma-separated
            r';',   # Semicolon-separated
            MULTI_SPACE_PATTERN  # Multiple spaces
        ]
        
        # Table header patterns
        self.header_patterns = [
            r'^[A-Za-z\s]+[\|\t,;]\s*[A-Za-z\s]+',  # Basic header row
            r'Test\s*[\|\t,;]\s*Value',  # Lab test format
            r'Parameter\s*[\|\t,;]\s*Result',  # Parameter format
            r'Date\s*[\|\t,;]\s*Time\s*[\|\t,;]\s*Value',  # Time series
        ]
        
        # Numeric value patterns in tables
        self.numeric_patterns = [
            r'\b\d+\.?\d*\b',  # Basic numbers
            r'\b\d+\.?\d*\s*-\s*\d+\.?\d*\b',  # Ranges (e.g., 5.0-7.0)
            r'\b\d+\.?\d*\s*[<>]\s*\d+\.?\d*\b',  # Comparisons
            r'\b\d+\.?\d*\s*mg/dL\b',  # Medical units
            r'\b\d+\.?\d*\s*mmHg\b',
            r'\b\d+\.?\d*\s*bpm\b',
            r'\b\d+\.?\d*\s*°F\b'
        ]
    
    def is_numeric_query(self, query: str) -> bool:
        """
        Detect if a query requires numeric/table processing
        
        Args:
            query: User query string
            
        Returns:
            Boolean indicating if query is numeric
        """
        
        query_lower = query.lower()
        
        # Check for numeric keywords
        has_numeric_keyword = any(keyword in query_lower for keyword in self.numeric_keywords)
        
        # Check for table indicators  
        has_table_indicator = any(indicator in query_lower for indicator in self.table_indicators)
        
        # Check for question words with numeric intent
        numeric_questions = [
            'what is the average',
            'what is the mean',
            'what is the median',
            'how many',
            'what are the values',
            'show me the numbers',
            'calculate the',
            'compute the'
        ]
        
        has_numeric_question = any(phrase in query_lower for phrase in numeric_questions)
        
        logger.info(f"Numeric query analysis: keywords={has_numeric_keyword}, "
                   f"table_indicators={has_table_indicator}, questions={has_numeric_question}")
        
        return has_numeric_keyword or has_table_indicator or has_numeric_question
    
    def extract_tables_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract table-like structures from text
        
        Args:
            text: Input text containing potential tables
            
        Returns:
            List of dictionaries containing table data and metadata
        """
        
        tables = []
        lines = text.split('\n')
        
        # Look for table patterns
        for i, line in enumerate(lines):
            if self._looks_like_table_row(line):
                # Try to extract a table starting from this line
                table_data = self._extract_table_from_line(lines, i)
                if table_data:
                    tables.append({
                        'data': table_data,
                        'start_line': i,
                        'raw_text': '\n'.join(lines[i:i+len(table_data)])
                    })
        
        logger.info(f"Extracted {len(tables)} tables from text")
        return tables
    
    def _looks_like_table_row(self, line: str) -> bool:
        """Check if a line looks like a table row"""
        
        if not line.strip():
            return False
        
        # Check for common table delimiters
        delimiter_count = 0
        for delimiter_pattern in self.table_delimiters:
            if re.search(delimiter_pattern, line):
                delimiter_count += len(re.findall(delimiter_pattern, line))
        
        # Check for numeric values
        has_numbers = bool(re.search(r'\b\d+\.?\d*\b', line))
        
        # Must have delimiters and preferably numbers
        return delimiter_count >= 1 and (has_numbers or delimiter_count >= 2)
    
    def _extract_table_from_line(self, lines: List[str], start_idx: int) -> Optional[List[List[str]]]:
        """Extract table data starting from a specific line"""
        
        table_rows = []
        current_idx = start_idx
        
        # Determine the delimiter used
        first_line = lines[start_idx]
        delimiter = None
        for delim_pattern in self.table_delimiters:
            if re.search(delim_pattern, first_line):
                delimiter = delim_pattern
                break
        
        if not delimiter:
            return None
        
        # Extract consecutive table rows
        while current_idx < len(lines):
            line = lines[current_idx].strip()
            
            if not line:
                current_idx += 1
                continue
            
            if not re.search(delimiter, line):
                break
            
            # Split the line by delimiter
            if delimiter == MULTI_SPACE_PATTERN:
                row = re.split(MULTI_SPACE_PATTERN, line)
            else:
                row = re.split(delimiter, line)
            
            # Clean up the row
            row = [cell.strip() for cell in row if cell.strip()]
            
            if len(row) >= 2:  # Must have at least 2 columns
                table_rows.append(row)
            
            current_idx += 1
        
        return table_rows if len(table_rows) >= 2 else None
    
    def process_table_data(self, table_data: List[List[str]]) -> pd.DataFrame:
        """
        Convert extracted table data to pandas DataFrame
        
        Args:
            table_data: List of rows (each row is a list of cells)
            
        Returns:
            pandas DataFrame
        """
        
        if not table_data:
            return pd.DataFrame()
        
        try:
            # First row might be headers
            headers = table_data[0]
            data_rows = table_data[1:]
            
            # Create DataFrame
            df = pd.DataFrame(data_rows, columns=headers)
            
            # Try to convert numeric columns
            for col in df.columns:
                df[col] = self._convert_to_numeric(df[col])
            
            logger.info(f"Created DataFrame with shape {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error processing table data: {e}")
            return pd.DataFrame()
    
    def _convert_to_numeric(self, series: pd.Series) -> pd.Series:
        """Convert series to numeric where possible"""
        
        def clean_numeric(value):
            if pd.isna(value):
                return value
            
            # Remove units and extra characters
            value_str = str(value).strip()
            
            # Extract numeric part
            numeric_match = re.search(r'\d+\.?\d*', value_str)
            if numeric_match:
                try:
                    return float(numeric_match.group())
                except Exception:
                    return value
            
            return value
        
        try:
            cleaned = series.apply(clean_numeric)
            return pd.to_numeric(cleaned, errors='ignore')
        except Exception:
            return series
    
    def compute_statistics(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """
        Compute statistics based on the query
        
        Args:
            df: DataFrame containing table data
            query: Original user query
            
        Returns:
            Dictionary with computed statistics
        """
        
        if df.empty:
            return {'error': 'No valid table data found'}
        
        query_lower = query.lower()
        results = {
            'table_shape': df.shape,
            'columns': list(df.columns),
            'statistics': {}
        }
        
        # Get numeric columns
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_columns:
            return {'error': 'No numeric columns found in table'}
        
        try:
            for col in numeric_columns:
                col_stats = {}
                
                # Basic statistics
                if 'mean' in query_lower or 'average' in query_lower:
                    col_stats['mean'] = float(df[col].mean())
                
                if 'median' in query_lower:
                    col_stats['median'] = float(df[col].median())
                
                if 'min' in query_lower or 'minimum' in query_lower or 'lowest' in query_lower:
                    col_stats['min'] = float(df[col].min())
                
                if 'max' in query_lower or 'maximum' in query_lower or 'highest' in query_lower:
                    col_stats['max'] = float(df[col].max())
                
                if 'sum' in query_lower or 'total' in query_lower:
                    col_stats['sum'] = float(df[col].sum())
                
                if 'count' in query_lower:
                    col_stats['count'] = int(df[col].count())
                
                if 'std' in query_lower or 'standard deviation' in query_lower:
                    col_stats['std'] = float(df[col].std())
                
                if 'var' in query_lower or 'variance' in query_lower:
                    col_stats['var'] = float(df[col].var())
                
                # If no specific statistic requested, provide common ones
                if not col_stats:
                    col_stats = {
                        'mean': float(df[col].mean()),
                        'median': float(df[col].median()),
                        'min': float(df[col].min()),
                        'max': float(df[col].max()),
                        'count': int(df[col].count())
                    }
                
                results['statistics'][col] = col_stats
            
            logger.info(f"Computed statistics for {len(numeric_columns)} columns")
            return results
            
        except Exception as e:
            logger.error(f"Error computing statistics: {e}")
            return {'error': f'Error computing statistics: {str(e)}'}
    
    def format_numeric_response(self, stats: Dict[str, Any], query: str, source_info: str = "") -> str:
        """
        Format the numeric results into a natural language response
        
        Args:
            stats: Computed statistics
            query: Original query
            source_info: Information about source table/document
            
        Returns:
            Formatted response string
        """
        
        if 'error' in stats:
            return f"Unable to process table data: {stats['error']}"
        
        response_parts = []
        
        # Add source information
        if source_info:
            response_parts.append(f"Based on the data from {source_info}:")
        else:
            response_parts.append("Based on the table data:")
        
        # Format statistics
        for column, col_stats in stats['statistics'].items():
            col_response = f"\n**{column}:**"
            
            for stat_name, value in col_stats.items():
                if stat_name == 'mean':
                    col_response += f"\n- Average: {value:.2f}"
                elif stat_name == 'median':
                    col_response += f"\n- Median: {value:.2f}"
                elif stat_name == 'min':
                    col_response += f"\n- Minimum: {value:.2f}"
                elif stat_name == 'max':
                    col_response += f"\n- Maximum: {value:.2f}"
                elif stat_name == 'sum':
                    col_response += f"\n- Total: {value:.2f}"
                elif stat_name == 'count':
                    col_response += f"\n- Count: {value}"
                elif stat_name == 'std':
                    col_response += f"\n- Standard Deviation: {value:.2f}"
                elif stat_name == 'var':
                    col_response += f"\n- Variance: {value:.2f}"
            
            response_parts.append(col_response)
        
        # Add table info
        shape = stats['table_shape']
        response_parts.append(f"\n*Table contains {shape[0]} rows and {shape[1]} columns.*")
        
        return '\n'.join(response_parts)

def main():
    """Demo of table processing functionality"""
    
    processor = TableProcessor()
    
    # Sample medical table text
    sample_table_text = """
    Lab Results - Patient John Smith
    
    Test Name | Value | Normal Range | Units
    Glucose | 95 | 70-100 | mg/dL
    Cholesterol | 180 | <200 | mg/dL
    HDL | 45 | >40 | mg/dL
    LDL | 110 | <100 | mg/dL
    Triglycerides | 150 | <150 | mg/dL
    Hemoglobin | 14.2 | 12-16 | g/dL
    Hematocrit | 42 | 36-46 | %
    White Blood Cells | 7.5 | 4.5-11.0 | K/uL
    """
    
    print("🔬 Table-Aware Numeric Reasoning Demo")
    print("=" * 50)
    
    # Test numeric query detection
    test_queries = [
        "What is the average glucose level?",
        "Show me the cholesterol values",
        "Calculate the mean HDL",
        "What are the lab results?",
        "Tell me about the patient",  # Non-numeric
        "What is the minimum hemoglobin value?"
    ]
    
    print("\n📝 Testing Query Detection:")
    for query in test_queries:
        is_numeric = processor.is_numeric_query(query)
        print(f"'{query}' -> Numeric: {is_numeric}")
    
    # Test table extraction
    print("\n📊 Testing Table Extraction:")
    tables = processor.extract_tables_from_text(sample_table_text)
    print(f"Found {len(tables)} tables")
    
    if tables:
        # Process first table
        table_data = tables[0]['data']
        print(f"Table data: {len(table_data)} rows")
        
        # Convert to DataFrame
        df = processor.process_table_data(table_data)
        print(f"DataFrame shape: {df.shape}")
        print("Columns:", df.columns.tolist())
        
        # Test statistics computation
        query = "What is the average glucose level?"
        stats = processor.compute_statistics(df, query)
        print(f"\nStatistics: {stats}")
        
        # Format response
        response = processor.format_numeric_response(stats, query, "Lab Results Table")
        print(f"\nFormatted Response:\n{response}")

if __name__ == "__main__":
    main()