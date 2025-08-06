"""
PDF compilation pipeline module.

Handles LaTeX to PDF compilation using external LaTeX distribution,
manages temporary files, and provides compilation status feedback.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class PDFCompiler:
  """Compiles LaTeX source code to PDF."""
  
  def __init__(self, latex_command: str = "pdflatex", 
               working_dir: Optional[str] = None):
    """
    Initialize the PDF compiler.
    
    Args:
      latex_command: LaTeX compiler command (pdflatex, xelatex, etc.)
      working_dir: Working directory for compilation
    """
    self.latex_command = latex_command
    self.working_dir = working_dir or tempfile.mkdtemp()
    self.temp_files = []
  
  def compile_latex(self, latex_content: str, output_path: str) -> Tuple[bool, str]:
    """
    Compile LaTeX content to PDF.
    
    Args:
      latex_content: LaTeX source code as string
      output_path: Path where PDF should be saved
    
    Returns:
      Tuple of (success: bool, message: str)
    """
    try:
      # Create temporary working directory
      temp_dir = tempfile.mkdtemp()
      self.temp_files.append(temp_dir)
      
      # Write LaTeX content to temporary file
      latex_file = os.path.join(temp_dir, "invoice.tex")
      with open(latex_file, 'w', encoding='utf-8') as f:
        f.write(latex_content)
      
      # Run LaTeX compilation
      success, message = self._run_latex_compilation(temp_dir, latex_file)
      
      if success:
        # Copy PDF to output location
        pdf_file = os.path.join(temp_dir, "invoice.pdf")
        if os.path.exists(pdf_file):
          shutil.copy2(pdf_file, output_path)
          return True, f"PDF successfully generated: {output_path}"
        else:
          return False, "PDF file not found after compilation"
      else:
        return False, message
    
    except Exception as e:
      return False, f"Compilation error: {str(e)}"
    
    finally:
      # Clean up temporary files
      self.cleanup()
  
  def _run_latex_compilation(self, temp_dir: str, latex_file: str) -> Tuple[bool, str]:
    """Run the actual LaTeX compilation process."""
    try:
      # First pass - generate PDF
      cmd = [
        self.latex_command,
        "-interaction=nonstopmode",
        "-output-directory=" + temp_dir,
        latex_file
      ]
      
      result = subprocess.run(
        cmd,
        cwd=temp_dir,
        capture_output=True,
        text=True,
        timeout=60  # 60 second timeout
      )
      
      # Check if PDF was created
      pdf_file = os.path.join(temp_dir, "invoice.pdf")
      if os.path.exists(pdf_file):
        return True, "Compilation successful"
      
      # If first pass failed, try second pass for references
      if result.returncode != 0:
        logger.warning(f"First LaTeX pass failed: {result.stderr}")
        
        # Second pass
        result2 = subprocess.run(
          cmd,
          cwd=temp_dir,
          capture_output=True,
          text=True,
          timeout=60
        )
        
        if os.path.exists(pdf_file):
          return True, "Compilation successful (second pass)"
        else:
          return False, f"LaTeX compilation failed: {result2.stderr}"
      
      return False, f"LaTeX compilation failed: {result.stderr}"
    
    except subprocess.TimeoutExpired:
      return False, "LaTeX compilation timed out"
    except FileNotFoundError:
      return False, f"LaTeX command '{self.latex_command}' not found. Please install a LaTeX distribution."
    except Exception as e:
      return False, f"Compilation error: {str(e)}"
  
  def cleanup(self) -> None:
    """Clean up temporary files."""
    for temp_dir in self.temp_files:
      try:
        if os.path.exists(temp_dir):
          shutil.rmtree(temp_dir)
      except Exception as e:
        logger.warning(f"Failed to clean up {temp_dir}: {e}")
    
    self.temp_files.clear()
  
  def __del__(self):
    """Cleanup on object destruction."""
    self.cleanup()


class LaTeXEnvironmentChecker:
  """Checks LaTeX environment and dependencies."""
  
  def __init__(self):
    self.required_packages = [
      "pdflatex",
      "xelatex"
    ]
  
  def check_latex_installation(self) -> Tuple[bool, List[str]]:
    """
    Check if LaTeX is properly installed.
    
    Returns:
      Tuple of (is_available: bool, available_commands: List[str])
    """
    available_commands = []
    
    for command in self.required_packages:
      if self._check_command_available(command):
        available_commands.append(command)
    
    return len(available_commands) > 0, available_commands
  
  def _check_command_available(self, command: str) -> bool:
    """Check if a command is available in PATH."""
    try:
      result = subprocess.run(
        [command, "--version"],
        capture_output=True,
        text=True,
        timeout=10
      )
      return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
      return False
  
  def get_installation_instructions(self) -> str:
    """Get installation instructions for LaTeX."""
    return """
LaTeX Installation Instructions:

macOS:
  - Install MacTeX: https://www.tug.org/mactex/
  - Or install BasicTeX: brew install --cask basictex

Ubuntu/Debian:
  - sudo apt-get install texlive-full
  - Or for minimal installation: sudo apt-get install texlive-latex-base

Windows:
  - Install MiKTeX: https://miktex.org/download
  - Or install TeX Live: https://www.tug.org/texlive/

After installation, ensure 'pdflatex' is available in your PATH.
"""


class CompilationError(Exception):
  """Exception raised when LaTeX compilation fails."""
  
  def __init__(self, message: str, latex_output: str = ""):
    self.message = message
    self.latex_output = latex_output
    super().__init__(self.message)


class PDFGenerator:
  """High-level PDF generation interface."""
  
  def __init__(self, latex_command: str = "pdflatex"):
    """
    Initialize the PDF generator.
    
    Args:
      latex_command: LaTeX compiler command to use
    """
    self.latex_command = latex_command
    self.compiler = PDFCompiler(latex_command)
    self.environment_checker = LaTeXEnvironmentChecker()
  
  def generate_pdf(self, latex_content: str, output_path: str) -> str:
    """
    Generate PDF from LaTeX content.
    
    Args:
      latex_content: LaTeX source code
      output_path: Output PDF file path
    
    Returns:
      Path to generated PDF file
    
    Raises:
      CompilationError: If compilation fails
    """
    # Check LaTeX environment
    is_available, available_commands = self.environment_checker.check_latex_installation()
    
    if not is_available:
      instructions = self.environment_checker.get_installation_instructions()
      raise CompilationError(
        f"No LaTeX installation found. Available commands: {available_commands}\n{instructions}"
      )
    
    # Compile LaTeX to PDF
    success, message = self.compiler.compile_latex(latex_content, output_path)
    
    if not success:
      raise CompilationError(message)
    
    return output_path
  
  def generate_pdf_from_file(self, latex_file: str, output_path: str) -> str:
    """
    Generate PDF from LaTeX file.
    
    Args:
      latex_file: Path to LaTeX source file
      output_path: Output PDF file path
    
    Returns:
      Path to generated PDF file
    """
    with open(latex_file, 'r', encoding='utf-8') as f:
      latex_content = f.read()
    
    return self.generate_pdf(latex_content, output_path)
  
  def cleanup(self) -> None:
    """Clean up temporary files."""
    self.compiler.cleanup()
  
  def __del__(self):
    """Cleanup on object destruction."""
    self.cleanup() 