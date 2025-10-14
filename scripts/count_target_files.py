#!/usr/bin/env python3
"""
Script to count files with specific target number and show additional details.
"""

import csv

def count_target_number(csv_file, target_number):
    """Count files with specific target number and provide additional details."""
    count = 0
    files_list = []
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            if row.get('target_number') == target_number:
                count += 1
                files_list.append({
                    'call_id': row.get('call_id'),
                    'target_id': row.get('target_id'), 
                    'name': row.get('name')
                })
    
    return count, files_list

def main():
    csv_file = "/Users/pikachu/Desktop/J/Create/PgWarp/file keywords.csv"
    target_number = "20251007122832"
    
    count, files_list = count_target_number(csv_file, target_number)
    
    print(f"Target Number: {target_number}")
    print(f"Total Files: {count}")
    print(f"Total Files x 2 : {count * 2}")    
    print(f"Target ID: {files_list[0]['target_id'] if files_list else 'N/A'}")
    print("\nFirst 10 files:")
    print("-" * 60)
    print(f"{'Call ID':<10} {'File Name':<40}")
    print("-" * 60)
    
    for i, file_info in enumerate(files_list[:10]):
        print(f"{file_info['call_id']:<10} {file_info['name']:<40}")
    
    if count > 10:
        print(f"... and {count - 10} more files")

if __name__ == "__main__":
    main()