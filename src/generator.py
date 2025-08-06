"""
LaTeX template engine module.

Generates LaTeX source code from invoice data and applies
professional formatting for PDF invoices.
"""

from typing import Optional

from .models import Invoice, Address


class LaTeXInvoiceGenerator:
  """Generates LaTeX source code from Invoice objects."""

  def __init__(self, template_path: Optional[str] = None):
    """
    Initialize the LaTeX generator.

    Args:
      template_path: Path to custom LaTeX template file (no longer used)
    """
    self.template_path = template_path
    # No longer using templates - LaTeX is generated directly

  def generate_latex(self, invoice: Invoice) -> str:
    """
    Generate LaTeX source code from an Invoice object using the invoice package.

    Args:
      invoice: Invoice object to convert to LaTeX

    Returns:
      Complete LaTeX source code as string
    """
    # Generate LaTeX using the invoice package
    latex_parts = []

    # Header
    latex_parts.append(self._get_latex_header(invoice))

    # Invoice content using invoice package
    latex_parts.append(self._generate_invoice_content_with_package(invoice))

    # Footer
    latex_parts.append(self._get_latex_footer())

    return '\n'.join(latex_parts)

  def _get_latex_header(self, invoice: Invoice) -> str:
    """Generate LaTeX document header using fancyhdr approach."""
    # Calculate totals for header
    subtotal = sum(item.amount for item in invoice.billable_items)
    tax_amount = subtotal * invoice.tax_rate if invoice.tax_rate > 0 else 0
    total = subtotal + tax_amount

    # Format addresses
    biller_address = self._format_address(invoice.biller.address)
    client_address = self._format_address(invoice.client.address)

    # Format contact info
    biller_contact_lines = []
    if invoice.biller.contact_email:
      biller_contact_lines.append(f"{invoice.biller.contact_email}")
    if invoice.biller.contact_phone:
      biller_contact_lines.append(f"{invoice.biller.contact_phone}")

    client_contact_lines = []
    if invoice.client.contact_email:
      client_contact_lines.append(f"{invoice.client.contact_email}")
    if invoice.client.contact_phone:
      client_contact_lines.append(f"{invoice.client.contact_phone}")

    return f"""\\documentclass[12pt]{{article}}
\\usepackage{{fancyhdr}}
\\usepackage{{geometry}}
\\usepackage{{graphicx}}
\\usepackage{{xcolor}}
\\usepackage{{enumitem}}
\\usepackage{{hyperref}}
\\usepackage{{tabularx}}
\\usepackage{{fontspec}}

% Custom hyperlink styling
\\hypersetup{{
  colorlinks=false,
  urlcolor=black,
  linkcolor=black,
  citecolor=black,
  filecolor=black,
  pdfborder={{0 0 0}},
  urlbordercolor={{0 0 0}},
  linkbordercolor={{0 0 0}},
  citebordercolor={{0 0 0}},
  filebordercolor={{0 0 0}}
}}

% Custom underline command for hyperlinks
\\newcommand{{\\ulink}}[2]{{\\underline{{\\href{{#1}}{{\\monofont #2}}}}}}

% Custom bullet for itemize
\\renewcommand{{\\labelitemi}}{{\\monofont ›}}

% Custom font setup
\\setmainfont{{GT-Maru-VF}}[
  Path = /Users/matter/fonts/maru vf/,
  Extension = .ttf,
  UprightFont = *,
  BoldFont = *,
  ItalicFont = *,
  BoldItalicFont = *
]

\\newfontfamily{{\\monofont}}{{GT-Maru-Mono-VF}}[
  Path = /Users/matter/fonts/maru vf/,
  Extension = .ttf
]

% Page setup
\\geometry{{margin=0.8in, top=1.75in, right=1.0in}}
\\pagestyle{{fancy}}
\\fancyhf{{}}
\\renewcommand{{\\headrulewidth}}{{0.4pt}}
\\setlength{{\\headheight}}{{1.5cm}}
\\setlength{{\\headsep}}{{1cm}}

% Custom header with invoice info
\\fancyhead[L]{{
    \\begin{{tabular}}{{ll}}
        \\textbf{{invoice \\#}} & {invoice.invoice_number} \\\\
        \\textbf{{date}} & {invoice.issue_date.strftime('%B %d, %Y')} \\\\
        \\textbf{{due date}} & {invoice.due_date.strftime('%B %d, %Y')} \\\\
    \\end{{tabular}}
}}
\\fancyhead[R]{{
    \\begin{{tabular}}{{rl}}
        \\textbf{{total}} & \\${total:.2f} \\\\
        \\textbf{{status}} & pending \\\\
    \\end{{tabular}}
}}

\\begin{{document}}

% Invoice header
\\begin{{minipage}}{{0.6\\textwidth}}
\\textbf{{{invoice.biller.name}}}\\\\
{biller_address.replace('\\\\', ' \\\\ ')}

{chr(10).join(biller_contact_lines).replace(chr(10), ' \\\\ ')}
\\end{{minipage}}
\\hfill
\\begin{{minipage}}{{0.35\\textwidth}}
\\textbf{{{invoice.client.name}}}\\\\
{client_address.replace('\\\\', ' \\\\ ')}

{chr(10).join(client_contact_lines).replace(chr(10), ' \\\\ ')}
\\end{{minipage}}

\\vspace{{1.5cm}}

% Project title
\\Large\\textbf{{services provided}}\\normalsize

\\vspace{{1cm}}"""

    return header_section

  def _generate_invoice_content_with_package(self, invoice: Invoice) -> str:
    """Generate invoice content using fancyhdr header approach."""
    # Calculate totals
    subtotal = sum(item.amount for item in invoice.billable_items)
    tax_amount = subtotal * invoice.tax_rate if invoice.tax_rate > 0 else 0
    total = subtotal + tax_amount

    # Generate line items table
    table_section = f"""
% Line items table
\\begin{{tabularx}}{{\\textwidth}}{{lXrrrr}}
{{\\monofont \\textbf{{type}}}} & {{\\monofont \\textbf{{notes}}}} & {{\\monofont \\textbf{{rate}}}} & {{\\monofont \\textbf{{qty}}}} & {{\\monofont \\textbf{{units}}}} & {{\\monofont \\textbf{{price (USD)}}}} \\\\
"""

    # Generate line items
    for item in invoice.billable_items:
      table_section += f"{{\\monofont service}} & {{\\monofont {self._escape_latex(item.description)}}} & {{\\monofont \\${item.hourly_rate:.2f}}} & {{\\monofont {item.hours_worked:.2f}}} & {{\\monofont hours}} & {{\\monofont \\${item.amount:.2f}}} \\\\\n"

    # Add totals
    table_section += f"{{\\monofont \\textbf{{subtotal}}}} & & & & & {{\\monofont \\${subtotal:.2f}}} \\\\\n"

    if invoice.tax_rate > 0:
      table_section += f"{{\\monofont \\textbf{{Tax ({invoice.tax_rate * 100:.0f}\\%)}}}} & & & & & {{\\monofont \\${tax_amount:.2f}}} \\\\\n"

    table_section += f"{{\\monofont \\textbf{{total}}}} & & & & & {{\\monofont \\textbf{{\\${total:.2f}}}}} \\\\\n"
    table_section += f"\\end{{tabularx}}\n"

    # Generate payment section
    payment_section = f"""
\\vspace{{1.5cm}}

\\Large\\textbf{{payment}}\\normalsize

\\vspace{{0.5cm}}

{invoice.payment_instructions or 'please remit payment within 30 days of invoice date.'}
\\begin{{itemize}}
\\item \\ulink{{https://paypal.me/jmatter4}}{{paypal: jmatter4@gmail.com}}
\\item \\ulink{{https://venmo.com/u/John-Matter}}{{venmo:  @John-Matter}}
\\end{{itemize}}"""

    return table_section + payment_section

  def _get_latex_footer(self) -> str:
    """Generate LaTeX document footer using Amy Fare template style."""
    return r"""
\end{document}"""

  def _format_address(self, address: Address) -> str:
    """Format address for LaTeX template."""
    if not address:
      return ""

    lines = [
      address.street,
      f"{address.city}, {address.state} {address.zip_code}",
      address.country
    ]

    # Filter out empty lines and join with double backslash
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    return "\\\\".join(non_empty_lines)

  def _escape_latex(self, text: str) -> str:
    """Escape special LaTeX characters in text."""
    if not text:
      return ""

    # LaTeX special characters that need escaping
    replacements = {
      '\\': r'\textbackslash{}',
      '{': r'\{',
      '}': r'\}',
      '$': r'\$',
      '&': r'\&',
      '%': r'\%',
      '#': r'\#',
      '^': r'\^{}',
      '_': r'\_',
      '~': r'\textasciitilde{}'
    }

    for old, new in replacements.items():
      text = text.replace(old, new)

    return text
