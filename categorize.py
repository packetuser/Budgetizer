import os
import glob
import pandas as pd
import numpy as np
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_categories(categories_file="categories.csv"):
    """Load or create the categories mapping file."""
    if os.path.exists(categories_file):
        df = pd.read_csv(categories_file)
        # Ensure keywords are uppercase for consistency
        df['Keyword'] = df['Keyword'].str.upper()
        return df
    else:
        # Seed with starter categories
        categories = pd.DataFrame([
            {"Keyword": "PAYROLL", "Category": "Income"},
            {"Keyword": "DEPOSIT", "Category": "Income"},
            {"Keyword": "INTERAC E-TRANSFER", "Category": "Transfer"},
            {"Keyword": "WITHDRAWAL", "Category": "Cash Withdrawal"},
            {"Keyword": "BILL PAYMENT", "Category": "Housing & Utilities"},
            {"Keyword": "ENBRIDGE", "Category": "Utilities"},
            {"Keyword": "WATER", "Category": "Utilities"},
            {"Keyword": "PAYPAL", "Category": "Shopping"},
            {"Keyword": "UBER", "Category": "Transportation"},
            {"Keyword": "ACT*VILLED", "Category": "Utilities"},
            {"Keyword": "CITY OF OTTAWA PARKING", "Category": "Transportation"},
            {"Keyword": "IKEA", "Category": "Shopping"},
            {"Keyword": "PRINCESS AUTO", "Category": "Shopping"},
            {"Keyword": "CANADA COMPUTERS", "Category": "Electronics"},
            {"Keyword": "STARBUCKS", "Category": "Food & Dining"},
            {"Keyword": "EQUATOR COFFEE", "Category": "Food & Dining"},
            {"Keyword": "LCBO", "Category": "Entertainment"},
        ])
        categories.to_csv(categories_file, index=False)
        return categories

def save_categories(categories_df, categories_file="categories.csv"):
    """Save the categories mapping file, removing duplicates."""
    # Remove duplicate keywords, keeping the last occurrence (most recent rule)
    categories_df = categories_df.drop_duplicates(subset=['Keyword'], keep='last')
    categories_df.to_csv(categories_file, index=False)
    print(f"💾 Saved {len(categories_df)} category rules to {categories_file}")

def get_available_categories():
    """Get list of unique categories from existing rules."""
    categories_df = load_categories()
    unique_categories = sorted(categories_df['Category'].unique())
    # Add some common categories that might not be in use yet
    all_categories = set(unique_categories)
    all_categories.update([
        "Income", "Food & Dining", "Shopping", "Transportation", 
        "Utilities", "Entertainment", "Healthcare", "Insurance",
        "Housing & Utilities", "Cash Withdrawal", "Transfer", 
        "Education", "Personal Care", "Gifts & Donations", "Fees",
        "Electronics", "Home Improvement", "Travel", "Subscriptions"
    ])
    return sorted(list(all_categories))

