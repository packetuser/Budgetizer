# Budgetizer

A smart transaction categorization tool for personal finance management.

## Features

- 🤖 AI-powered transaction categorization using Claude API
- 🔍 Wildcard matching for household brand names
- 📊 Automatic categorization of bank and credit card transactions
- 💳 Support for multiple CSV formats
- 📈 Generate spending summaries by category, account, and month
- ⚡ Interactive mode for categorizing new transactions

## Setup

1. Install dependencies:
```bash
sudo apt install python3-dotenv python3-requests python3-pandas
```

2. Create a `.env` file with your Claude API key:
```
ANTHROPIC_API_KEY=your_api_key_here
```

3. Place your bank/credit card CSV files in the `Statements/` folder

## Usage

Run the categorizer:
```bash
python3 categorize.py
```

The script will:
- Process all CSV files in the Statements folder
- Categorize transactions based on keywords
- Ask for categorization of unknown transactions (if interactive mode is enabled)
- Generate summary reports

## Output Files

- `all_transactions.csv` - Master file with all categorized transactions
- `summary_by_category.csv` - Spending by category
- `summary_by_account.csv` - Individual account spending
- `summary_by_month.csv` - Monthly spending breakdown
- `categories.csv` - Keyword rules for categorization

## Wildcard Support

The tool supports wildcards for brand names. For example:
- `NETFLIX*` matches `NETFLIX-123`, `NETFLIX.COM`, etc.
- `AMAZON*` matches `AMAZON.CA ORDER-456`, `AMAZON PRIME`, etc.

## License

MIT