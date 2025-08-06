"""
Timewarrior data parsing module.

Handles parsing of JSON/CSV output from timew export command,
extracting time intervals, tags, and project categorization.
"""

import json
import csv
from datetime import datetime
from typing import List, Dict, Optional, Union
from dataclasses import dataclass


@dataclass
class TimeEntry:
  """Represents a single time tracking entry from Timewarrior."""
  start: datetime
  end: Optional[datetime]
  tags: List[str]
  annotation: Optional[str]
  project: Optional[str]
  duration_seconds: Optional[int] = None


@dataclass
class BillableItem:
  """Represents a billable line item for an invoice."""
  description: str
  hours_worked: float
  hourly_rate: float
  amount: float
  project: str
  tags: List[str]


class TimewarriorParser:
  """Parses Timewarrior export data and converts to billable items."""
  
  def __init__(self):
    self.supported_formats = ['json', 'csv']
  
  def parse_export_data(self, data: str, format_type: str = 'json') -> List[TimeEntry]:
    """
    Parse Timewarrior export data into TimeEntry objects.
    
    Args:
      data: Raw export data from timew export command
      format_type: Format of the data ('json' or 'csv')
    
    Returns:
      List of TimeEntry objects
    """
    if format_type == 'json':
      return self._parse_json(data)
    elif format_type == 'csv':
      return self._parse_csv(data)
    else:
      raise ValueError(f"Unsupported format: {format_type}")
  
  def _parse_json(self, json_data: str) -> List[TimeEntry]:
    """Parse JSON format Timewarrior export data."""
    try:
      data = json.loads(json_data)
      entries = []
      
      for interval in data:
        start = datetime.fromisoformat(interval['start'].replace('Z', '+00:00'))
        end = None
        if interval.get('end'):
          end = datetime.fromisoformat(interval['end'].replace('Z', '+00:00'))
        
        tags = interval.get('tags', [])
        annotation = interval.get('annotation')
        
        # Extract project from tags or annotation
        project = self._extract_project(tags, annotation)
        
        entry = TimeEntry(
          start=start,
          end=end,
          tags=tags,
          annotation=annotation,
          project=project
        )
        entries.append(entry)
      
      return entries
    except json.JSONDecodeError as e:
      raise ValueError(f"Invalid JSON data: {e}")
  
  def _parse_csv(self, csv_data: str) -> List[TimeEntry]:
    """Parse CSV format Timewarrior export data."""
    entries = []
    reader = csv.DictReader(csv_data.splitlines())
    
    for row in reader:
      start = datetime.fromisoformat(row['start'].replace('Z', '+00:00'))
      end = None
      if row.get('end'):
        end = datetime.fromisoformat(row['end'].replace('Z', '+00:00'))
      
      tags = row.get('tags', '').split(',') if row.get('tags') else []
      tags = [tag.strip() for tag in tags if tag.strip()]
      
      annotation = row.get('annotation')
      project = self._extract_project(tags, annotation)
      
      entry = TimeEntry(
        start=start,
        end=end,
        tags=tags,
        annotation=annotation,
        project=project
      )
      entries.append(entry)
    
    return entries
  
  def _extract_project(self, tags: List[str], annotation: Optional[str]) -> Optional[str]:
    """Extract project name from tags or annotation."""
    # Look for project tag (common patterns)
    project_tags = [tag for tag in tags if tag.startswith('project:')]
    if project_tags:
      return project_tags[0].replace('project:', '')
    
    # Look for client tags
    client_tags = [tag for tag in tags if tag.startswith('client:')]
    if client_tags:
      return client_tags[0].replace('client:', '')
    
    # Use first tag as project if no specific project/client tag
    if tags:
      return tags[0]
    
    return None
  
  def group_by_project(self, entries: List[TimeEntry]) -> Dict[str, List[TimeEntry]]:
    """
    Group time entries by project.
    
    Args:
      entries: List of TimeEntry objects
    
    Returns:
      Dictionary mapping project names to lists of entries
    """
    grouped = {}
    
    for entry in entries:
      project = entry.project or 'unknown'
      if project not in grouped:
        grouped[project] = []
      grouped[project].append(entry)
    
    return grouped
  
  def calculate_billable_hours(self, entries: List[TimeEntry]) -> float:
    """
    Calculate total billable hours from time entries.
    
    Args:
      entries: List of TimeEntry objects
    
    Returns:
      Total billable hours as float
    """
    total_seconds = 0
    
    for entry in entries:
      if entry.end:
        duration = (entry.end - entry.start).total_seconds()
        total_seconds += duration
      elif entry.duration_seconds:
        total_seconds += entry.duration_seconds
    
    return total_seconds / 3600.0  # Convert to hours
  
  def apply_hourly_rates(self, entries: List[TimeEntry], 
                        config_manager) -> List[BillableItem]:
    """
    Apply hourly rates to time entries and create billable items.
    
    Args:
      entries: List of TimeEntry objects
      config_manager: ConfigManager instance for rate lookup
    
    Returns:
      List of BillableItem objects
    """
    billable_items = []
    
    # Group by project first
    grouped_entries = self.group_by_project(entries)
    
    for project, project_entries in grouped_entries.items():
      # Group entries by their primary task tag for more granular rate application
      task_groups = self._group_by_primary_task(project_entries)
      
      for task, task_entries in task_groups.items():
        # Find applicable rate for this specific task using config manager
        rate = config_manager.get_client_task_rate(project, task)
        
        # Calculate hours for this task
        hours = self.calculate_billable_hours(task_entries)
        
        # Create description from tags and annotations
        description = self._create_description(task_entries)
        
        # Create billable item
        item = BillableItem(
          description=description,
          hours_worked=hours,
          hourly_rate=rate,
          amount=hours * rate,
          project=project,
          tags=self._get_unique_tags(task_entries)
        )
        billable_items.append(item)
    
    return billable_items
  
  def _group_by_primary_task(self, entries: List[TimeEntry]) -> Dict[str, List[TimeEntry]]:
    """
    Group entries by their primary task tag for more granular rate application.
    
    This allows different rates for different tasks within the same project.
    """
    task_groups = {}
    
    for entry in entries:
      # Find the primary task tag (first non-project/client tag)
      primary_task = self._find_primary_task_tag(entry.tags)
      
      if primary_task not in task_groups:
        task_groups[primary_task] = []
      task_groups[primary_task].append(entry)
    
    return task_groups
  
  def _find_primary_task_tag(self, tags: List[str]) -> str:
    """
    Find the primary task tag from a list of tags.
    
    Returns the first tag that's not a project/client identifier.
    """
    # Filter out project/client tags and find the first task tag
    task_tags = [tag for tag in tags if not tag.startswith(('project:', 'client:'))]
    
    # Remove known client names from task tags
    known_clients = ['madrona', 'goodhertz', 'uhe']
    task_tags = [tag for tag in task_tags if tag not in known_clients]
    
    if task_tags:
      return task_tags[0]
    
    # If no task tag found, use a default
    return "general"
  
  def _create_description(self, entries: List[TimeEntry]) -> str:
    """Create a description from tags and annotations."""
    descriptions = []
    
    for entry in entries:
      if entry.annotation:
        descriptions.append(entry.annotation)
      elif entry.tags:
        # Use tags as description, excluding project/client tags
        tag_descriptions = [tag for tag in entry.tags 
                          if not tag.startswith(('project:', 'client:'))]
        if tag_descriptions:
          descriptions.append(', '.join(tag_descriptions))
    
    if descriptions:
      return '; '.join(set(descriptions))  # Remove duplicates
    else:
      return "Time tracking"
  
  def _get_unique_tags(self, entries: List[TimeEntry]) -> List[str]:
    """Get unique tags from a list of entries."""
    all_tags = []
    for entry in entries:
      all_tags.extend(entry.tags)
    return list(set(all_tags)) 