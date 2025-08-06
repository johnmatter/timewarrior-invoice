"""
Tests for Timewarrior data parser module.
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import Mock
from src.parser import TimewarriorParser, TimeEntry, BillableItem


class TestTimewarriorParser(unittest.TestCase):
  """Test cases for TimewarriorParser class."""
  
  def setUp(self):
    """Set up test fixtures."""
    self.parser = TimewarriorParser()
    
    # Sample JSON data from timew export
    self.sample_json = '''[
      {
        "start": "2024-01-15T09:00:00Z",
        "end": "2024-01-15T12:00:00Z",
        "tags": ["madrona", "development", "bugfix"],
        "annotation": "Fixed audio processing bug"
      },
      {
        "start": "2024-01-15T13:00:00Z",
        "end": "2024-01-15T17:00:00Z",
        "tags": ["madrona", "testing"],
        "annotation": "Unit tests for new feature"
      }
    ]'''
  
  def test_parse_json_data(self):
    """Test parsing JSON format Timewarrior data."""
    entries = self.parser.parse_export_data(self.sample_json, 'json')
    
    self.assertEqual(len(entries), 2)
    
    # Check first entry
    first_entry = entries[0]
    # Handle timezone-aware datetime comparison
    expected_start = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    self.assertEqual(first_entry.start, expected_start)
    expected_end = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    self.assertEqual(first_entry.end, expected_end)
    self.assertEqual(first_entry.tags, ["madrona", "development", "bugfix"])
    self.assertEqual(first_entry.annotation, "Fixed audio processing bug")
    self.assertEqual(first_entry.project, "madrona")
  
  def test_extract_project(self):
    """Test project extraction from tags."""
    # Test with project tag
    tags = ["project:madrona", "development"]
    project = self.parser._extract_project(tags, None)
    self.assertEqual(project, "madrona")
    
    # Test with client tag
    tags = ["client:goodhertz", "consulting"]
    project = self.parser._extract_project(tags, None)
    self.assertEqual(project, "goodhertz")
    
    # Test with first tag as project
    tags = ["madrona", "development"]
    project = self.parser._extract_project(tags, None)
    self.assertEqual(project, "madrona")
    
    # Test with no tags
    project = self.parser._extract_project([], None)
    self.assertIsNone(project)
  
  def test_group_by_project(self):
    """Test grouping entries by project."""
    entries = self.parser.parse_export_data(self.sample_json, 'json')
    grouped = self.parser.group_by_project(entries)
    
    self.assertIn("madrona", grouped)
    self.assertEqual(len(grouped["madrona"]), 2)
  
  def test_calculate_billable_hours(self):
    """Test billable hours calculation."""
    entries = self.parser.parse_export_data(self.sample_json, 'json')
    hours = self.parser.calculate_billable_hours(entries)
    
    # 3 hours + 4 hours = 7 hours
    self.assertEqual(hours, 7.0)
  
  def test_apply_hourly_rates(self):
    """Test applying hourly rates to entries."""
    entries = self.parser.parse_export_data(self.sample_json, 'json')
    
    # Create mock config manager
    mock_config = Mock()
    mock_config.get_client_task_rate.return_value = 150.0
    
    billable_items = self.parser.apply_hourly_rates(entries, mock_config)
    
    # Now we get 2 items: one for development, one for testing
    self.assertEqual(len(billable_items), 2)
    
    # Check total hours and amounts
    total_hours = sum(item.hours_worked for item in billable_items)
    total_amount = sum(item.amount for item in billable_items)
    self.assertEqual(total_hours, 7.0)
    self.assertEqual(total_amount, 1050.0)  # 7 hours * 150.0
    
    # Verify config manager was called correctly
    mock_config.get_client_task_rate.assert_called()
  
  def test_per_task_rates(self):
    """Test per-task rate application."""
    # Create entries with different tasks
    sample_data = '''[
      {
        "start": "2024-01-15T09:00:00Z",
        "end": "2024-01-15T12:00:00Z",
        "tags": ["madrona", "development"],
        "annotation": "Development work"
      },
      {
        "start": "2024-01-15T13:00:00Z",
        "end": "2024-01-15T17:00:00Z",
        "tags": ["madrona", "consulting"],
        "annotation": "Consulting work"
      }
    ]'''
    
    entries = self.parser.parse_export_data(sample_data, 'json')
    
    # Create mock config manager that returns different rates for different tasks
    mock_config = Mock()
    def mock_get_rate(client, task):
      if task == "development":
        return 140.0
      elif task == "consulting":
        return 200.0
      else:
        return 150.0
    
    mock_config.get_client_task_rate.side_effect = mock_get_rate
    
    billable_items = self.parser.apply_hourly_rates(entries, mock_config)
    
    # Should have two separate billable items (one per task)
    self.assertEqual(len(billable_items), 2)
    
    # Development item
    dev_item = next(item for item in billable_items if "development" in item.tags)
    self.assertEqual(dev_item.hours_worked, 3.0)
    self.assertEqual(dev_item.hourly_rate, 140.0)  # Uses development rate
    self.assertEqual(dev_item.amount, 420.0)
    
    # Consulting item
    consulting_item = next(item for item in billable_items if "consulting" in item.tags)
    self.assertEqual(consulting_item.hours_worked, 4.0)
    self.assertEqual(consulting_item.hourly_rate, 200.0)  # Uses consulting rate
    self.assertEqual(consulting_item.amount, 800.0)
  
  def test_client_specific_task_rates(self):
    """Test client-specific task rate application."""
    sample_data = '''[
      {
        "start": "2024-01-15T09:00:00Z",
        "end": "2024-01-15T12:00:00Z",
        "tags": ["madrona", "consulting"],
        "annotation": "Premium consulting"
      }
    ]'''
    
    entries = self.parser.parse_export_data(sample_data, 'json')
    
    # Create mock config manager
    mock_config = Mock()
    mock_config.get_client_task_rate.return_value = 225.0
    
    billable_items = self.parser.apply_hourly_rates(entries, mock_config)
    
    self.assertEqual(len(billable_items), 1)
    self.assertEqual(billable_items[0].hourly_rate, 225.0)  # Uses madrona consulting rate
    self.assertEqual(billable_items[0].amount, 675.0)  # 3 hours * 225.0
  
  def test_rate_precedence(self):
    """Test rate precedence using config manager."""
    sample_data = '''[
      {
        "start": "2024-01-15T09:00:00Z",
        "end": "2024-01-15T10:00:00Z",
        "tags": ["goodhertz", "documentation"],
        "annotation": "Documentation work"
      }
    ]'''
    
    entries = self.parser.parse_export_data(sample_data, 'json')
    
    # Create mock config manager that simulates the precedence logic
    mock_config = Mock()
    mock_config.get_client_task_rate.return_value = 140.0  # Goodhertz documentation rate
    
    billable_items = self.parser.apply_hourly_rates(entries, mock_config)
    
    self.assertEqual(billable_items[0].hourly_rate, 140.0)
  
  def test_invalid_json(self):
    """Test handling of invalid JSON data."""
    with self.assertRaises(ValueError):
      self.parser.parse_export_data("invalid json", 'json')
  
  def test_unsupported_format(self):
    """Test handling of unsupported format."""
    with self.assertRaises(ValueError):
      self.parser.parse_export_data("data", 'xml')


class TestTimeEntry(unittest.TestCase):
  """Test cases for TimeEntry dataclass."""
  
  def test_time_entry_creation(self):
    """Test TimeEntry object creation."""
    start = datetime(2024, 1, 15, 9, 0, 0)
    end = datetime(2024, 1, 15, 12, 0, 0)
    tags = ["madrona", "development"]
    
    entry = TimeEntry(
      start=start,
      end=end,
      tags=tags,
      annotation="Test annotation",
      project="madrona"
    )
    
    self.assertEqual(entry.start, start)
    self.assertEqual(entry.end, end)
    self.assertEqual(entry.tags, tags)
    self.assertEqual(entry.annotation, "Test annotation")
    self.assertEqual(entry.project, "madrona")


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


if __name__ == '__main__':
  unittest.main() 