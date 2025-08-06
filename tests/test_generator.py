"""
Tests for LaTeX template engine module.
"""

import unittest
import tempfile
import os
from datetime import date
from src.generator import LaTeXInvoiceGenerator, LaTeXTemplateManager
from src.models import Invoice, Biller, Client, Address, BillableItem


class TestLaTeXInvoiceGenerator(unittest.TestCase):
  """Test cases for LaTeXInvoiceGenerator class."""
  
  def setUp(self):
    """Set up test fixtures."""
    self.generator = LaTeXInvoiceGenerator()
    
    # Create test invoice
    self.biller = Biller(
      name="John Matter",
      address=Address("123 Main St", "Seattle", "WA", "98101"),
      contact_email="john@example.com",
      contact_phone="(555) 123-4567"
    )
    
    self.client = Client(
      name="Madrona Labs",
      address=Address("456 Oak Ave", "Portland", "OR", "97201"),
      contact_email="contact@madronalabs.com",
      contact_phone="(555) 987-6543",
      prefix="madrona"
    )
    
    self.billable_items = [
      BillableItem("Development work", 5.0, 150.0, 750.0, "madrona"),
      BillableItem("Testing", 2.0, 100.0, 200.0, "madrona")
    ]
    
    self.invoice = Invoice(
      invoice_number="madrona-a23fa87c",
      issue_date=date(2024, 1, 15),
      due_date=date(2024, 2, 14),
      biller=self.biller,
      client=self.client,
      billable_items=self.billable_items,
      tax_rate=0.08
    )
  
  def test_generate_latex(self):
    """Test LaTeX generation from invoice."""
    latex_content = self.generator.generate_latex(self.invoice)
    
    # Should contain key elements
    self.assertIn("madrona-a23fa87c", latex_content)
    self.assertIn("John Matter", latex_content)
    self.assertIn("Madrona Labs", latex_content)
    self.assertIn("Development work", latex_content)
    self.assertIn("Testing", latex_content)
    self.assertIn("$950.00", latex_content)  # Subtotal
    self.assertIn("$76.00", latex_content)   # Tax
    self.assertIn("$1026.00", latex_content) # Total
  
  def test_escape_latex(self):
    """Test LaTeX character escaping."""
    # Test special characters
    escaped = self.generator._escape_latex("Test & More % Stuff")
    self.assertIn("\\&", escaped)
    self.assertIn("\\%", escaped)
    
    # Test backslashes
    escaped = self.generator._escape_latex("Path\\to\\file")
    self.assertIn("\\textbackslash{}", escaped)
    
    # Test empty string
    escaped = self.generator._escape_latex("")
    self.assertEqual(escaped, "")
  
  def test_format_address(self):
    """Test address formatting for LaTeX."""
    address = Address("123 Main St", "Seattle", "WA", "98101")
    formatted = self.generator._format_address(address)
    
    # Should contain LaTeX line breaks
    self.assertIn("\\\\", formatted)
    self.assertIn("123 Main St", formatted)
    self.assertIn("Seattle, WA 98101", formatted)
    self.assertIn("USA", formatted)
  
  def test_format_address_none(self):
    """Test address formatting with None address."""
    formatted = self.generator._format_address(None)
    self.assertEqual(formatted, "")
  
  def test_generate_line_items_latex(self):
    """Test line items LaTeX generation."""
    latex_items = self.generator._generate_line_items_latex(self.billable_items)
    
    # Should contain both items
    self.assertIn("Development work", latex_items)
    self.assertIn("Testing", latex_items)
    self.assertIn("5.00", latex_items)
    self.assertIn("2.00", latex_items)
    self.assertIn("$150.00", latex_items)
    self.assertIn("$100.00", latex_items)
    self.assertIn("$750.00", latex_items)
    self.assertIn("$200.00", latex_items)
  
  def test_prepare_variables(self):
    """Test template variable preparation."""
    variables = self.generator._prepare_variables(self.invoice)
    
    # Check key variables
    self.assertEqual(variables['invoice_number'], "madrona-a23fa87c")
    self.assertEqual(variables['biller_name'], "John Matter")
    self.assertEqual(variables['client_name'], "Madrona Labs")
    self.assertEqual(variables['subtotal'], "$950.00")
    self.assertEqual(variables['tax_rate'], "8.0%")
    self.assertEqual(variables['tax_amount'], "$76.00")
    self.assertEqual(variables['total_amount'], "$1026.00")
    self.assertEqual(variables['total_hours'], 7.0)
    self.assertEqual(variables['item_count'], 2)
  
  def test_custom_template(self):
    """Test custom template loading."""
    # Create temporary template file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
      f.write("Custom template: {{invoice_number}}")
      template_path = f.name
    
    try:
      generator = LaTeXInvoiceGenerator(template_path)
      latex_content = generator.generate_latex(self.invoice)
      
      self.assertIn("Custom template: madrona-a23fa87c", latex_content)
    finally:
      os.unlink(template_path)
  
  def test_default_template_structure(self):
    """Test default template structure."""
    template = self.generator.default_template
        
    # Should contain essential LaTeX elements
    self.assertIn("\\documentclass", template)
    self.assertIn("\\usepackage", template)
    self.assertIn("\\begin{document}", template)
    self.assertIn("\\end{document}", template)
    
    # Should contain template placeholders
    self.assertIn("{{invoice_number}}", template)
    self.assertIn("{{biller_name}}", template)
    self.assertIn("{{client_name}}", template)
    self.assertIn("{{line_items}}", template)


class TestLaTeXTemplateManager(unittest.TestCase):
  """Test cases for LaTeXTemplateManager class."""
  
  def setUp(self):
    """Set up test fixtures."""
    self.temp_dir = tempfile.mkdtemp()
    self.manager = LaTeXTemplateManager(self.temp_dir)
  
  def tearDown(self):
    """Clean up test fixtures."""
    import shutil
    shutil.rmtree(self.temp_dir)
  
  def test_save_and_load_template(self):
    """Test saving and loading templates."""
    template_name = "test_template"
    latex_content = "\\documentclass{article}\\begin{document}Test\\end{document}"
    
    # Save template
    self.manager.save_template(template_name, latex_content)
    
    # Load template
    loaded_content = self.manager.load_template(template_name)
    
    self.assertEqual(loaded_content, latex_content)
  
  def test_list_templates(self):
    """Test listing available templates."""
    # Create some test templates
    self.manager.save_template("template1", "content1")
    self.manager.save_template("template2", "content2")
    
    templates = self.manager.list_templates()
    
    self.assertIn("template1", templates)
    self.assertIn("template2", templates)
  
  def test_load_nonexistent_template(self):
    """Test loading non-existent template."""
    with self.assertRaises(FileNotFoundError):
      self.manager.load_template("nonexistent")
  
  def test_create_custom_template(self):
    """Test creating custom template with customizations."""
    customizations = {
      "invoice_number": "TEST-123",
      "biller_name": "Test Biller"
    }
    
    template_content = self.manager.create_custom_template("custom", customizations)
    
    # Should contain customizations
    self.assertIn("TEST-123", template_content)
    self.assertIn("Test Biller", template_content)
    
    # Should be saved
    loaded_content = self.manager.load_template("custom")
    self.assertEqual(loaded_content, template_content)


if __name__ == '__main__':
  unittest.main() 