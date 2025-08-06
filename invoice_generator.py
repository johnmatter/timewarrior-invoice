#!/usr/bin/env python3
"""
Invoice Generator - Timewarrior to LaTeX PDF Invoice Generator
"""

import sys
import os
import subprocess
import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List

import click

from src.config import ConfigManager
from src.parser import TimewarriorParser
from src.models import Invoice, Biller, Client, Address, BillableItem, InvoiceNumberGenerator, InvoiceCalculator, InvoiceValidator
from src.generator import LaTeXInvoiceGenerator
from src.compiler import PDFGenerator, CompilationError


def generate_output_path(client_id: str, client_data: dict, invoice_number: str, start_date: str) -> str:
  """Generate organized output path: output/{client}/{year}/{month}/{prefix}-{hash}.pdf"""
  # Parse start date to get year and month
  start_dt = datetime.strptime(start_date, '%Y-%m-%d')
  year = str(start_dt.year)
  month = f"{start_dt.month:02d}"
  
  # Create directory structure
  output_dir = Path("output") / client_id / year / month
  output_dir.mkdir(parents=True, exist_ok=True)
  
  # Generate filename: {prefix}-{hash}.pdf
  filename = f"{invoice_number}.pdf"
  
  return str(output_dir / filename)


def cleanup_intermediate_files(output_path: str, verbose: bool = False):
  """Clean up intermediate LaTeX files except for the .tex file."""
  output_dir = Path(output_path).parent
  output_stem = Path(output_path).stem
  
  # Files to delete
  files_to_delete = [
    output_dir / f"{output_stem}.aux",
    output_dir / f"{output_stem}.log",
    output_dir / f"{output_stem}.out",
    output_dir / f"{output_stem}.fls",
    output_dir / f"{output_stem}.fdb_latexmk",
    output_dir / f"{output_stem}.synctex.gz"
  ]
  
  for file_path in files_to_delete:
    if file_path.exists():
      file_path.unlink()
      if verbose:
        click.echo(f"Cleaned up: {file_path}")


@click.command()
@click.option('--start-date', required=True, help='Start date of billing period (YYYY-MM-DD)')
@click.option('--end-date', required=True, help='End date of billing period (YYYY-MM-DD)')
@click.option('--client', required=True, help='Client identifier (e.g., madrona, goodhertz)')
@click.option('--output', help='Output PDF filename (optional, will use organized path if not specified)')
@click.option('--config', help='Configuration file path (default: ~/.config/timewarrior/invoice/config.yaml)')
@click.option('--template', help='Custom LaTeX template path')
@click.option('--format', 'export_format', default='json', type=click.Choice(['json', 'csv']),
              help='Timewarrior export format')
