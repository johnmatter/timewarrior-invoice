# Invoice Generation System Design Document

## Overview

This system converts Timewarrior CLI output into professional LaTeX-based PDF invoices. The system processes time tracking data and generates legally compliant invoices for the United States market.

## System Architecture

### Core Components

1. **Timewarrior Data Parser**
   - Processes JSON/CSV output from `timew export` command
   - Handles time intervals, tags, and project categorization
   - Calculates billable hours and rates

2. **Invoice Data Model**
   - Represents invoice structure with all required US legal elements
   - Manages client information, line items, and totals
   - Handles tax calculations and payment terms

3. **LaTeX Template Engine**
   - Generates LaTeX source code from invoice data
   - Uses professional invoice template with proper formatting
   - Ensures legal compliance and professional appearance

4. **PDF Compilation Pipeline**
   - Compiles LaTeX to PDF using external LaTeX distribution
   - Handles compilation errors and warnings
   - Provides output file management

## Invoice Numbering Strategy

### Hex Hash-Based Invoice IDs

For audio software industry clients, the system will generate invoice numbers using the format:
```
{client-prefix}-{hex-hash}
```

Examples:
- `madrona-a23fa87c`
- `goodhertz-bd87a879`
- `uhe-7f4e2a1d`

### Implementation Details

**Class: `InvoiceNumberGenerator`**

The hash will be generated from:
- Client identifier
- Billing period start/end dates
- Total billable hours
- Project tags (sorted alphabetically)
- Timestamp of invoice generation

This approach provides:
- **Uniqueness**: Hash collision probability is extremely low
- **Traceability**: Same time period + client + data = same invoice number
- **Professional appearance**: Clean, consistent format
- **Industry appropriate**: Matches the technical nature of audio software companies

### Hash Generation Algorithm

```python
def generate_invoice_hash(self, client_id: str, start_date: str, end_date: str, 
                         total_hours: float, projects: List[str], 
                         timestamp: datetime) -> str:
    # Create deterministic string from invoice data
    data_string = f"{client_id}:{start_date}:{end_date}:{total_hours:.2f}:{','.join(sorted(projects))}:{timestamp.isoformat()}"
    
    # Generate SHA-256 hash and take first 8 characters
    hash_object = hashlib.sha256(data_string.encode())
    return hash_object.hexdigest()[:8]
```

### Client Prefix Management

**Configuration Structure:**
```yaml
clients:
  madrona:
    name: "Madrona Labs"
    prefix: "madrona"
    address: "..."
    contact: "..."
  goodhertz:
    name: "Goodhertz"
    prefix: "goodhertz"
    address: "..."
    contact: "..."
  uhe:
    name: "u-he"
    prefix: "uhe"
    address: "..."
    contact: "..."
```

### Benefits for Audio Software Industry

1. **Technical Credibility**: Hex hashes resonate with developers and technical teams
2. **Consistency**: Same work period always generates same invoice number
3. **Collision Resistance**: SHA-256 provides excellent uniqueness
4. **Audit Trail**: Hash can be verified against source data
5. **Professional Branding**: Clean, memorable format for client communications

## Data Flow

```
Timewarrior Export → Parser → Invoice Model → LaTeX Generator → PDF Output
```

## Detailed Component Design

### 1. Timewarrior Data Parser

**Class: `TimewarriorParser`**

Responsibilities:
- Parse JSON/CSV output from `timew export` command
- Extract time intervals, tags, and annotations
- Group entries by project/client
- Calculate billable hours and apply rates

Key Methods:
```python
def parse_export_data(self, json_data: str) -> List[TimeEntry]
def group_by_project(self, entries: List[TimeEntry]) -> Dict[str, List[TimeEntry]]
def calculate_billable_hours(self, entries: List[TimeEntry]) -> float
def apply_hourly_rates(self, entries: List[TimeEntry], rates: Dict[str, float]) -> List[BillableItem]
```

### 2. Invoice Data Model

**Class: `Invoice`**

Core attributes:
- Invoice number (auto-generated)
- Issue date
- Due date
- Biller information (John Matter + address)
- Client information
- Line items with descriptions, hours, rates, and amounts
- Subtotal, tax, and total amounts
- Payment terms and methods
- Notes and terms

**Class: `BillableItem`**
- Description (from Timewarrior tags/annotations)
- Hours worked
- Hourly rate
- Amount
- Project/client association

**Class: `Client`**
- Name
- Address
- Contact information
- Tax ID (if applicable)

### 3. LaTeX Template Engine

**Class: `LaTeXInvoiceGenerator`**

Responsibilities:
- Generate LaTeX source from Invoice object
- Apply professional formatting
- Include all legally required elements
- Handle special characters and formatting

Template structure:
```latex
\documentclass[11pt,letterpaper]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\usepackage{fancyhdr}
\usepackage{longtable}
\usepackage{array}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{hyperref}
```

