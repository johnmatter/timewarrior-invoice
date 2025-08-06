# Timewarrior Invoice Generator

A Python-based invoice generation system that converts Timewarrior CLI time tracking data into professional PDF invoices using LaTeX.

## Features

- **Timewarrior Integration**: Exports time tracking data directly from Timewarrior CLI
- **Professional PDF Output**: Generates high-quality invoices using LaTeX with custom fonts
- **Organized File Structure**: Automatically organizes invoices by client, year, and month
- **Deterministic Invoice Numbers**: Invoice numbers are based on the actual time period data
- **Custom Font Support**: Uses Maru fonts for professional typography
- **Clean Monospace Tables**: Uses monospace fonts for perfect alignment without grid lines
- **Flexible Configuration**: YAML-based configuration for clients, rates, and billing details

## Requirements

- Python 3.12+
- Timewarrior CLI
- LaTeX distribution (XeLaTeX for custom fonts)
- Custom fonts (Maru fonts)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd timewarrior-invoice
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install custom fonts:
   - Place Maru fonts in `/Users/matter/fonts/maru vf/`
   - Update font paths in `src/generator.py` if needed

5. Initialize your personal configuration:
```bash
python invoice_generator.py init-config
```

## Configuration

Your personal configuration is stored in `~/.config/timewarrior/invoice/config.yaml`. The system will automatically create this directory and file when you run `init-config`.

Edit your configuration file to set up your billing information and client details:

```yaml
biller:
  name: "Your Name"
  email: "your.email@example.com"
  phone: "(555) 123-4567"
  address:
    street: "123 Main St"
    city: "Your City"
    state: "ST"
    zip_code: "12345"
    country: "USA"

defaults:
  tax_rate: 0.08
  payment_terms: "Net 30"
  payment_instructions: "Please remit payment within 30 days of invoice date."

latex:
  command: "xelatex"

clients:
  client_id:
    name: "Client Name"
    prefix: "cn"
    address:
      street: "456 Client St"
      city: "Client City"
      state: "ST"
      zip_code: "67890"
    contact_email: "client@example.com"
    contact_phone: "(555) 987-6543"
    rates:
      default: 150.0
      code: 150.0
      design: 125.0
```

## Usage

### Generate an Invoice

```bash
python invoice_generator.py generate \
  --start-date 2025-07-01 \
  --end-date 2025-07-31 \
  --client madrona_labs \
  --verbose
```

### Options

- `--start-date`: Start date of billing period (YYYY-MM-DD)
- `--end-date`: End date of billing period (YYYY-MM-DD)
- `--client`: Client identifier from configuration
- `--output`: Custom output path (optional, uses organized path by default)
- `--config`: Configuration file path (default: ~/.config/timewarrior/invoice/config.yaml)
- `--dry-run`: Generate LaTeX without compiling to PDF
- `--verbose`: Verbose output

### Output Structure

Invoices are automatically organized in the following structure:
```
output/
├── client_id/
│   └── year/
│       └── month/
│           ├── prefix-hash.pdf
│           └── prefix-hash.tex
```

Example: `output/madrona_labs/2025/07/ml-de0b4cc0.pdf`

## Features in Detail

### Deterministic Invoice Numbers

Invoice numbers are generated using a hash of the invoice data:
- Client prefix
- Start and end dates
- Total hours
- Project list
- Time period midpoint

This ensures the same invoice data always generates the same invoice number.

### Custom Typography

- **Main Font**: GT-Maru-VF for body text
- **Monospace Font**: GT-Maru-Mono-VF for tables
- **Clean Design**: No grid lines, relies on monospace alignment

### Professional Layout

- **Header**: Invoice information in organized tables
- **Addresses**: Biller and client information
- **Line Items**: Type, Notes, Rate, Qty, Units, Amount
- **Totals**: Subtotal, tax, and final total
- **Payment Instructions**: Clear payment methods and terms

## Development

### Project Structure

```
timewarrior-invoice/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── generator.py       # LaTeX generation
│   ├── models.py          # Data models
│   ├── parser.py          # Timewarrior data parsing
│   └── compiler.py        # PDF compilation
├── config/
│   └── 2025.yaml         # Configuration file
├── output/               # Generated invoices
├── tests/               # Test suite
├── invoice_generator.py # Main CLI script
└── requirements.txt     # Python dependencies
```

### Running Tests

```bash
python -m pytest tests/
```

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here] 