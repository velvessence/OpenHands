"""
File Management Module for Desktop Automation.

Provides file operations:
- Read, write, copy, move, delete files
- List directories
- File search
"""

import os
import shutil
import glob
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class FileManagerConfig:
    """Configuration for file operations."""
    base_dir: str = "."
    create_dirs: bool = True


class FileManager:
    """
    File management operations.
    
    Usage:
        fm = FileManager("/path/to/workspace")
        fm.read_file("config.json")
        fm.write_file("output.txt", "Hello")
        fm.copy_file("src.txt", "dest.txt")
    """
    
    def __init__(self, config: Optional[FileManagerConfig] = None):
        self.config = config or FileManagerConfig()
        self.base_dir = Path(self.config.base_dir)
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to base_dir."""
        p = Path(path)
        if p.is_absolute():
            return p
        return self.base_dir / p
    
    def read_file(self, path: str, encoding: str = "utf-8") -> Optional[str]:
        """
        Read file contents.
        
        Args:
            path: File path
            encoding: File encoding
            
        Returns:
            File contents or None on error
        """
        try:
            p = self._resolve_path(path)
            return p.read_text(encoding=encoding)
        except Exception:
            return None
    
    def write_file(
        self, 
        path: str, 
        content: str, 
        encoding: str = "utf-8",
        append: bool = False
    ) -> bool:
        """
        Write content to file.
        
        Args:
            path: File path
            content: Content to write
            encoding: File encoding
            append: Whether to append or overwrite
            
        Returns:
            True if successful
        """
        try:
            p = self._resolve_path(path)
            if self.config.create_dirs:
                p.parent.mkdir(parents=True, exist_ok=True)
            
            mode = "a" if append else "w"
            with open(p, mode, encoding=encoding) as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    def copy_file(self, src: str, dest: str) -> bool:
        """
        Copy file.
        
        Args:
            src: Source path
            dest: Destination path
            
        Returns:
            True if successful
        """
        try:
            src_p = self._resolve_path(src)
            dest_p = self._resolve_path(dest)
            
            if self.config.create_dirs:
                dest_p.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src_p, dest_p)
            return True
        except Exception:
            return False
    
    def move_file(self, src: str, dest: str) -> bool:
        """
        Move/rename file.
        
        Args:
            src: Source path
            dest: Destination path
            
        Returns:
            True if successful
        """
        try:
            src_p = self._resolve_path(src)
            dest_p = self._resolve_path(dest)
            
            if self.config.create_dirs:
                dest_p.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_p), str(dest_p))
            return True
        except Exception:
            return False
    
    def delete_file(self, path: str) -> bool:
        """
        Delete file.
        
        Args:
            path: File path
            
        Returns:
            True if successful
        """
        try:
            p = self._resolve_path(path)
            p.unlink()
            return True
        except Exception:
            return False
    
    def list_dir(
        self, 
        path: str = ".", 
        pattern: Optional[str] = None,
        recursive: bool = False
    ) -> List[str]:
        """
        List directory contents.
        
        Args:
            path: Directory path
            pattern: Optional glob pattern
            recursive: Whether to list recursively
            
        Returns:
            List of file paths
        """
        try:
            p = self._resolve_path(path)
            
            if pattern:
                if recursive:
                    return [str(f) for f in p.rglob(pattern)]
                return [str(f) for f in p.glob(pattern)]
            
            if recursive:
                return [str(f) for f in p.rglob("*") if f.is_file()]
            
            return [str(f) for f in p.iterdir() if f.is_file()]
        except Exception:
            return []
    
    def list_dirs(self, path: str = ".", recursive: bool = False) -> List[str]:
        """
        List subdirectories.
        
        Args:
            path: Directory path
            recursive: Whether to list recursively
            
        Returns:
            List of directory paths
        """
        try:
            p = self._resolve_path(path)
            
            if recursive:
                return [str(f) for f in p.rglob("*") if f.is_dir()]
            
            return [str(f) for f in p.iterdir() if f.is_dir()]
        except Exception:
            return []
    
    def create_dir(self, path: str) -> bool:
        """
        Create directory.
        
        Args:
            path: Directory path
            
        Returns:
            True if successful
        """
        try:
            p = self._resolve_path(path)
            p.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
    
    def delete_dir(self, path: str, recursive: bool = False) -> bool:
        """
        Delete directory.
        
        Args:
            path: Directory path
            recursive: Whether to delete recursively
            
        Returns:
            True if successful
        """
        try:
            p = self._resolve_path(path)
            
            if recursive:
                shutil.rmtree(p)
            else:
                p.rmdir()
            return True
        except Exception:
            return False
    
    def exists(self, path: str) -> bool:
        """Check if path exists."""
        p = self._resolve_path(path)
        return p.exists()
    
    def is_file(self, path: str) -> bool:
        """Check if path is a file."""
        p = self._resolve_path(path)
        return p.is_file()
    
    def is_dir(self, path: str) -> bool:
        """Check if path is a directory."""
        p = self._resolve_path(path)
        return p.is_dir()
    
    def get_size(self, path: str) -> Optional[int]:
        """Get file size in bytes."""
        try:
            p = self._resolve_path(path)
            return p.stat().st_size
        except Exception:
            return None
    
    def get_info(self, path: str) -> Optional[Dict[str, Any]]:
        """Get file information."""
        try:
            p = self._resolve_path(path)
            stat = p.stat()
            return {
                "path": str(p),
                "size": stat.st_size,
                "is_file": p.is_file(),
                "is_dir": p.is_dir(),
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
            }
        except Exception:
            return None
    
    def search(self, pattern: str, path: str = ".") -> List[str]:
        """
        Search for files matching pattern.
        
        Args:
            pattern: Glob pattern
            path: Search directory
            
        Returns:
            List of matching paths
        """
        try:
            p = self._resolve_path(path)
            return [str(f) for f in p.rglob(pattern)]
        except Exception:
            return []
    
    def execute_action(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a file action.
        
        Args:
            action: Action name
            **kwargs: Action arguments
            
        Returns:
            Result dictionary
        """
        actions = {
            "read": lambda: self.read_file(kwargs.get("path", "")),
            "write": lambda: self.write_file(
                kwargs.get("path", ""),
                kwargs.get("content", "")
            ),
            "copy": lambda: self.copy_file(
                kwargs.get("src", ""),
                kwargs.get("dest", "")
            ),
            "move": lambda: self.move_file(
                kwargs.get("src", ""),
                kwargs.get("dest", "")
            ),
            "delete": lambda: self.delete_file(kwargs.get("path", "")),
            "list": lambda: self.list_dir(kwargs.get("path", ".")),
            "mkdir": lambda: self.create_dir(kwargs.get("path", "")),
            "rmdir": lambda: self.delete_dir(kwargs.get("path", "")),
            "exists": lambda: self.exists(kwargs.get("path", "")),
            "search": lambda: self.search(
                kwargs.get("pattern", ""),
                kwargs.get("path", ".")
            ),
        }
        
        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}"}
        
        try:
            result = actions[action]()
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def __repr__(self):
        return f"FileManager(base_dir={self.base_dir})"


if __name__ == "__main__":
    # Example usage
    fm = FileManager(".")
    print(f"Base dir: {fm.base_dir}")
    print(f"Files: {fm.list_dir('.')}")