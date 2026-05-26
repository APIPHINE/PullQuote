#!/usr/bin/env python3
"""
Quote Extractor and Search Tool
Extracts quotes from the quotes_json.zip archive and displays them in a tabular format.
"""

import zipfile
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import argparse
from tabulate import tabulate

class QuoteExtractor:
    def __init__(self, zip_path: str = "quotes_json.zip"):
        """Initialize the quote extractor with a zip file path."""
        self.zip_path = zip_path
        self.quotes = []
        self.load_quotes()
    
    def load_quotes(self) -> None:
        """Load all quotes from the zip file."""
        if not os.path.exists(self.zip_path):
            raise FileNotFoundError(f"Zip file not found: {self.zip_path}")
        
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                # Find all JSON files in the zip
                json_files = [f for f in zip_ref.namelist() if f.endswith('.json')]
                
                for json_file in json_files:
                    try:
                        with zip_ref.open(json_file) as file:
                            data = json.load(file)
                            
                            # Handle both single quote objects and lists of quotes
                            if isinstance(data, list):
                                self.quotes.extend(data)
                            elif isinstance(data, dict):
                                self.quotes.append(data)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Could not parse {json_file}: {e}", file=sys.stderr)
                    except Exception as e:
                        print(f"Warning: Error reading {json_file}: {e}", file=sys.stderr)
        
        except zipfile.BadZipFile:
            raise ValueError(f"Invalid zip file: {self.zip_path}")
    
    def search(self, query: str, fields: Optional[List[str]] = None) -> List[Dict]:
        """
        Search quotes by query string.
        
        Args:
            query: Search term (case-insensitive)
            fields: Specific fields to search in (default: all fields)
        
        Returns:
            List of matching quotes
        """
        query = query.lower()
        results = []
        
        for quote in self.quotes:
            match = False
            
            if fields:
                # Search only in specified fields
                for field in fields:
                    if field in quote:
                        value = str(quote[field]).lower()
                        if query in value:
                            match = True
                            break
            else:
                # Search in all fields
                for value in quote.values():
                    if query in str(value).lower():
                        match = True
                        break
            
            if match:
                results.append(quote)
        
        return results
    
    def display_table(self, quotes: List[Dict], max_rows: Optional[int] = None,
                     columns: Optional[List[str]] = None) -> None:
        """
        Display quotes in a formatted table.
        
        Args:
            quotes: List of quote dictionaries to display
            max_rows: Maximum number of rows to display (None = all)
            columns: Specific columns to display (default: auto-detect)
        """
        if not quotes:
            print("No quotes found.")
            return
        
        # Auto-detect columns if not specified
        if not columns:
            all_keys = set()
            for quote in quotes[:min(10, len(quotes))]:
                all_keys.update(quote.keys())
            columns = sorted(list(all_keys))
        
        # Limit to specified rows
        display_quotes = quotes[:max_rows] if max_rows else quotes
        
        # Prepare table data
        table_data = []
        for quote in display_quotes:
            row = []
            for col in columns:
                value = quote.get(col, "")
                # Truncate long values
                if isinstance(value, str) and len(value) > 50:
                    value = value[:47] + "..."
                row.append(value)
            table_data.append(row)
        
        # Print table
        print(tabulate(table_data, headers=columns, tablefmt="grid", maxcolwidths=50))
        print(f"\nShowing {len(display_quotes)} of {len(quotes)} quotes")
    
    def get_stats(self) -> Dict:
        """Get statistics about the loaded quotes."""
        stats = {
            "total_quotes": len(self.quotes),
            "unique_fields": set(),
        }
        
        for quote in self.quotes:
            stats["unique_fields"].update(quote.keys())
        
        stats["unique_fields"] = sorted(list(stats["unique_fields"]))
        
        return stats


def main():
    parser = argparse.ArgumentParser(
        description="Search and display quotes from quotes_json.zip"
    )
    parser.add_argument(
        "-z", "--zip",
        default="quotes_json.zip",
        help="Path to the zip file (default: quotes_json.zip)"
    )
    parser.add_argument(
        "-s", "--search",
        help="Search term to find matching quotes"
    )
    parser.add_argument(
        "-f", "--fields",
        help="Comma-separated fields to search in (e.g., 'text,author')"
    )
    parser.add_argument(
        "-c", "--columns",
        help="Comma-separated columns to display (e.g., 'text,author,source')"
    )
    parser.add_argument(
        "-n", "--number",
        type=int,
        help="Number of results to display"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics about the quotes"
    )
    
    args = parser.parse_args()
    
    try:
        # Load quotes
        extractor = QuoteExtractor(args.zip)
        print(f"✓ Loaded {len(extractor.quotes)} quotes from {args.zip}\n")
        
        # Show stats if requested
        if args.stats:
            stats = extractor.get_stats()
            print("📊 Quote Statistics:")
            print(f"  Total quotes: {stats['total_quotes']}")
            print(f"  Available fields: {', '.join(stats['unique_fields'])}\n")
        
        # Search or display all
        if args.search:
            fields = args.fields.split(",") if args.fields else None
            results = extractor.search(args.search, fields)
            print(f"🔍 Found {len(results)} quotes matching '{args.search}'\n")
        else:
            results = extractor.quotes
            print(f"📋 Displaying quotes:\n")
        
        # Display results
        columns = args.columns.split(",") if args.columns else None
        extractor.display_table(results, max_rows=args.number, columns=columns)
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
