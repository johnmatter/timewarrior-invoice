"""
Tests for invoice data models module.
"""

import unittest
from datetime import datetime, date
from src.models import (
  Address, Client, Biller, BillableItem, Invoice,
  InvoiceNumberGenerator, InvoiceCalculator, InvoiceValidator
)


class TestAddress(unittest.TestCase):
  """Test cases for Address dataclass."""
  
  def test_address_creation(self):
    """Test Address object creation."""
    address = Address(
      street="123 Main St",
      city="Seattle",
      state="WA",
      zip_code="98101"
    )
    
    self.assertEqual(address.street, "123 Main St")
    self.assertEqual(address.city, "Seattle")
    self.assertEqual(address.state, "WA")
    self.assertEqual(address.zip_code, "98101")
    self.assertEqual(address.country, "USA")  # Default value
  
  def test_address_string_representation(self):
    """Test Address string formatting."""
    address = Address(
      street="123 Main St",
      city="Seattle",
      state="WA",
      zip_code="98101"
    )
    
    expected = "123 Main St\nSeattle, WA 98101\nUSA"
    self.assertEqual(str(address), expected)


class TestClient(unittest.TestCase):
  """Test cases for Client dataclass."""
  
  def test_client_creation(self):
    """Test Client object creation."""
    address = Address("123 Main St", "Seattle", "WA", "98101")
    client = Client(
      name="Madrona Labs",
      address=address,
      contact_email="contact@madronalabs.com",
      contact_phone="(555) 123-4567",
      tax_id="12-3456789",
      prefix="madrona"
    )
    
    self.assertEqual(client.name, "Madrona Labs")
    self.assertEqual(client.address, address)
    self.assertEqual(client.contact_email, "contact@madronalabs.com")
    self.assertEqual(client.contact_phone, "(555) 123-4567")
    self.assertEqual(client.tax_id, "12-3456789")
    self.assertEqual(client.prefix, "madrona")


class TestBiller(unittest.TestCase):
  """Test cases for Biller dataclass."""
  
  def test_biller_creation(self):
    """Test Biller object creation."""
    address = Address("456 Oak Ave", "Portland", "OR", "97201")
    biller = Biller(
      name="John Matter",
      address=address,
      contact_email="john@example.com",
      contact_phone="(555) 987-6543",
      tax_id="98-7654321",
      website="https://example.com"
    )
    
    self.assertEqual(biller.name, "John Matter")
    self.assertEqual(biller.address, address)
    self.assertEqual(biller.contact_email, "john@example.com")
    self.assertEqual(biller.contact_phone, "(555) 987-6543")
    self.assertEqual(biller.tax_id, "98-7654321")
    self.assertEqual(biller.website, "https://example.com")
  
  def test_biller_default_name(self):
    """Test Biller default name."""
    biller = Biller()
    self.assertEqual(biller.name, "John Matter")


class TestBillableItem(unittest.TestCase):
  """Test cases for BillableItem dataclass."""
  
  def test_billable_item_creation(self):
    """Test BillableItem object creation."""
    item = BillableItem(
      description="Development work",
      hours_worked=5.0,
      hourly_rate=150.0,
      amount=750.0,
      project="madrona",
      tags=["development", "bugfix"]
    )
    
    self.assertEqual(item.description, "Development work")
    self.assertEqual(item.hours_worked, 5.0)
    self.assertEqual(item.hourly_rate, 150.0)
    self.assertEqual(item.amount, 750.0)
    self.assertEqual(item.project, "madrona")
    self.assertEqual(item.tags, ["development", "bugfix"])
  
  def test_billable_item_auto_calculation(self):
    """Test automatic amount calculation."""
    item = BillableItem(
      description="Development work",
      hours_worked=5.0,
      hourly_rate=150.0,
      amount=0.0,  # Will be calculated automatically
      project="madrona"
    )
    
    self.assertEqual(item.amount, 750.0)  # 5.0 * 150.0