def guess_category_with_ai(description):
    """Use Claude API to guess the category for a transaction."""
    try:
        # Try to use Claude API if available
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print("⚠️ ANTHROPIC_API_KEY not found in environment variables")
            return None
            
        categories = get_available_categories()
        categories_str = ", ".join(categories)
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        prompt = f"""Given this financial transaction description: '{description}'
        
        Choose the most appropriate category from this list:
        {categories_str}
        
        Respond with ONLY the category name, nothing else."""
        
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 50,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            category = result['content'][0]['text'].strip()
            # Validate that it's one of our categories
            if category in categories:
                return category
            else:
                print(f"⚠️ AI suggested unknown category: {category}")
                return None
        else:
            print(f"⚠️ Claude API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"⚠️ Error calling Claude API: {e}")
        return None

def interactive_categorize(description, categories_df):
    """Interactively categorize an uncategorized transaction."""
    print(f"\n🔍 Uncategorized transaction: '{description}'")
    print("Choose an option:")
    print("1. Select category manually")
    print("2. Let AI suggest a category")
    print("3. Skip this transaction")
    print("4. Exit and save progress")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        # Manual selection
        categories = get_available_categories()
        print("\nAvailable categories:")
        for i, cat in enumerate(categories, 1):
            print(f"{i:2}. {cat}")
        
        while True:
            try:
                cat_num = input("\nEnter category number (or 'new' to create new, 'exit' to save and quit): ").strip()
                if cat_num.lower() == 'exit':
                    return "EXIT_AND_SAVE"
                elif cat_num.lower() == 'new':
                    new_category = input("Enter new category name: ").strip()
                    if new_category:
                        return new_category
                else:
                    cat_idx = int(cat_num) - 1
                    if 0 <= cat_idx < len(categories):
                        return categories[cat_idx]
                    else:
                        print("Invalid number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number or 'new'.")
                
    elif choice == "2":
        # AI suggestion
        print("🤖 Asking Claude for suggestion...")
        suggested = guess_category_with_ai(description)
        
        if suggested:
            print(f"\n💡 AI suggests: '{suggested}'")
            confirm = input("Accept this suggestion? (Y/n): ").strip().lower()
            if confirm != 'n':
                return suggested
            else:
                # Fall back to manual selection
                print("\nFalling back to manual selection...")
                return interactive_categorize(description, categories_df)
        else:
            print("\n⚠️ AI couldn't suggest a category. Falling back to manual selection...")
            # Recursively call with manual selection
            categories = get_available_categories()
            print("\nAvailable categories:")
            for i, cat in enumerate(categories, 1):
                print(f"{i:2}. {cat}")
            
            while True:
                try:
                    cat_num = input("\nEnter category number: ").strip()
                    cat_idx = int(cat_num) - 1
                    if 0 <= cat_idx < len(categories):
                        return categories[cat_idx]
                    else:
                        print("Invalid number. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
    
    elif choice == "4":
        # Exit and save
        return "EXIT_AND_SAVE"
    
    # Choice 3 or invalid - skip
    return None

def extract_keyword_from_description(description):
    """Extract a meaningful keyword from a transaction description."""
    # Remove common transaction prefixes and clean up
    desc_upper = str(description).upper()
    
    # Remove common prefixes
    prefixes_to_remove = [
        'POS PURCHASE - ', 'INTERAC PURCHASE - ', 'VISA DEBIT PURCHASE - ',
        'E-TRANSFER ', 'BILL PAYMENT - ', 'PREAUTHORIZED DEBIT - '
    ]
    for prefix in prefixes_to_remove:
        if desc_upper.startswith(prefix):
            desc_upper = desc_upper[len(prefix):]
    
    # Take the first meaningful part (before numbers/dates)
    import re
    # Remove date patterns and long numbers
    desc_clean = re.sub(r'\d{6,}|\d{2}/\d{2}', '', desc_upper)
    
    # Split and take first meaningful word/phrase
    parts = desc_clean.split()
    if parts:
        # Check if this looks like a well-known brand that should use wildcard
        first_word = parts[0]
        common_brands = ['NETFLIX', 'SPOTIFY', 'AMAZON', 'UBER', 'AIRBNB', 'APPLE', 
                        'STARBUCKS', 'TIM', 'COSTCO', 'WALMART', 'GOOGLE', 'MICROSOFT',
                        'PAYPAL', 'EBAY', 'FACEBOOK', 'ADOBE', 'DROPBOX']
        
        # If it's a common brand, use wildcard
        for brand in common_brands:
            if first_word.startswith(brand):
                return brand + '*'
        
        # Try to get first 2-3 words as keyword (more specific)
        keyword_parts = []
        for part in parts[:3]:
            if len(part) > 2 and not part.isdigit():
                keyword_parts.append(part)
        
        if keyword_parts:
            # If it looks like a specific store/restaurant, use full name
            keyword = ' '.join(keyword_parts[:2])  # Use first 2 meaningful words
            
            # But if it ends with numbers or looks like it has location/store info, add wildcard
            if len(parts) > 2 and any(char.isdigit() for char in parts[-1]):
                # Check if the base name might benefit from wildcard
                if not any(c in keyword for c in ['*', '#', '@']):
                    keyword = keyword_parts[0] + '*'
            
            return keyword
    
    # Fallback to first 20 chars of original
    return desc_upper[:20].strip()

def categorize_transaction(description, categories_df, debug=False):
    """Match transaction description to category based on keywords with wildcard support."""
    if pd.isna(description):
        return "Uncategorized"
    desc_upper = str(description).upper().strip()  # Strip whitespace
    for _, row in categories_df.iterrows():
        keyword = row["Keyword"].strip()  # Strip whitespace from keyword too
        if keyword.endswith("*"):
            # Wildcard matching - keyword without * must be at the start of a word
            base_keyword = keyword[:-1]
            # Check if the base keyword appears as a word start in the description
            import re
            # Match if keyword is at start or after a space/special char
            pattern = r'(^|[\s\-_/])'+ re.escape(base_keyword)
            if re.search(pattern, desc_upper):
                if debug:
                    print(f"    DEBUG: Wildcard match '{keyword}' in '{desc_upper}'")
                return row["Category"]
        else:
            # Exact substring matching (original behavior)
            if keyword.upper() in desc_upper:  # Case insensitive comparison
                if debug:
                    print(f"    DEBUG: Exact match '{keyword}' in '{desc_upper}'")
                return row["Category"]
    return "Uncategorized"

def inspect_csv_structure(file_path):
    """Inspect CSV file structure to understand its format."""
    try:
        # Read first few rows to understand structure
        df = pd.read_csv(file_path, nrows=5)
        print(f"\n📋 File: {os.path.basename(file_path)}")
        print(f"Columns: {list(df.columns)}")
        print("First few rows:")
        print(df.head())
        return df.columns.tolist()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return None

def safe_to_numeric(series, default_value=0):
    """Safely convert series to numeric, replacing errors with default value."""
    return pd.to_numeric(series, errors='coerce').fillna(default_value)

def normalize_bank_csv(path):
    """Normalize bank CSV to a common schema with flexible column mapping."""
    # First, try to read with headers
    try:
        df = pd.read_csv(path)
        columns = [col.strip() for col in df.columns]
        
        # Check if this looks like it has real headers or if first row is actually data
        first_row = df.iloc[0] if not df.empty else None
        
        # If first column looks like a date and we have numeric-looking columns, 
        # this might be headerless data that pandas incorrectly treated as having headers
        if (first_row is not None and 
            any(str(first_row.iloc[0]).replace('/', '').replace('-', '').isdigit() for _ in [1]) and
            len(columns) <= 4):
            # This is likely headerless data - reread without headers
            print("🏦 Detected headerless bank format - rereading...")
            df = pd.read_csv(path, header=None)
            
            # Assign column names based on number of columns
            if len(df.columns) == 3:
                df.columns = ['Date', 'Amount', 'Description']
            elif len(df.columns) == 4:
                df.columns = ['Date', 'Amount', 'Extra', 'Description']
                # Combine Extra and Description if needed
                df['Description'] = df['Extra'].astype(str) + ' ' + df['Description'].astype(str)
                df = df.drop(columns=['Extra'])
            else:
                # Generic naming for other formats
                df.columns = [f'Col_{i}' for i in range(len(df.columns))]
                print(f"⚠️ Unusual bank format with {len(df.columns)} columns")
                
            column_mapping = {
                'Date': 'Date',
                'Amount': 'Amount', 
                'Description': 'Description'
            }
        else:
            # This appears to be a proper CSV with headers
            column_mapping = {}
            
            # Map date columns
            date_variants = ['Transaction Date', 'Date', 'Posted Date', 'Posting Date', 'date']
            for variant in date_variants:
                if variant in columns:
                    column_mapping['Date'] = variant
                    break
            
            # Map description columns
            desc_variants = ['Description', 'Description 1', 'Merchant Name', 'Transaction Details', 'description']
            for variant in desc_variants:
                if variant in columns:
                    column_mapping['Description'] = variant
                    break
            
            # Map amount columns
            amount_variants = ['Amount', 'CAD$', 'amount']
            debit_variants = ['Debit', 'Withdrawal', 'debit']
            credit_variants = ['Credit', 'Deposit', 'credit']
            
            has_amount = any(variant in columns for variant in amount_variants)
            has_debit = any(variant in columns for variant in debit_variants)
            has_credit = any(variant in columns for variant in credit_variants)
            
            if has_amount:
                # Single amount column
                for variant in amount_variants:
                    if variant in columns:
                        column_mapping['Amount'] = variant
                        break
            elif has_debit and has_credit:
                # Separate debit/credit columns
                for variant in debit_variants:
                    if variant in columns:
                        column_mapping['Debit'] = variant
                        break
                for variant in credit_variants:
                    if variant in columns:
                        column_mapping['Credit'] = variant
                        break
    
    except Exception as e:
        # If reading with headers fails, try reading without headers
        print(f"🔄 Header read failed, trying headerless format: {e}")
        try:
            df = pd.read_csv(path, header=None)
            print("🏦 Reading as headerless bank format")
            
            if len(df.columns) == 3:
                df.columns = ['Date', 'Amount', 'Description']
            elif len(df.columns) == 4:
                df.columns = ['Date', 'Amount', 'Extra', 'Description']
                df['Description'] = df['Extra'].astype(str) + ' ' + df['Description'].astype(str)
                df = df.drop(columns=['Extra'])
            else:
                df.columns = [f'Col_{i}' for i in range(len(df.columns))]
                
            column_mapping = {
                'Date': 'Date',
                'Amount': 'Amount', 
                'Description': 'Description'
            }
        except Exception as e2:
            print(f"❌ Failed to read file: {e2}")
            return pd.DataFrame(columns=["Date", "Description", "Amount", "Source", "Account"])
    
    print(f"🔍 Bank CSV column mapping: {column_mapping}")
    
    # Apply the mapping
    renamed_df = df.copy()
    for new_name, old_name in column_mapping.items():
        if old_name in renamed_df.columns:
            renamed_df = renamed_df.rename(columns={old_name: new_name})
    
    # Calculate amount from debit/credit columns or use existing amount
    if 'Debit' in column_mapping and 'Credit' in column_mapping:
        debit_col = safe_to_numeric(renamed_df.get('Debit', 0))
        credit_col = safe_to_numeric(renamed_df.get('Credit', 0))
        # For bank statements: Credit is positive income, Debit is negative expense
        renamed_df['Amount'] = credit_col - debit_col
    elif 'Amount' in renamed_df.columns:
        renamed_df['Amount'] = safe_to_numeric(renamed_df['Amount'])
    else:
        print("⚠️ No amount column found - setting to 0")
        renamed_df['Amount'] = 0
    
    renamed_df["Source"] = "Bank"
    renamed_df["Account"] = "Chequing"
    
    # Return only the columns we need
    result_columns = ["Date", "Description", "Amount", "Source", "Account"]
    for col in result_columns:
        if col not in renamed_df.columns:
            if col == "Date":
                renamed_df[col] = ""
            elif col == "Description":
                renamed_df[col] = "Unknown Transaction"
            else:
                renamed_df[col] = renamed_df.get(col, "")
    
    return renamed_df[result_columns]

def normalize_credit_csv(path):
    """Normalize credit card CSV to a common schema with flexible column mapping."""
    df = pd.read_csv(path)
    
    column_mapping = {}
    columns = [col.strip() for col in df.columns]
    
    # Map date columns
    date_variants = ['Transaction Date', 'Date', 'Posting Date', 'date']
    for variant in date_variants:
        if variant in columns:
            column_mapping['Date'] = variant
            break
    
    # Map description columns
    desc_variants = ['Description', 'Merchant Name', 'Transaction Details', 'description']
    for variant in desc_variants:
        if variant in columns:
            column_mapping['Description'] = variant
            break
    
    # Map amount columns
    amount_variants = ['CAD$', 'Amount', 'amount']
    for variant in amount_variants:
        if variant in columns:
            column_mapping['Amount'] = variant
            break
    
    # Map card number columns
    card_variants = ['Card No.', 'Card Number', 'Card', 'card']
    for variant in card_variants:
        if variant in columns:
            column_mapping['Card'] = variant
            break
    
    print(f"🔍 Credit CSV column mapping: {column_mapping}")
    
    # Apply the mapping
    renamed_df = df.copy()
    for new_name, old_name in column_mapping.items():
        if old_name in renamed_df.columns:
            renamed_df = renamed_df.rename(columns={old_name: new_name})
    
    # Handle amount - credit card amounts are typically negative for purchases
    if 'Amount' in renamed_df.columns:
        renamed_df['Amount'] = safe_to_numeric(renamed_df['Amount'])
        # Make purchases negative (assuming positive amounts in CSV are purchases)
        renamed_df['Amount'] = -abs(renamed_df['Amount'])
    elif 'Debit' in renamed_df.columns and 'Credit' in renamed_df.columns:
        # Some credit statements use Debit/Credit format
        debit_col = safe_to_numeric(renamed_df.get('Debit', 0))
        credit_col = safe_to_numeric(renamed_df.get('Credit', 0))
        # For credit cards: Debit = purchases (negative), Credit = payments (positive)
        renamed_df['Amount'] = credit_col - debit_col
    else:
        print("⚠️ No amount column found - setting to 0")
        renamed_df['Amount'] = 0
    
    renamed_df["Source"] = "CreditCard"
    
    # Map card numbers to cardholders - get all unique card numbers first
    if 'Card' in renamed_df.columns:
        unique_cards = renamed_df['Card'].astype(str).str[-4:].unique()
        print(f"🃏 Found cards ending in: {list(unique_cards)}")
        
        # Map known cards and handle unknown ones
        card_mapping = {
            "1522": "Paul",
            "7256": "Sarah"
        }
        
        renamed_df["Account"] = renamed_df["Card"].astype(str).str[-4:].map(card_mapping)
        
        # Handle unmapped cards
        unmapped_cards = [card for card in unique_cards if card not in card_mapping]
        if unmapped_cards:
            print(f"❓ Unknown card numbers: {unmapped_cards}")
            print("💡 Update the card_mapping in normalize_credit_csv() function if needed")
            
        renamed_df["Account"] = renamed_df["Account"].fillna("UnknownCard")
    else:
        renamed_df["Account"] = "CreditCard"
    
    # Return only the columns we need
    result_columns = ["Date", "Description", "Amount", "Source", "Account"]
    for col in result_columns:
        if col not in renamed_df.columns:
            if col == "Date":
                renamed_df[col] = ""
            elif col == "Description":
                renamed_df[col] = "Unknown Transaction"
            else:
                renamed_df[col] = renamed_df.get(col, "")
    
    return renamed_df[result_columns]

def process_files(folder, categories_df, interactive=True):
    """Process all CSVs in a folder with improved error handling and interactive categorization."""
    all_data = []
    csv_files = glob.glob(os.path.join(folder, "*.csv"))
    
    if not csv_files:
        print(f"❌ No CSV files found in folder: {folder}")
        return pd.DataFrame(columns=["Date","Description","Amount","Source","Account","Category"]), categories_df
    
    print(f"📁 Found {len(csv_files)} CSV files")
    
    # First, inspect all files to understand their structure
    print("\n🔍 Inspecting file structures...")
    for file in csv_files:
        inspect_csv_structure(file)
    
    print("\n📊 Processing files...")
    for file in csv_files:
        try:
            filename = os.path.basename(file).lower()
            print(f"\nProcessing: {filename}")
            
            # Determine file type based on filename and content
            df_peek = pd.read_csv(file, nrows=1)  # Read just first row to check columns
            columns = [col.strip() for col in df_peek.columns]
            
            # Check if it's a credit card file based on filename or columns
            is_credit = ("transaction_download" in filename or 
                        "credit" in filename or
                        any(col in columns for col in ['Card No.', 'Card Number', 'Card']))
            
            if is_credit:
                df = normalize_credit_csv(file)
                print(f"✅ Processed as credit card file: {len(df)} transactions")
            else:
                df = normalize_bank_csv(file)
                print(f"✅ Processed as bank file: {len(df)} transactions")
            
            if not df.empty:
                all_data.append(df)
            
        except Exception as e:
            print(f"⚠️ Error processing {file}: {e}")
            print("Continuing with other files...")
    
    if not all_data:
        return pd.DataFrame(columns=["Date","Description","Amount","Source","Account","Category"]), categories_df
    
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"\n📈 Combined {len(combined_df)} total transactions from {len(all_data)} files")
    
    # Interactive categorization for uncategorized items
    if interactive:
        print("\n🏷️ Checking for uncategorized transactions...")
        uncategorized_descriptions = set()
        categorized_descriptions = {}  # Track what we've already categorized
        new_rules_added = False
        early_exit = False
        
        for idx, row in combined_df.iterrows():
            desc = row['Description']
            if pd.notna(desc):
                # Check if we already categorized this exact description in this session
                if desc in categorized_descriptions:
                    continue
                    
                category = categorize_transaction(desc, categories_df)
                if category == "Uncategorized" and desc not in uncategorized_descriptions:
                    uncategorized_descriptions.add(desc)
                    
                    # Show what keyword would be extracted for debugging
                    potential_keyword = extract_keyword_from_description(desc)
                    print(f"  📝 Potential keyword: '{potential_keyword}'")
                    
                    # Offer to categorize this transaction
                    new_category = interactive_categorize(desc, categories_df)
                    
                    if new_category == "EXIT_AND_SAVE":
                        print("\n🛑 Exiting categorization and saving progress...")
                        early_exit = True
                        break
                    elif new_category:
                        # Extract a keyword from the description
                        keyword = extract_keyword_from_description(desc)
                        
                        # Add new rule to categories (save keyword in uppercase for consistency)
                        new_rule = pd.DataFrame([{
                            "Keyword": keyword.upper(),
                            "Category": new_category
                        }])
                        categories_df = pd.concat([categories_df, new_rule], ignore_index=True)
                        print(f"✅ Added rule: '{keyword}' → '{new_category}'")
                        
                        # Debug: Show if this rule would match the current description
                        test_match = categorize_transaction(desc, categories_df)
                        if test_match == new_category:
                            print(f"  ✓ Rule successfully matches this transaction")
                        else:
                            print(f"  ⚠️ Warning: Rule doesn't match! Got '{test_match}' instead of '{new_category}'")
                        
                        new_rules_added = True
                        
                        # Mark this description as categorized for this session
                        categorized_descriptions[desc] = new_category
        
        if new_rules_added or early_exit:
            # Save updated categories (always save on exit, even without new rules)
            save_categories(categories_df)
            
        if early_exit:
            print("💾 Progress has been saved. You can continue categorization later.")
    
    return combined_df, categories_df

def main():
    print("💳 Transaction Categorizer")
    print("=" * 40)
    
    # Default folder = ./Statements
    default_folder = os.path.join(os.getcwd(), "Statements")
    folder = input(f"Enter the folder containing your transaction CSVs [{default_folder}]: ").strip()
    if not folder:
        folder = default_folder
    
    if not os.path.exists(folder):
        print(f"❌ Folder doesn't exist: {folder}")
        return

    categories_df = load_categories()
    print(f"📂 Loaded {len(categories_df)} category rules")
    
    # Ask if user wants interactive categorization
    interactive = input("\nEnable interactive categorization for new transactions? (Y/n): ").strip().lower()
    interactive = interactive != 'n'
    
    new_data, updated_categories_df = process_files(folder, categories_df, interactive=interactive)

    if new_data.empty:
        print("❌ No transactions were successfully processed.")
        return

    # Apply categories with updated rules
    print("\n🏷️ Applying categories...")
    new_data["Category"] = new_data["Description"].apply(lambda d: categorize_transaction(d, updated_categories_df))
    
    # Handle date parsing
    new_data["Date"] = pd.to_datetime(new_data["Date"], errors="coerce")
    new_data["Year"] = new_data["Date"].dt.year
    new_data["Month"] = new_data["Date"].dt.month

    # Show sample of categorized data
    print("\n📋 Sample categorized transactions:")
    sample_data = new_data.head(10)[["Date", "Description", "Amount", "Category", "Account"]]
    print(sample_data.to_string(index=False))

    # Load existing master file
    master_file = "all_transactions.csv"
    if os.path.exists(master_file):
        print(f"\n📄 Loading existing master file...")
        master_df = pd.read_csv(master_file)
        master_df["Date"] = pd.to_datetime(master_df["Date"], errors="coerce")
        print(f"Found {len(master_df)} existing transactions")
    else:
        print(f"\n📄 Creating new master file...")
        master_df = pd.DataFrame(columns=new_data.columns)

    # Combine & dedupe
    print("🔄 Combining and deduplicating...")
    combined = pd.concat([master_df, new_data], ignore_index=True).drop_duplicates(
        subset=["Date","Description","Amount","Source","Account"], keep='last'
    )
    
    # Sort by date
    combined = combined.sort_values('Date').reset_index(drop=True)
    
    combined.to_csv(master_file, index=False)
    print(f"✅ Saved master file with {len(combined)} total transactions")
    print(f"   - Added {len(combined) - len(master_df)} new transactions")

    # Generate summaries
    print("\n📊 Generating summaries...")
    
    # Category summary (shared budget)
    summary_cat = combined.groupby("Category")["Amount"].sum().reset_index()
    summary_cat = summary_cat.sort_values("Amount", ascending=False)
    summary_cat.to_csv("summary_by_category.csv", index=False)
    
    print("\n💰 Top spending categories (shared budget):")
    print(summary_cat.head(10).to_string(index=False))

    # Account summary (individual spending)
    summary_account = combined.groupby(["Account", "Category"])["Amount"].sum().reset_index()
    summary_account = summary_account.sort_values(["Account", "Amount"])
    summary_account.to_csv("summary_by_account.csv", index=False)
    
    print(f"\n👥 Individual account spending:")
    for account in combined['Account'].unique():
        if account in ['Paul', 'Sarah']:
            account_total = combined[combined['Account'] == account]['Amount'].sum()
            print(f"   {account}: ${account_total:,.2f}")

    # Monthly summary
    valid_dates = combined.dropna(subset=['Date'])
    if not valid_dates.empty:
        summary_month = valid_dates.groupby(["Year","Month","Category"])["Amount"].sum().reset_index()
        summary_month.to_csv("summary_by_month.csv", index=False)
        print(f"\n📅 Monthly summary saved with {len(summary_month)} entries")
    
    # Show uncategorized transactions
    uncategorized = combined[combined["Category"] == "Uncategorized"]
    if not uncategorized.empty:
        print(f"\n❓ Found {len(uncategorized)} uncategorized transactions:")
        print("Consider adding rules for these descriptions:")
        unique_descriptions = uncategorized["Description"].value_counts().head(10)
        for desc, count in unique_descriptions.items():
            print(f"  - {desc} ({count} times)")

    print(f"\n🎉 Processing complete!")
    print(f"📁 Files created:")
    print(f"   - all_transactions.csv ({len(combined)} transactions)")
    print(f"   - summary_by_category.csv (shared budget)")
    print(f"   - summary_by_account.csv (individual spending)")
    print(f"   - summary_by_month.csv")
    print(f"   - categories.csv (keyword rules)")

def debug_mode():
    """Run in debug mode to inspect file structures without processing."""
    default_folder = os.path.join(os.getcwd(), "Statements")
    folder = input(f"Enter folder to inspect [{default_folder}]: ").strip()
    if not folder:
        folder = default_folder
    
    csv_files = glob.glob(os.path.join(folder, "*.csv"))
    if not csv_files:
        print(f"❌ No CSV files found in: {folder}")
        return
    
    print(f"🔍 Debug Mode - Inspecting {len(csv_files)} CSV files:")
    for file in csv_files:
        inspect_csv_structure(file)

if __name__ == "__main__":
    print("Select mode:")
    print("1. Normal processing")
    print("2. Debug mode (inspect file structures)")
    
    choice = input("Enter choice [1]: ").strip()
    
    if choice == "2":
        debug_mode()
    else:
        main()

