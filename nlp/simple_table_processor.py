"""
Simple Table-Aware Numeric Reasoning Module
Detects and processes numeric queries on medical tables without pandas dependency
"""

import re
import logging
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleTableProcessor:
    """
    Handles detection and processing of table-based numeric queries without pandas
    """
    
    def __init__(self):
        self.setup_numeric_patterns()
    
    def setup_numeric_patterns(self):
        """Setup patterns for detecting numeric queries"""
        
        # Numeric keywords that indicate table-based queries
        self.numeric_keywords = [
            'mean', 'average', 'avg',
            'median', 'middle',
            'sum', 'total',
            'count', 'number of',
            'min', 'minimum', 'lowest',
            'max', 'maximum', 'highest',
            'range', 'spread',
            'lab value', 'lab values', 'laboratory',
            'blood test', 'blood work',
            'vital signs', 'vitals',
            'measurement', 'measurements',
            'reading', 'readings',
            'result', 'results',
            'level', 'levels',
            'glucose', 'cholesterol',
            'hemoglobin', 'hematocrit',
            'blood pressure'
        ]
        
        # Table indicators
        self.table_indicators = [
            'table', 'chart', 'data',
            'lab report', 'lab panel',
            'blood panel', 'chemistry panel'
        ]
    
    def is_numeric_query(self, query: str) -> bool:
        """
        Detect if a query requires numeric/table processing
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
            'what are the values',
            'show me the numbers',
            'how many'
        ]
        
        has_numeric_question = any(phrase in query_lower for phrase in numeric_questions)
        
        logger.info(f"Numeric query analysis: keywords={has_numeric_keyword}, "
                   f"table_indicators={has_table_indicator}, questions={has_numeric_question}")
        
        return has_numeric_keyword or has_table_indicator or has_numeric_question
    
    def extract_tables_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract table-like structures from text
        """
        tables = []
        lines = text.split('\n')
        
        # Look for lines that look like table headers or data rows
        for i, line in enumerate(lines):
            if self._looks_like_table_header(line):
                # Extract table from this point
                table_data = self._extract_table_from_line(lines, i)
                if table_data and len(table_data) > 1:
                    tables.append({
                        'data': table_data,
                        'start_line': i,
                        'raw_text': '\n'.join(lines[i:i+len(table_data)])
                    })
                    break  # Take first table found
        
        logger.info(f"Extracted {len(tables)} tables from text")
        return tables
    
    def _looks_like_table_header(self, line: str) -> bool:
        """Check if a line looks like a table header"""
        if not line.strip():
            return False
        
        # Look for common table patterns
        table_patterns = [
            r'Test\s*\|\s*Value',
            r'Parameter\s*\|\s*Result',
            r'Name\s*\|\s*Value\s*\|\s*Range',
            r'\|\s*Value\s*\|\s*Normal',
            r'Date\s*\|\s*Blood Pressure'
        ]
        
        for pattern in table_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        # Check for pipe-separated headers with medical terms
        if '|' in line and any(term in line.lower() for term in ['test', 'value', 'normal', 'range', 'units']):
            return True
        
        return False
    
    def _extract_table_from_line(self, lines: List[str], start_idx: int) -> Optional[List[List[str]]]:
        """Extract table data starting from a specific line"""
        table_rows = []
        current_idx = start_idx
        
        # Extract consecutive table rows
        while current_idx < len(lines) and current_idx < start_idx + 20:  # Limit to 20 rows
            line = lines[current_idx].strip()
            
            if not line:
                current_idx += 1
                continue
            
            # Stop if line doesn't look like table data
            if '|' not in line:
                break
            
            # Split by pipe and clean
            row = [cell.strip() for cell in line.split('|') if cell.strip()]
            
            if len(row) >= 2:  # Must have at least 2 columns
                table_rows.append(row)
            
            current_idx += 1
        
        return table_rows if len(table_rows) >= 2 else None
    
    def extract_numeric_values(self, table_data: List[List[str]], query: str) -> Dict[str, Any]:
        """
        Extract numeric values from table data based on query
        """
        if not table_data:
            return {'error': 'No table data provided'}
        
        # First row is usually headers
        headers = table_data[0] if table_data else []
        data_rows = table_data[1:] if len(table_data) > 1 else []
        
        query_lower = query.lower()
        
        # Find the value column
        value_col_idx = -1
        for i, header in enumerate(headers):
            if 'value' in header.lower() or 'result' in header.lower():
                value_col_idx = i
                break
        
        if value_col_idx == -1:
            # Try second column as default
            value_col_idx = 1 if len(headers) > 1 else 0
        
        # Extract numeric values
        numeric_values = []
        relevant_rows = []
        
        for row in data_rows:
            if len(row) > value_col_idx:
                value_str = row[value_col_idx]
                # Extract number from value string
                number = self._extract_number(value_str)
                if number is not None:
                    numeric_values.append(number)
                    relevant_rows.append(row)
        
        if not numeric_values:
            return {'error': 'No numeric values found in table'}
        
        # Compute basic statistics
        stats = self._compute_basic_stats(numeric_values, query_lower)
        
        return {
            'values': numeric_values,
            'count': len(numeric_values),
            'statistics': stats,
            'relevant_rows': relevant_rows[:5],  # Show first 5 rows
            'headers': headers
        }
    
    def _extract_number(self, value_str: str) -> Optional[float]:
        """Extract numeric value from string"""
        if not value_str:
            return None
        
        # Remove common units and characters
        clean_str = re.sub(r'[^\d\.\-\+]', '', value_str)
        
        # Extract first number found
        number_match = re.search(r'-?\d+\.?\d*', clean_str)
        if number_match:
            try:
                return float(number_match.group())
            except ValueError:
                pass
        
        return None
    
    def _compute_basic_stats(self, values: List[float], query: str) -> Dict[str, float]:
        """Compute basic statistics"""
        if not values:
            return {}
        
        stats = {}
        
        # Always compute basic stats
        stats['count'] = len(values)
        stats['min'] = min(values)
        stats['max'] = max(values)
        stats['sum'] = sum(values)
        stats['mean'] = sum(values) / len(values)
        
        # Median
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 0:
            stats['median'] = (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            stats['median'] = sorted_values[n//2]
        
        # Check what user specifically asked for
        if 'average' in query or 'mean' in query:
            stats['requested'] = 'mean'
        elif 'median' in query:
            stats['requested'] = 'median'
        elif 'minimum' in query or 'min' in query or 'lowest' in query:
            stats['requested'] = 'min'
        elif 'maximum' in query or 'max' in query or 'highest' in query:
            stats['requested'] = 'max'
        elif 'total' in query or 'sum' in query:
            stats['requested'] = 'sum'
        else:
            stats['requested'] = 'mean'  # Default
        
        return stats
    
    def format_numeric_response(self, result: Dict[str, Any], query: str, source_info: str = "") -> str:
        """
        Format the numeric results into a natural language response
        """
        if 'error' in result:
            return f"Unable to process table data: {result['error']}"
        
        stats = result.get('statistics', {})
        if not stats:
            return "No statistics could be computed from the table data."
        
        # Get the requested statistic
        requested = stats.get('requested', 'mean')
        requested_value = stats.get(requested, stats.get('mean'))
        
        response_parts = []
        
        # Add source information
        if source_info:
            response_parts.append(f"Based on data from {source_info}:")
        else:
            response_parts.append("Based on the table data:")
        
        # Main result
        if requested == 'mean':
            response_parts.append(f"\n**Average value: {requested_value:.2f}**")
        elif requested == 'median':
            response_parts.append(f"\n**Median value: {requested_value:.2f}**")
        elif requested == 'min':
            response_parts.append(f"\n**Minimum value: {requested_value:.2f}**")
        elif requested == 'max':
            response_parts.append(f"\n**Maximum value: {requested_value:.2f}**")
        elif requested == 'sum':
            response_parts.append(f"\n**Total sum: {requested_value:.2f}**")
        
        # Additional context
        response_parts.append(f"\n**Statistical Summary:**")
        response_parts.append(f"- Count: {stats['count']} values")
        response_parts.append(f"- Range: {stats['min']:.2f} to {stats['max']:.2f}")
        response_parts.append(f"- Average: {stats['mean']:.2f}")
        response_parts.append(f"- Median: {stats['median']:.2f}")
        
        # Show sample values
        if 'relevant_rows' in result and result['relevant_rows']:
            response_parts.append(f"\n**Sample data:**")
            headers = result.get('headers', [])
            for i, row in enumerate(result['relevant_rows'][:3]):
                if headers and len(row) >= 2:
                    response_parts.append(f"- {row[0]}: {row[1]}")
        
        return '\n'.join(response_parts)

def main():
    """Demo of simple table processing"""
    processor = SimpleTableProcessor()
    
    # Test with sample text
    sample_text = """
    Lab Results
    
    Test Name | Value | Normal Range | Units
    Glucose | 110 | 70-100 | mg/dL
    Cholesterol | 195 | <200 | mg/dL
    HDL | 52 | >50 | mg/dL
    """
    
    print("🔬 Simple Table Processor Demo")
    print("=" * 40)
    
    query = "What is the average glucose level?"
    print(f"Query: {query}")
    print(f"Is numeric: {processor.is_numeric_query(query)}")
    
    tables = processor.extract_tables_from_text(sample_text)
    print(f"Found {len(tables)} tables")
    
    if tables:
        result = processor.extract_numeric_values(tables[0]['data'], query)
        response = processor.format_numeric_response(result, query, "sample lab table")
        print(f"\nResponse:\n{response}")

if __name__ == "__main__":
    main()