"""
Invoice data models module.

Defines the core data structures for invoices, clients, and billable items.
Includes the invoice numbering system using hex hashes.
"""

import hashlib
from datetime import datetime, date
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Address:
  """Represents a physical address."""
  street: str
  city: str
  state: str
  zip_code: str
  country: str = "USA"
  
  def __str__(self) -> str:
    return f"{self.street}\n{self.city}, {self.state} {self.zip_code}\n{self.country}"


@dataclass
class Client:
  """Represents a client for invoicing."""
  name: str
  address: Address
  contact_email: Optional[str] = None
  contact_phone: Optional[str] = None
  tax_id: Optional[str] = None
  prefix: Optional[str] = None


@dataclass
class Biller:
  """Represents the biller (John Matter)."""
  name: str = "John Matter"
  address: Optional[Address] = None
  contact_email: Optional[str] = None
  contact_phone: Optional[str] = None
  tax_id: Optional[str] = None
  website: Optional[str] = None


@dataclass
class BillableItem:
  """Represents a billable line item for an invoice."""
  description: str
  hours_worked: float
  hourly_rate: float
  amount: float
  project: str
  tags: List[str] = field(default_factory=list)
  
  def __post_init__(self):
    """Calculate amount if not provided."""
    if self.amount == 0:
      self.amount = self.hours_worked * self.hourly_rate


@dataclass
class Invoice:
  """Represents a complete invoice."""
  invoice_number: str
  issue_date: date
  due_date: date
  biller: Biller
  client: Client
  billable_items: List[BillableItem] = field(default_factory=list)
  subtotal: float = 0.0
  tax_rate: float = 0.0
  tax_amount: float = 0.0
  total_amount: float = 0.0
  payment_terms: str = "Net 30"
  payment_instructions: str = ""
  notes: str = ""
  terms_and_conditions: str = ""
  
  def __post_init__(self):
    """Calculate totals if not provided."""
    if self.subtotal == 0:
      self.subtotal = sum(item.amount for item in self.billable_items)
    
    if self.tax_amount == 0 and self.tax_rate > 0:
      self.tax_amount = self.subtotal * self.tax_rate
    
    if self.total_amount == 0:
      self.total_amount = self.subtotal + self.tax_amount


class InvoiceNumberGenerator:
  """Generates unique invoice numbers using hex hashes."""
  
  def __init__(self):
    self.hash_length = 8  # 8 characters for readability
  
  def generate_invoice_number(self, client_prefix: str, start_date: str, 
                            end_date: str, total_hours: float, 
                            projects: List[str], timestamp: datetime) -> str:
    """
    Generate a unique invoice number using hex hash.
    
    Args:
      client_prefix: Client identifier prefix
      start_date: Billing period start date
      end_date: Billing period end date
      total_hours: Total billable hours
      projects: List of project names
      timestamp: Invoice generation timestamp
    
    Returns:
      Invoice number in format: {client_prefix}-{hex_hash}
    """
    # Create deterministic string from invoice data
    data_string = self._create_data_string(
      client_prefix, start_date, end_date, total_hours, projects, timestamp
    )
    
    # Generate hash
    hash_value = self._generate_hash(data_string)
    
    # Return formatted invoice number
    return f"{client_prefix}-{hash_value}"
  
  def _create_data_string(self, client_prefix: str, start_date: str, 
                         end_date: str, total_hours: float, 
                         projects: List[str], timestamp: datetime) -> str:
    """Create a deterministic string from invoice data."""
    # Sort projects for consistency
    sorted_projects = sorted(projects)
    
    # Format data consistently
    data_string = (
      f"{client_prefix}:"
      f"{start_date}:"
      f"{end_date}:"
      f"{total_hours:.2f}:"
      f"{','.join(sorted_projects)}:"
      f"{timestamp.isoformat()}"
    )
    
    return data_string
  
  def _generate_hash(self, data_string: str) -> str:
    """Generate SHA-256 hash and return first N characters."""
    hash_object = hashlib.sha256(data_string.encode('utf-8'))
    return hash_object.hexdigest()[:self.hash_length]
  
  def verify_invoice_number(self, invoice_number: str, client_prefix: str,
                          start_date: str, end_date: str, total_hours: float,
                          projects: List[str], timestamp: datetime) -> bool:
    """
    Verify that an invoice number matches the expected hash.
    
    Args:
      invoice_number: Invoice number to verify
      client_prefix: Expected client prefix
      start_date: Billing period start date
      end_date: Billing period end date
      total_hours: Total billable hours
      projects: List of project names
      timestamp: Invoice generation timestamp
    
    Returns:
      True if invoice number matches expected hash
    """
    expected_number = self.generate_invoice_number(
      client_prefix, start_date, end_date, total_hours, projects, timestamp
    )
    return invoice_number == expected_number