class TestInvoice(unittest.TestCase):
  """Test cases for Invoice dataclass."""
  
  def setUp(self):
    """Set up test fixtures."""
    self.biller = Biller(name="John Matter")
    self.client = Client(name="Madrona Labs", address=Address("123 St", "Seattle", "WA", "98101"))
    self.billable_items = [
      BillableItem("Development", 5.0, 150.0, 750.0, "madrona"),
      BillableItem("Testing", 2.0, 100.0, 200.0, "madrona")
    ]
  
  def test_invoice_creation(self):
    """Test Invoice object creation."""
    invoice = Invoice(
      invoice_number="madrona-a23fa87c",
      issue_date=date(2024, 1, 15),
      due_date=date(2024, 2, 14),
      biller=self.biller,
      client=self.client,
      billable_items=self.billable_items,
      tax_rate=0.08
    )
    
    self.assertEqual(invoice.invoice_number, "madrona-a23fa87c")
    self.assertEqual(invoice.issue_date, date(2024, 1, 15))
    self.assertEqual(invoice.due_date, date(2024, 2, 14))
    self.assertEqual(invoice.biller, self.biller)
    self.assertEqual(invoice.client, self.client)
    self.assertEqual(len(invoice.billable_items), 2)
    self.assertEqual(invoice.tax_rate, 0.08)
  
  def test_invoice_auto_calculation(self):
    """Test automatic invoice calculations."""
    invoice = Invoice(
      invoice_number="madrona-a23fa87c",
      issue_date=date(2024, 1, 15),
      due_date=date(2024, 2, 14),
      biller=self.biller,
      client=self.client,
      billable_items=self.billable_items,
      tax_rate=0.08
    )
    
    # Subtotal should be calculated automatically
    self.assertEqual(invoice.subtotal, 950.0)  # 750 + 200
    
    # Tax amount should be calculated automatically
    self.assertEqual(invoice.tax_amount, 76.0)  # 950 * 0.08
    
    # Total should be calculated automatically
    self.assertEqual(invoice.total_amount, 1026.0)  # 950 + 76


class TestInvoiceNumberGenerator(unittest.TestCase):
  """Test cases for InvoiceNumberGenerator class."""
  
  def setUp(self):
    """Set up test fixtures."""
    self.generator = InvoiceNumberGenerator()
  
  def test_generate_invoice_number(self):
    """Test invoice number generation."""
    timestamp = datetime(2024, 1, 15, 10, 30, 0)
    invoice_number = self.generator.generate_invoice_number(
      client_prefix="madrona",
      start_date="2024-01-01",
      end_date="2024-01-31",
      total_hours=25.5,
      projects=["development", "testing"],
      timestamp=timestamp
    )
    
    # Should have format: madrona-{8_char_hash}
    self.assertTrue(invoice_number.startswith("madrona-"))
    self.assertEqual(len(invoice_number), 16)  # madrona- + 8 chars
    
    # Hash part should be hexadecimal
    hash_part = invoice_number.split("-")[1]
    self.assertTrue(all(c in "0123456789abcdef" for c in hash_part))
  
  def test_deterministic_generation(self):
    """Test that same inputs generate same invoice number."""
    timestamp = datetime(2024, 1, 15, 10, 30, 0)
    
    number1 = self.generator.generate_invoice_number(
      "madrona", "2024-01-01", "2024-01-31", 25.5, ["dev", "test"], timestamp
    )
    
    number2 = self.generator.generate_invoice_number(
      "madrona", "2024-01-01", "2024-01-31", 25.5, ["dev", "test"], timestamp
    )
    
    self.assertEqual(number1, number2)
  
  def test_verify_invoice_number(self):
    """Test invoice number verification."""
    timestamp = datetime(2024, 1, 15, 10, 30, 0)
    invoice_number = self.generator.generate_invoice_number(
      "madrona", "2024-01-01", "2024-01-31", 25.5, ["dev", "test"], timestamp
    )
    
    # Should verify correctly
    self.assertTrue(self.generator.verify_invoice_number(
      invoice_number, "madrona", "2024-01-01", "2024-01-31", 25.5, ["dev", "test"], timestamp
    ))
    
    # Should fail with different data
    self.assertFalse(self.generator.verify_invoice_number(
      invoice_number, "goodhertz", "2024-01-01", "2024-01-31", 25.5, ["dev", "test"], timestamp
    ))


