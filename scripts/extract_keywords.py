#!/usr/bin/env python3
"""
Script to extract reference and identified phrases from Global_Keywords_new field in CSV file.
The script reads the JSON data and creates a formatted string with all phrases.
"""

import csv
import ast
import json
from typing import List, Dict, Any

def parse_keywords_json(json_string: str) -> List[Dict[str, Any]]:
    """
    Parse the JSON string from the CSV field.
    The data is stored as Python list format with single quotes.
    """
    try:
        # The data is stored as Python literal (with single quotes)
        # Use ast.literal_eval to safely parse it
        parsed_data = ast.literal_eval(json_string)
        return parsed_data
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing JSON: {e}")
        print(f"Problematic string: {json_string[:100]}...")
        return []

def extract_phrases(keywords_data: List[Dict[str, Any]]) -> str:
    """
    Extract only the identified phrases from the keywords data.
    Format: phrase1, phrase2, phrase3, ...
    """
    phrases = []
    
    for item in keywords_data:
        identified_phrase = item.get('identified_phrase', '')
        if identified_phrase:  # Only add non-empty phrases
            phrases.append(identified_phrase)
    
    return ", ".join(phrases)

def process_csv_file(input_file: str, output_file: str):
    """
    Process the CSV file and create a new file with extracted phrases.
    """
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        
        # Create output file with additional columns
        fieldnames = reader.fieldnames + ['extracted_phrases', 'phrase_count']
        
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row_num, row in enumerate(reader, 1):
                keywords_json = row.get('global_keywords_new', '')
                
                if keywords_json:
                    try:
                        keywords_data = parse_keywords_json(keywords_json)
                        extracted_phrases = extract_phrases(keywords_data)
                        phrase_count = len(keywords_data)
                        
                        row['extracted_phrases'] = extracted_phrases
                        row['phrase_count'] = phrase_count
                        
                        print(f"Processed row {row_num}: {phrase_count} phrases extracted")
                        
                    except Exception as e:
                        print(f"Error processing row {row_num}: {e}")
                        row['extracted_phrases'] = f"Error: {str(e)}"
                        row['phrase_count'] = 0
                else:
                    row['extracted_phrases'] = ""
                    row['phrase_count'] = 0
                
                writer.writerow(row)

def process_csv_file_inplace(input_file: str):
    """
    Process the CSV file and update the global_keywords_new column with extracted phrases.
    Also adds a phrase_count column.
    """
    rows = []
    
    # Read all rows first
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames)
        
        # Add new columns if they don't exist
        if 'extracted_phrases' not in fieldnames:
            fieldnames.append('extracted_phrases')
        if 'phrase_count' not in fieldnames:
            fieldnames.append('phrase_count')
        
        for row_num, row in enumerate(reader, 1):
            keywords_json = row.get('global_keywords_new', '')
            
            if keywords_json:
                try:
                    keywords_data = parse_keywords_json(keywords_json)
                    extracted_phrases = extract_phrases(keywords_data)
                    phrase_count = len(keywords_data)
                    
                    row['global_keywords_new'] = extracted_phrases
                    row['extracted_phrases'] = extracted_phrases
                    row['phrase_count'] = phrase_count
                    
                    print(f"Processed row {row_num}: {phrase_count} phrases extracted")
                    
                except Exception as e:
                    print(f"Error processing row {row_num}: {e}")
                    row['global_keywords_new'] = f"Error: {str(e)}"
                    row['extracted_phrases'] = f"Error: {str(e)}"
                    row['phrase_count'] = 0
            else:
                row['global_keywords_new'] = ""
                row['extracted_phrases'] = ""
                row['phrase_count'] = 0
            
            rows.append(row)
    
    # Write back to the same file
    with open(input_file, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    input_file = "/Users/pikachu/Desktop/J/Create/PgWarp/file keywords.csv"
    
    print("Choose processing option:")
    print("1. Create new file with extracted phrases (keeps original data)")
    print("2. Update original file (replaces global_keywords_new column)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        output_file = "/Users/pikachu/Desktop/J/Create/PgWarp/file keywords_processed.csv"
        print(f"Processing CSV file: {input_file}")
        print(f"Output will be saved to: {output_file}")
        process_csv_file(input_file, output_file)
        print(f"Processing completed! Check {output_file}")
        
    elif choice == "2":
        confirm = input(f"This will modify the original file '{input_file}'. Are you sure? (y/N): ").strip().lower()
        if confirm == 'y' or confirm == 'yes':
            print(f"Processing CSV file in-place: {input_file}")
            process_csv_file_inplace(input_file)
            print("Processing completed! Original file has been updated.")
        else:
            print("Operation cancelled.")
    else:
        print("Invalid choice. Please run the script again.")

if __name__ == "__main__":
    main()