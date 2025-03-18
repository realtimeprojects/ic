"""
Command classes for IC.
Implements the command pattern for executing IC commands.
"""

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional
from .shell_executor import ShellExecutor
import argparse
import traceback
import signal

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class CommandBase(ABC):
    """Abstract base class for all commands."""
    
    def __init__(self, name: str, config: Dict[str, Any], env: Dict[str, str]):
        """
        Initialize command with its configuration.
        
        Args:
            name: Name of the command
            config: Command configuration dictionary
        """
        self.name = name
        self.config = config
        self.env = env
        self._help = config.get('help', 'No help available')
        signal.signal(signal.SIGINT, self.terminate)

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

    @abstractmethod
    def terminate(self, sig, frame):
        pass

class CommandGroup(CommandBase):
    """Command that executes a group of commands."""
    def __init__(self, name, config, env):
        super().__init__(name, config, env)

    def run(self, args) -> int:
        """
        Execute the group of commands.
        """
        __parser = argparse.ArgumentParser()
        # __parser.add_argument('--help', action='store_true', help='Show help')
        __parser.add_argument('command', help='Subcommand to execute')
        __parser.add_argument('args', nargs=argparse.REMAINDER, help='Command arguments')

        __args = __parser.parse_args(args.args)

        if not __args.command:
            self.help()
            return 1

        subcmd = CommandFactory(self.config, self.env).get(__args)
        if not subcmd:
            log.error(f"Unknown command: {__args.command}")
            self.help()
            return 1

        return subcmd.run(args)
    
    def help(self) -> str:
        """Return the help text for this command."""
        log.info("Available commands:")
        for cmd in self.config.get('commands', {}).keys():
            log.info(f"  {cmd}")

    def terminate(self, sig, frame):
        pass

class ShellCommand(CommandBase):
    """Command that executes a shell command."""
    def __init__(self, name: str, config: Dict[str, Any], env: Dict[str, str], prefer_os_env=False):
        super().__init__(name, config, env)
        self.executor = None
        self.prefer_os_env = prefer_os_env
    
    def run(self, args) -> int:
        """
        Execute the shell commands sequentially in a single shell environment.
        Aborts execution if any command fails.
        
        Returns:
            int: Return code (0 for success, non-zero for failure)
        """
        self.env.update(self.config.get('_env', {}))
        shell_cmd = self.config.get('shell')
        if not shell_cmd:
            raise ValueError(f"No shell command specified for command '{self.name}'")
        
        try:
            cmds = shell_cmd.splitlines()
            log.debug(f"Starting execution of {len(cmds)} shell commands")
            
            self.executor = ShellExecutor(args=args, env=self.env, prefer_os_env=self.prefer_os_env)
            
            # Execute each command sequentially
            for cmd in cmds:
                status = self.executor.execute_command(cmd)
                if status != 0:
                    log.error(f"Command failed with status {status}: {cmd}")
                    self.executor.cleanup()
                    return status
            
            self.executor.cleanup()
            return 0
            
        except Exception as e:
            log.error(f"Error executing command '{self.name}': {e}")
            # print stack trace
            traceback.print_exc() 
            return 1

    def terminate(self, sig, frame):
        self.executor.close()


class CommandFactory:
    """Factory class for creating command instances."""
    def __init__(self, config, env = {}):
        self.config = config
        self.env = env
        self.env.update(self.config.get("commands", {}).get("_env", {}))

    def get(self, args) -> Optional[CommandBase]:
        """
        Create and return a command instance based on the configuration.
        
        Args:
            name: Name of the command
            config: Command configuration dictionary
        
        Returns:
            CommandBase: Instance of appropriate command class, or None if invalid
        """
        # log.debug(f"Getting command '{args}' from config '{self.config}'")
        cmdconfig = self.config.get('commands', {}).get(args.command)
        if not cmdconfig:
            return None

        if 'commands' in cmdconfig:
            return CommandGroup(args.command, cmdconfig, self.env)

        if 'shell' in cmdconfig:
            return ShellCommand(args.command, cmdconfig, self.env, prefer_os_env=True)
        
        elif 'script' in cmdconfig:
            # Reserved for future implementation
            raise NotImplementedError("Script commands are not yet implemented")
        else:
            raise ValueError(f"Unknown command type in configuration for '{args.command}'") 