class TestInvoiceCalculator(unittest.TestCase):
  """Test cases for InvoiceCalculator class."""
  
  def test_calculate_subtotal(self):
    """Test subtotal calculation."""
    items = [
      BillableItem("Dev", 5.0, 150.0, 750.0, "project"),
      BillableItem("Test", 2.0, 100.0, 200.0, "project")
    ]
    
    subtotal = InvoiceCalculator.calculate_subtotal(items)
    self.assertEqual(subtotal, 950.0)
  
  def test_calculate_tax(self):
    """Test tax calculation."""
    tax_amount = InvoiceCalculator.calculate_tax(1000.0, 0.08)
    self.assertEqual(tax_amount, 80.0)
  
  def test_calculate_total(self):
    """Test total calculation."""
    total = InvoiceCalculator.calculate_total(1000.0, 80.0)
    self.assertEqual(total, 1080.0)
  
  def test_format_currency(self):
    """Test currency formatting."""
    formatted = InvoiceCalculator.format_currency(1234.56)
    self.assertEqual(formatted, "$1234.56")
  
  def test_calculate_due_date(self):
    """Test due date calculation."""
    issue_date = date(2024, 1, 15)
    
    # Net 30
    due_date = InvoiceCalculator.calculate_due_date(issue_date, "Net 30")
    self.assertEqual(due_date, date(2024, 2, 14))
    
    # Net 15
    due_date = InvoiceCalculator.calculate_due_date(issue_date, "Net 15")
    self.assertEqual(due_date, date(2024, 1, 30))
    
    # Due on receipt
    due_date = InvoiceCalculator.calculate_due_date(issue_date, "Due on receipt")
    self.assertEqual(due_date, date(2024, 1, 15))


class TestInvoiceValidator(unittest.TestCase):
  """Test cases for InvoiceValidator class."""
  
  def setUp(self):
    """Set up test fixtures."""
    self.biller = Biller(name="John Matter")
    self.client = Client(name="Madrona Labs", address=Address("123 St", "Seattle", "WA", "98101"))
    self.billable_items = [
      BillableItem("Development", 5.0, 150.0, 750.0, "madrona")
    ]
  
  def test_validate_invoice_success(self):
    """Test successful invoice validation."""
    invoice = Invoice(
      invoice_number="madrona-a23fa87c",
      issue_date=date(2024, 1, 15),
      due_date=date(2024, 2, 14),
      biller=self.biller,
      client=self.client,
      billable_items=self.billable_items
    )
    
    errors = InvoiceValidator.validate_invoice(invoice)
    self.assertEqual(len(errors), 0)
  
  def test_validate_invoice_missing_fields(self):
    """Test invoice validation with missing fields."""
    invoice = Invoice(
      invoice_number="",  # Missing
      issue_date=date(2024, 1, 15),
      due_date=date(2024, 2, 14),
      biller=Biller(name=""),  # Missing name
      client=Client(name="", address=Address("", "", "", "")),  # Missing name
      billable_items=[]  # Missing items
    )
    
    errors = InvoiceValidator.validate_invoice(invoice)
    self.assertGreater(len(errors), 0)
    self.assertIn("Invoice number is required", errors)
    self.assertIn("Biller name is required", errors)
    self.assertIn("Client name is required", errors)
    self.assertIn("At least one billable item is required", errors)
  
  def test_validate_billable_item(self):
    """Test billable item validation."""
    # Valid item
    item = BillableItem("Development", 5.0, 150.0, 750.0, "madrona")
    errors = InvoiceValidator.validate_billable_item(item)
    self.assertEqual(len(errors), 0)
    
    # Invalid item
    item = BillableItem("", 0.0, 0.0, 0.0, "madrona")
    errors = InvoiceValidator.validate_billable_item(item)
    self.assertGreater(len(errors), 0)


if __name__ == '__main__':
  unittest.main() 