### 4. PDF Compilation Pipeline

**Class: `PDFCompiler`**

Responsibilities:
- Execute LaTeX compilation commands
- Handle compilation errors and warnings
- Manage temporary files
- Provide compilation status feedback

## US Legal Requirements

The invoice must include:

1. **Biller Information**
   - Full name (John Matter)
   - Complete address
   - Contact information
   - Tax identification number (if applicable)

2. **Client Information**
   - Client name
   - Billing address
   - Contact information

3. **Invoice Details**
   - Unique invoice number
   - Issue date
   - Due date
   - Payment terms

4. **Line Items**
   - Detailed description of services
   - Quantity (hours)
   - Rate per unit
   - Amount for each line item

5. **Financial Summary**
   - Subtotal
   - Tax amount and rate (if applicable)
   - Total amount due
   - Payment instructions

6. **Additional Elements**
   - Terms and conditions
   - Late payment penalties
   - Payment methods accepted

## Configuration Management

**Class: `InvoiceConfig`**

Configuration file (`config.yaml`) will include:
- Default hourly rates by project/tag
- Biller information (name, address, contact)
- Tax rates and rules
- Invoice numbering scheme
- Payment terms
- LaTeX template customization

## Command Line Interface

**Script: `invoice_generator.py`**

Usage:
```bash
python invoice_generator.py --start-date 2024-01-01 --end-date 2024-01-31 --client "Client Name" --output invoice.pdf
```

Options:
- `--start-date`: Start of billing period
- `--end-date`: End of billing period
- `--client`: Client name for filtering
- `--project`: Project name for filtering
- `--output`: Output PDF filename
- `--config`: Configuration file path
- `--template`: Custom LaTeX template path

## Dependencies

### Required Python Packages
- `pyyaml`: Configuration file parsing
- `jinja2`: Template rendering (alternative to direct LaTeX generation)
- `click`: Command line interface
- `python-dateutil`: Date parsing and manipulation
- `pathlib`: File path handling

### External Dependencies
- LaTeX distribution (TeX Live, MiKTeX, or MacTeX)
- `pdflatex` command available in PATH

## File Structure

```
invoice-maker/
├── src/
│   ├── __init__.py
│   ├── parser.py          # Timewarrior data parsing
│   ├── models.py          # Invoice data models
│   ├── generator.py       # LaTeX generation
│   ├── compiler.py        # PDF compilation
│   └── config.py          # Configuration management
├── templates/
│   ├── invoice.tex        # LaTeX invoice template
│   └── styles.tex         # LaTeX style definitions
├── config/
│   └── default.yaml       # Default configuration
├── tests/
│   ├── test_parser.py
│   ├── test_models.py
│   └── test_generator.py
├── invoice_generator.py   # Main CLI script
├── requirements.txt       # Python dependencies
└── README.md
```

## Error Handling

1. **Timewarrior Export Errors**
   - Handle missing or malformed JSON/CSV data
   - Validate time interval format
   - Provide helpful error messages

2. **LaTeX Compilation Errors**
   - Capture and display compilation errors
   - Suggest common fixes
   - Provide fallback templates

3. **Configuration Errors**
   - Validate configuration file format
   - Check for required fields
   - Provide default values where appropriate

## Testing Strategy

1. **Unit Tests**
   - Parser functionality with sample Timewarrior data
   - Invoice model calculations
   - LaTeX generation with known inputs

2. **Integration Tests**
   - End-to-end workflow from Timewarrior data to PDF
   - Configuration file loading and validation
   - Error handling scenarios

3. **Sample Data**
   - Include sample Timewarrior export data
   - Provide example configuration files
   - Create test invoices for validation

## Future Enhancements

1. **Multiple Output Formats**
   - HTML invoice generation
   - Email integration
   - Cloud storage integration

2. **Advanced Features**
   - Recurring invoice templates
   - Multiple currency support
   - Tax calculation automation
   - Client database integration

3. **User Interface**
   - Web-based interface
   - Desktop application
   - Mobile app for time tracking

## Implementation Priority

1. **Phase 1**: Core parsing and basic LaTeX generation
2. **Phase 2**: Configuration system and CLI interface
3. **Phase 3**: Error handling and testing
4. **Phase 4**: Advanced features and optimizations

## Security Considerations

1. **Data Privacy**
   - Secure handling of client information
   - Temporary file cleanup
   - Configuration file permissions

2. **Input Validation**
   - Sanitize all user inputs
   - Validate file paths and names
   - Prevent command injection in LaTeX compilation

## Performance Considerations

1. **Large Datasets**
   - Efficient parsing of large Timewarrior exports
   - Memory management for long billing periods
   - Incremental processing capabilities

2. **Compilation Optimization**
   - Parallel processing for multiple invoices
   - Caching of compiled templates
   - Minimal LaTeX compilation overhead 