class InvoiceCalculator:
  """Handles invoice calculations and financial summaries."""
  
  @staticmethod
  def calculate_subtotal(billable_items: List[BillableItem]) -> float:
    """Calculate invoice subtotal."""
    return sum(item.amount for item in billable_items)
  
  @staticmethod
  def calculate_tax(subtotal: float, tax_rate: float) -> float:
    """Calculate tax amount."""
    tax_amount = subtotal * tax_rate
    # Round to 2 decimal places
    return Decimal(str(tax_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
  
  @staticmethod
  def calculate_total(subtotal: float, tax_amount: float) -> float:
    """Calculate total amount."""
    total = subtotal + tax_amount
    # Round to 2 decimal places
    return Decimal(str(total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
  
  @staticmethod
  def format_currency(amount: float) -> str:
    """Format amount as currency string."""
    return f"${amount:.2f}"
  
  @staticmethod
  def calculate_due_date(issue_date: date, payment_terms: str) -> date:
    """Calculate due date based on payment terms."""
    from datetime import timedelta
    
    if payment_terms.lower() == "net 30":
      return issue_date + timedelta(days=30)
    elif payment_terms.lower() == "net 15":
      return issue_date + timedelta(days=15)
    elif payment_terms.lower() == "due on receipt":
      return issue_date
    else:
      # Default to net 30
      return issue_date + timedelta(days=30)


class InvoiceValidator:
  """Validates invoice data for completeness and correctness."""
  
  @staticmethod
  def validate_invoice(invoice: Invoice) -> List[str]:
    """
    Validate invoice data and return list of errors.
    
    Args:
      invoice: Invoice object to validate
    
    Returns:
      List of validation error messages
    """
    errors = []
    
    # Check required fields
    if not invoice.invoice_number:
      errors.append("Invoice number is required")
    
    if not invoice.biller.name:
      errors.append("Biller name is required")
    
    if not invoice.client.name:
      errors.append("Client name is required")
    
    if not invoice.billable_items:
      errors.append("At least one billable item is required")
    
    # Check financial calculations
    calculated_subtotal = InvoiceCalculator.calculate_subtotal(invoice.billable_items)
    if abs(calculated_subtotal - invoice.subtotal) > 0.01:
      errors.append(f"Subtotal calculation error: expected {calculated_subtotal}, got {invoice.subtotal}")
    
    calculated_tax = InvoiceCalculator.calculate_tax(invoice.subtotal, invoice.tax_rate)
    if abs(float(calculated_tax) - invoice.tax_amount) > 0.01:
      errors.append(f"Tax calculation error: expected {calculated_tax}, got {invoice.tax_amount}")
    
    calculated_total = InvoiceCalculator.calculate_total(invoice.subtotal, invoice.tax_amount)
    if abs(float(calculated_total) - invoice.total_amount) > 0.01:
      errors.append(f"Total calculation error: expected {calculated_total}, got {invoice.total_amount}")
    
    return errors
  
  @staticmethod
  def validate_billable_item(item: BillableItem) -> List[str]:
    """Validate a single billable item."""
    errors = []
    
    if not item.description:
      errors.append("Item description is required")
    
    if item.hours_worked <= 0:
      errors.append("Hours worked must be greater than 0")
    
    if item.hourly_rate <= 0:
      errors.append("Hourly rate must be greater than 0")
    
    expected_amount = item.hours_worked * item.hourly_rate
    if abs(expected_amount - item.amount) > 0.01:
      errors.append(f"Item amount calculation error: expected {expected_amount}, got {item.amount}")
    
    return errors 