#!/usr/bin/env python3
"""Debug script to test categorization issues"""

import pandas as pd
from categorize import categorize_transaction, load_categories, extract_keyword_from_description

# Load categories
categories_df = load_categories()
print("=" * 60)
print("LOADED CATEGORIES:")
print("=" * 60)
print(categories_df.tail(20))  # Show last 20 rules
print(f"\nTotal rules: {len(categories_df)}")

# Test transaction descriptions
test_descriptions = [
    "MANDY LAURIER OTTAWA",
    "MANDY LAURIER",
    "REST EXPRESS OTTAWA",
    "TIM HORTONS #1234",
    "NETFLIX.COM-5678",
    "SPOTIFY P2AE7E4B5A",
]

print("\n" + "=" * 60)
print("TESTING CATEGORIZATION:")
print("=" * 60)

for desc in test_descriptions:
    category = categorize_transaction(desc, categories_df)
    keyword = extract_keyword_from_description(desc)
    print(f"\nDescription: '{desc}'")
    print(f"  Extracted keyword: '{keyword}'")
    print(f"  Category: '{category}'")
    
    # Check if any keyword in categories would match
    desc_upper = desc.upper()
    matching_rules = []
    for _, row in categories_df.iterrows():
        keyword_check = row["Keyword"]
        if keyword_check.endswith("*"):
            base_keyword = keyword_check[:-1]
            import re
            pattern = r'(^|[\s\-_/])'+ re.escape(base_keyword)
            if re.search(pattern, desc_upper):
                matching_rules.append(f"    - '{keyword_check}' -> '{row['Category']}' (wildcard match)")
        else:
            if keyword_check in desc_upper:
                matching_rules.append(f"    - '{keyword_check}' -> '{row['Category']}' (exact match)")
    
    if matching_rules:
        print("  Matching rules found:")
        for rule in matching_rules:
            print(rule)
    else:
        print("  No matching rules found")

print("\n" + "=" * 60)
print("CHECKING FOR DUPLICATES:")
print("=" * 60)
duplicates = categories_df[categories_df.duplicated(subset=['Keyword'], keep=False)]
if not duplicates.empty:
    print("Found duplicate keywords:")
    print(duplicates)
else:
    print("No duplicate keywords found")