@click.option('--dry-run', is_flag=True, help='Generate LaTeX without compiling to PDF')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def main(start_date: str, end_date: str, client: str, output: str,
         config: str, template: str, export_format: str, dry_run: bool, verbose: bool):
  """Generate invoice from Timewarrior data."""
  try:
    # Set default config path if not specified
    if not config:
      config = os.path.expanduser("~/.config/timewarrior/invoice/config.yaml")
    
    # Load configuration
    config_manager = ConfigManager(config)
    invoice_config = config_manager.load_config()

    if verbose:
      click.echo("Configuration loaded successfully")
      click.echo(f"Starting invoice generation for {client} from {start_date} to {end_date}")

    # Validate client exists
    client_data = config_manager.get_client(client)
    if not client_data:
      click.echo(f"Error: Client '{client}' not found in configuration", err=True)
      click.echo("Available clients:", err=True)
      for client_id in invoice_config.clients.keys():
        click.echo(f"  - {client_id}", err=True)
      sys.exit(1)

    # Export Timewarrior data
    timew_data = export_timewarrior_data(start_date, end_date, export_format, verbose)

    if verbose:
      click.echo(f"Exported {len(timew_data)} time tracking entries")

    # Parse Timewarrior data
    parser = TimewarriorParser()
    time_entries = parser.parse_export_data(timew_data, export_format)

    if not time_entries:
      click.echo("No time tracking entries found for the specified period", err=True)
      sys.exit(1)

    # Filter entries for the specified client
    client_entries = filter_entries_for_client(time_entries, client)

    if not client_entries:
      click.echo(f"No time tracking entries found for client '{client}' in the specified period", err=True)
      sys.exit(1)

    # Apply hourly rates
    billable_items = parser.apply_hourly_rates(client_entries, config_manager)

    if verbose:
      total_hours = sum(item.hours_worked for item in billable_items)
      total_amount = sum(item.amount for item in billable_items)
      click.echo(f"Generated {len(billable_items)} billable items: {total_hours:.2f} hours, ${total_amount:.2f}")

    # Create invoice
    invoice = create_invoice(client, client_data, billable_items, start_date, end_date, invoice_config, verbose)

    # Validate invoice
    errors = InvoiceValidator.validate_invoice(invoice)
    if errors:
      click.echo("Invoice validation errors:", err=True)
      for error in errors:
        click.echo(f"  - {error}", err=True)
      sys.exit(1)

    if verbose:
      click.echo(f"Invoice {invoice.invoice_number} created successfully")

    # Generate organized output path if not specified
    if not output:
      output = generate_output_path(client, client_data, invoice.invoice_number, start_date)
      if verbose:
        click.echo(f"Using organized output path: {output}")

    # Generate LaTeX
    generator = LaTeXInvoiceGenerator(template)
    latex_content = generator.generate_latex(invoice)

    if verbose:
      click.echo("LaTeX content generated")

    # Save LaTeX file if requested or in dry-run mode
    if dry_run or verbose:
      latex_file = output.replace('.pdf', '.tex')
      with open(latex_file, 'w', encoding='utf-8') as f:
        f.write(latex_content)
      click.echo(f"LaTeX file saved: {latex_file}")

    if dry_run:
      click.echo("Dry run completed. LaTeX file generated but PDF compilation skipped.")
      return

    # Compile to PDF
    pdf_generator = PDFGenerator(invoice_config.latex_command)

    try:
      pdf_path = pdf_generator.generate_pdf(latex_content, output)
      click.echo(f"PDF invoice generated successfully: {pdf_path}")

      # Clean up intermediate files
      cleanup_intermediate_files(output, verbose)

      if verbose:
        click.echo(f"Invoice details:")
        click.echo(f"  Number: {invoice.invoice_number}")
        click.echo(f"  Client: {invoice.client.name}")
        click.echo(f"  Period: {start_date} to {end_date}")
        click.echo(f"  Total: {InvoiceCalculator.format_currency(invoice.total_amount)}")

    except CompilationError as e:
      click.echo(f"PDF compilation failed: {e.message}", err=True)
      if verbose and e.latex_output:
        click.echo("LaTeX compilation output:", err=True)
        click.echo(e.latex_output, err=True)
      sys.exit(1)

  except Exception as e:
    click.echo(f"Error: {str(e)}", err=True)
    if verbose:
      import traceback
      traceback.print_exc()
    sys.exit(1)


def export_timewarrior_data(start_date: str, end_date: str, format_type: str, verbose: bool) -> str:
  """Export data from Timewarrior for the specified date range."""
  try:
    # Build timew export command
    cmd = ['timew', 'export', f'{start_date}', '-', f'{end_date}']

    if verbose:
      click.echo(f"Running command: {' '.join(cmd)}")

    # Execute timew export
    result = subprocess.run(
      cmd,
      capture_output=True,
      text=True,
      timeout=30
    )

    if result.returncode != 0:
      click.echo(f"Timewarrior export failed: {result.stderr}", err=True)
      sys.exit(1)

    return result.stdout

  except subprocess.TimeoutExpired:
    click.echo("Timewarrior export timed out", err=True)
    sys.exit(1)
  except FileNotFoundError:
    click.echo("Timewarrior command not found. Please ensure Timewarrior is installed and in PATH.", err=True)
    sys.exit(1)


def filter_entries_for_client(entries: List, client_id: str) -> List:
  """Filter time entries for the specified client."""
  client_entries = []

  for entry in entries:
    # Check if entry belongs to this client
    if entry.project == client_id:
      client_entries.append(entry)
    elif entry.tags and client_id in entry.tags:
      client_entries.append(entry)

  return client_entries


