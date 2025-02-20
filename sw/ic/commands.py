"""
Command classes for IC.
Implements the command pattern for executing IC commands.
"""

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional
from .shell_executor import ShellExecutor

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class CommandBase(ABC):
    """Abstract base class for all commands."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize command with its configuration.
        
        Args:
            name: Name of the command
            config: Command configuration dictionary
        """
        self.name = name
        self.config = config
        self._help = config.get('help', 'No help available')

    def help(self) -> str:
        """Return the help text for this command."""
        return self._help

    @abstractmethod
    def run(self) -> int:
        """
        Execute the command.
        
        Returns:
            int: Return code (0 for success, non-zero for failure)
        """
        pass


class ShellCommand(CommandBase):
    """Command that executes a shell command."""
    
    def run(self) -> int:
        """
        Execute the shell commands sequentially in a single shell environment.
        Aborts execution if any command fails.
        
        Returns:
            int: Return code (0 for success, non-zero for failure)
        """
        shell_cmd = self.config.get('shell')
        if not shell_cmd:
            raise ValueError(f"No shell command specified for command '{self.name}'")
        
        try:
            cmds = shell_cmd.splitlines()
            log.info(f"Starting execution of {len(cmds)} shell commands")
            
            executor = ShellExecutor()
            
            # Execute each command sequentially
            for cmd in cmds:
                status = executor.execute_command(cmd)
                if status != 0:
                    log.error(f"Command failed with status {status}: {cmd}")
                    executor.cleanup()
                    return status
            
            executor.cleanup()
            return 0
            
        except Exception as e:
            log.error(f"Error executing command '{self.name}': {e}")
            return 1


class CommandFactory:
    """Factory class for creating command instances."""
    
    @staticmethod
    def get(name: str, config: Dict[str, Any]) -> Optional[CommandBase]:
        """
        Create and return a command instance based on the configuration.
        
        Args:
            name: Name of the command
            config: Command configuration dictionary
        
        Returns:
            CommandBase: Instance of appropriate command class, or None if invalid
        """
        if 'shell' in config:
            return ShellCommand(name, config)
        elif 'script' in config:
            # Reserved for future implementation
            raise NotImplementedError("Script commands are not yet implemented")
        else:
            raise ValueError(f"Unknown command type in configuration for '{name}'") 