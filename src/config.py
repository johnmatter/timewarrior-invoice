"""
Configuration management module.

Handles loading and validation of configuration files for
invoice generation settings, client information, and rates.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .models import Address, Client, Biller


@dataclass
class InvoiceConfig:
  """Configuration settings for invoice generation."""

  # Biller information
  biller_name: str = "Mr Socially Necessary Labour Time"
  biller_address: Optional[Address] = None
  biller_email: Optional[str] = None
  biller_phone: Optional[str] = None
  biller_tax_id: Optional[str] = None
  biller_website: Optional[str] = None

  # Default settings
  default_tax_rate: float = 0.0
  default_payment_terms: str = "Net 30"
  default_payment_instructions: str = ""
  default_notes: str = ""
  default_terms_and_conditions: str = ""

  # Invoice numbering
  invoice_number_prefix: str = ""
  invoice_number_format: str = "hash"  # hash, sequential, custom

  # LaTeX settings
  latex_command: str = "pdflatex"
  template_path: Optional[str] = None

  # Client information
  clients: Dict[str, Dict[str, Any]] = field(default_factory=dict)

  # Hourly rates
  hourly_rates: Dict[str, float] = field(default_factory=dict)
  default_hourly_rate: float = 0.0

  # Output settings
  output_directory: str = "invoices"
  output_format: str = "pdf"  # pdf, tex, both

  def __post_init__(self):
    """Set default values after initialization."""
    if not self.biller_address:
      self.biller_address = Address(
        street="[Your Street Address]",
        city="[Your City]",
        state="[Your State]",
        zip_code="[Your ZIP]"
      )


class ConfigManager:
  """Manages configuration loading, validation, and access."""

  def __init__(self, config_path: Optional[str] = None):
    """
    Initialize configuration manager.

    Args:
      config_path: Path to configuration file
    """
    self.config_path = config_path or "config/default.yaml"
    self.config = None

  def load_config(self, config_path: Optional[str] = None) -> InvoiceConfig:
    """
    Load configuration from YAML file.

    Args:
      config_path: Optional path to config file

    Returns:
      InvoiceConfig object
    """
    path = config_path or self.config_path

    if not os.path.exists(path):
      # Try to load from config/default.yaml if it exists
      default_path = "config/default.yaml"
      if os.path.exists(default_path):
        path = default_path
      else:
        # Create minimal default configuration
        config = self._create_default_config()
        self.save_config(config, path)
        return config

    try:
      with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

      config = self._parse_config_data(data)
      self.config = config
      return config

    except yaml.YAMLError as e:
      raise ValueError(f"Invalid YAML configuration: {e}")
    except Exception as e:
      raise ValueError(f"Error loading configuration: {e}")

  def save_config(self, config: InvoiceConfig, config_path: Optional[str] = None) -> None:
    """
    Save configuration to YAML file.

    Args:
      config: InvoiceConfig object to save
      config_path: Optional path to save config file
    """
    path = config_path or self.config_path

    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Convert config to dictionary
    data = self._config_to_dict(config)

    try:
      with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, indent=2)
    except Exception as e:
      raise ValueError(f"Error saving configuration: {e}")

  def _create_default_config(self) -> InvoiceConfig:
    """Create a default configuration."""
    config = InvoiceConfig()
    
    # Set up minimal default rates
    config.hourly_rates = {
      "default": 150.0,
      "development": 150.0,
      "programming": 150.0,
      "coding": 150.0,
      "consulting": 200.0,
      "testing": 100.0,
      "qa": 100.0,
      "documentation": 120.0,
      "docs": 120.0,
      "design": 180.0,
      "ui": 180.0,
      "ux": 180.0,
      "research": 160.0,
      "planning": 140.0,
      "meeting": 140.0,
      "review": 130.0,
      "debugging": 140.0,
      "bugfix": 140.0,
      "maintenance": 130.0,
      "support": 120.0,
      "training": 180.0,
      "general": 150.0
    }
    
    config.default_hourly_rate = 150.0
    
    return config

  def _parse_config_data(self, data: Dict[str, Any]) -> InvoiceConfig:
    """Parse YAML data into InvoiceConfig object."""
    config = InvoiceConfig()

    # Parse biller information
    if 'biller' in data:
      biller_data = data['biller']
      config.biller_name = biller_data.get('name', config.biller_name)
      config.biller_email = biller_data.get('email')
      config.biller_phone = biller_data.get('phone')
      config.biller_tax_id = biller_data.get('tax_id')
      config.biller_website = biller_data.get('website')

      if 'address' in biller_data:
        addr_data = biller_data['address']
        config.biller_address = Address(
          street=addr_data.get('street', ''),
          city=addr_data.get('city', ''),
          state=addr_data.get('state', ''),
          zip_code=addr_data.get('zip_code', ''),
          country=addr_data.get('country', 'USA')
        )

    # Parse default settings
    if 'defaults' in data:
      defaults = data['defaults']
      config.default_tax_rate = defaults.get('tax_rate', config.default_tax_rate)
      config.default_payment_terms = defaults.get('payment_terms', config.default_payment_terms)
      config.default_payment_instructions = defaults.get('payment_instructions', config.default_payment_instructions)
      config.default_notes = defaults.get('notes', config.default_notes)
      config.default_terms_and_conditions = defaults.get('terms_and_conditions', config.default_terms_and_conditions)

    # Parse invoice numbering
    if 'invoice_numbering' in data:
      numbering = data['invoice_numbering']
      config.invoice_number_prefix = numbering.get('prefix', config.invoice_number_prefix)
      config.invoice_number_format = numbering.get('format', config.invoice_number_format)

    # Parse LaTeX settings
    if 'latex' in data:
      latex_data = data['latex']
      config.latex_command = latex_data.get('command', config.latex_command)
      config.template_path = latex_data.get('template_path')

    # Parse clients
    if 'clients' in data:
      config.clients = data['clients']

    # Parse hourly rates
    if 'hourly_rates' in data:
      config.hourly_rates = data['hourly_rates']
      config.default_hourly_rate = config.hourly_rates.get('default', config.default_hourly_rate)

    # Parse output settings
    if 'output' in data:
      output_data = data['output']
      config.output_directory = output_data.get('directory', config.output_directory)
      config.output_format = output_data.get('format', config.output_format)

    return config

  def _config_to_dict(self, config: InvoiceConfig) -> Dict[str, Any]:
    """Convert InvoiceConfig object to dictionary for YAML serialization."""
    data = {
      'biller': {
        'name': config.biller_name,
        'email': config.biller_email,
        'phone': config.biller_phone,
        'tax_id': config.biller_tax_id,
        'website': config.biller_website
      },
      'defaults': {
        'tax_rate': config.default_tax_rate,
        'payment_terms': config.default_payment_terms,
        'payment_instructions': config.default_payment_instructions,
        'notes': config.default_notes,
        'terms_and_conditions': config.default_terms_and_conditions
      },
      'invoice_numbering': {
        'prefix': config.invoice_number_prefix,
        'format': config.invoice_number_format
      },
      'latex': {
        'command': config.latex_command,
        'template_path': config.template_path
      },
      'clients': config.clients,
      'hourly_rates': config.hourly_rates,
      'output': {
        'directory': config.output_directory,
        'format': config.output_format
      }
    }

    # Add biller address if present
    if config.biller_address:
      data['biller']['address'] = {
        'street': config.biller_address.street,
        'city': config.biller_address.city,
        'state': config.biller_address.state,
        'zip_code': config.biller_address.zip_code,
        'country': config.biller_address.country
      }

    return data

  def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
    """Get client information by ID."""
    if not self.config:
      self.load_config()

    return self.config.clients.get(client_id)

  def get_hourly_rate(self, project_or_tag: str) -> float:
    """Get hourly rate for project or tag from global rates."""
    if not self.config:
      self.load_config()

    return self.config.hourly_rates.get(project_or_tag, self.config.default_hourly_rate)

  def get_client_task_rate(self, client_id: str, task: str) -> float:
    """
    Get hourly rate for a specific client and task combination.

    This allows for client-specific task rates using the nested structure.
    """
    if not self.config:
      self.load_config()

    # Get client data
    client_data = self.config.clients.get(client_id)
    if not client_data:
      # Client not found, use global task rate
      return self.get_hourly_rate(task)

    # Check for client-specific rates
    client_rates = client_data.get('rates', {})
    if task in client_rates:
      return client_rates[task]

    # Check for client default rate
    if 'default' in client_rates:
      return client_rates['default']

    # Fall back to global task rate
    return self.get_hourly_rate(task)

  def get_client_rates(self, client_id: str) -> Dict[str, float]:
    """
    Get all rates for a specific client.

    Returns a dictionary of task -> rate mappings for the client.
    """
    if not self.config:
      self.load_config()

    client_data = self.config.clients.get(client_id)
    if not client_data:
      return {}

    return client_data.get('rates', {})

  def validate_config(self, config: InvoiceConfig) -> List[str]:
    """
    Validate configuration and return list of errors.

    Args:
      config: InvoiceConfig object to validate

    Returns:
      List of validation error messages
    """
    errors = []

    # Validate biller information
    if not config.biller_name:
      errors.append("Biller name is required")

    if config.biller_address:
      if not config.biller_address.street:
        errors.append("Biller street address is required")
      if not config.biller_address.city:
        errors.append("Biller city is required")
      if not config.biller_address.state:
        errors.append("Biller state is required")
      if not config.biller_address.zip_code:
        errors.append("Biller ZIP code is required")

    # Validate hourly rates
    if config.default_hourly_rate <= 0:
      errors.append("Default hourly rate must be greater than 0")

    # Validate clients
    for client_id, client_data in config.clients.items():
      if not client_data.get('name'):
        errors.append(f"Client '{client_id}' name is required")
      if not client_data.get('prefix'):
        errors.append(f"Client '{client_id}' prefix is required")

    return errors