def create_invoice(client_id: str, client_data: dict, billable_items: List[BillableItem],
                  start_date: str, end_date: str, config, verbose: bool) -> Invoice:
  """Create an Invoice object from the provided data."""

  # Create biller
  biller = Biller(
    name=config.biller_name,
    address=config.biller_address,
    contact_email=config.biller_email,
    contact_phone=config.biller_phone,
    tax_id=config.biller_tax_id,
    website=config.biller_website
  )

  # Create client
  client_address = Address(
    street=client_data['address']['street'],
    city=client_data['address']['city'],
    state=client_data['address']['state'],
    zip_code=client_data['address']['zip_code'],
    country=client_data['address'].get('country', 'USA')
  )

  client = Client(
    name=client_data['name'],
    address=client_address,
    contact_email=client_data.get('contact_email'),
    contact_phone=client_data.get('contact_phone'),
    tax_id=client_data.get('tax_id'),
    prefix=client_data['prefix']
  )

  # Generate invoice number
  number_generator = InvoiceNumberGenerator()
  
  # Calculate time period from billable items instead of using current timestamp
  if billable_items:
    # Get the first and last entry times from the timewarrior data
    # We'll use the start_date and end_date as the time period
    time_period_start = datetime.strptime(start_date, '%Y-%m-%d')
    time_period_end = datetime.strptime(end_date, '%Y-%m-%d')
    # Use the midpoint of the time period as the timestamp
    time_period_midpoint = time_period_start + (time_period_end - time_period_start) / 2
  else:
    # Fallback to current time if no billable items
    time_period_midpoint = datetime.now()
  
  total_hours = sum(item.hours_worked for item in billable_items)
  projects = list(set(item.project for item in billable_items))

  invoice_number = number_generator.generate_invoice_number(
    client_data['prefix'],
    start_date,
    end_date,
    total_hours,
    projects,
    time_period_midpoint
  )

  if verbose:
    click.echo(f"Generated invoice number: {invoice_number}")

  # Calculate dates
  issue_date = date.today()
  due_date = InvoiceCalculator.calculate_due_date(issue_date, config.default_payment_terms)

  # Create invoice
  invoice = Invoice(
    invoice_number=invoice_number,
    issue_date=issue_date,
    due_date=due_date,
    biller=biller,
    client=client,
    billable_items=billable_items,
    tax_rate=config.default_tax_rate,
    payment_terms=config.default_payment_terms,
    payment_instructions=config.default_payment_instructions,
    notes=config.default_notes,
    terms_and_conditions=config.default_terms_and_conditions
  )

  return invoice


@click.command()
@click.option('--config', help='Configuration file path (default: ~/.config/timewarrior/invoice/config.yaml)')
def init_config(config: str):
  """Initialize a new configuration file with default settings."""
  try:
    if not config:
      config = os.path.expanduser("~/.config/timewarrior/invoice/config.yaml")
    
    # Create config directory if it doesn't exist
    config_dir = os.path.dirname(config)
    os.makedirs(config_dir, exist_ok=True)
    
    config_manager = ConfigManager(config)
    
    # Create and save default configuration
    default_config = config_manager._create_default_config()
    config_manager.save_config(default_config, config)

    click.echo(f"Configuration file created: {config}")
    click.echo("Please edit the configuration file to set your personal information and client details.")

  except Exception as e:
    click.echo(f"Error creating configuration: {str(e)}", err=True)
    sys.exit(1)


@click.command()
@click.option('--config', help='Configuration file path (default: ~/.config/timewarrior/invoice/config.yaml)')
def list_clients(config: str):
  """List all configured clients."""
  try:
    if not config:
      config = os.path.expanduser("~/.config/timewarrior/invoice/config.yaml")
    
    config_manager = ConfigManager(config)
    invoice_config = config_manager.load_config()

    click.echo("Configured clients:")
    for client_id, client_data in invoice_config.clients.items():
      click.echo(f"  {client_id}: {client_data['name']}")

  except Exception as e:
    click.echo(f"Error loading configuration: {str(e)}", err=True)
    sys.exit(1)


@click.command()
@click.option('--config', help='Configuration file path (default: ~/.config/timewarrior/invoice/config.yaml)')
def check_environment(config: str):
  """Check if the environment is properly configured."""
  try:
    # Check Timewarrior
    try:
      result = subprocess.run(['timew', '--version'], capture_output=True, text=True, timeout=10)
      if result.returncode == 0:
        click.echo("✓ Timewarrior is installed")
      else:
        click.echo("✗ Timewarrior is not working properly")
    except (FileNotFoundError, subprocess.TimeoutExpired):
      click.echo("✗ Timewarrior is not installed or not in PATH")

    # Check LaTeX
    try:
      result = subprocess.run(['pdflatex', '--version'], capture_output=True, text=True, timeout=10)
      if result.returncode == 0:
        click.echo("✓ LaTeX (pdflatex) is installed")
      else:
        click.echo("✗ LaTeX (pdflatex) is not working properly")
    except (FileNotFoundError, subprocess.TimeoutExpired):
      click.echo("✗ LaTeX (pdflatex) is not installed or not in PATH")

    # Check configuration
    config_manager = ConfigManager(config)
    try:
      invoice_config = config_manager.load_config()
      errors = config_manager.validate_config(invoice_config)
      if errors:
        click.echo("✗ Configuration has errors:")
        for error in errors:
          click.echo(f"  - {error}")
      else:
        click.echo("✓ Configuration is valid")
    except Exception as e:
      click.echo(f"✗ Configuration error: {str(e)}")

  except Exception as e:
    click.echo(f"Error checking environment: {str(e)}", err=True)
    sys.exit(1)


# Create command group
@click.group()
def cli():
  """Invoice Generator - Timewarrior to LaTeX PDF Invoice Generator"""
  pass


# Add commands to group
cli.add_command(main, name='generate')
cli.add_command(init_config, name='init')
cli.add_command(list_clients, name='clients')
cli.add_command(check_environment, name='check')


if __name__ == '__main__':
  cli()
