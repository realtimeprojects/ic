import argparse
import sys
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from .commands import CommandFactory

logging.basicConfig(level=logging.INFO,  format='%(message)s')

class CommandLineInterface:
    def __init__(self):
        self.config = {}
        self.parser = self._create_parser()
        self._load_configurations()

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description='IC Command Line Interface')
        parser.add_argument('command', nargs='?', help='Command to execute')
        parser.add_argument('args', nargs=argparse.REMAINDER, help='Command arguments')
        parser.add_argument('-help', action='store_true', help='Display help')
        parser.add_argument('-version', action='store_true', help='Display version')
        parser.add_argument('-list-commands', action='store_true', help='List available commands')
        return parser

    def _load_configurations(self) -> None:
        """Load configurations in the specified order:
        1. Default configuration (installed with package)
        2. Project configuration (./.ic.yml)
        3. User global configuration (~/.config/ic/ic.yml)
        4. User home configuration (~/.ic.yml)
        """
        # Load default config (required)
        self._load_default_config()
        
        # Load optional configs
        self._load_project_config()
        self._load_user_global_config()
        self._load_user_home_config()

    def _load_default_config(self) -> None:
        default_config_path = Path(__file__).parent / 'data' / 'default.yml'
        try:
            with open(default_config_path) as f:
                self.config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            sys.exit('Error: Default configuration file not found')
        except yaml.YAMLError:
            sys.exit('Error: Invalid YAML in default configuration')

    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """Merge new configuration with existing, giving precedence to new config"""
        if not new_config:
            return
        for key, value in new_config.items():
            if isinstance(value, dict) and key in self.config and isinstance(self.config[key], dict):
                self.config[key].update(value)
            else:
                self.config[key] = value

    def _load_yaml_file(self, path: Path) -> Dict[str, Any]:
        """Safely load a YAML file, returning empty dict if file doesn't exist"""
        try:
            with open(path) as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}
        except yaml.YAMLError:
            print(f"Warning: Invalid YAML in {path}")
            return {}

    def _load_project_config(self) -> None:
        """Load project-specific configuration from ./.ic.yml"""
        config = self._load_yaml_file(Path('.ic.yml'))
        self._merge_config(config)

    def _load_user_global_config(self) -> None:
        """Load user global configuration from ~/.config/ic/ic.yml"""
        config_path = Path.home() / '.config' / 'ic' / 'ic.yml'
        config = self._load_yaml_file(config_path)
        self._merge_config(config)

    def _load_user_home_config(self) -> None:
        """Load user home configuration from ~/.ic.yml"""
        config_path = Path.home() / '.ic.yml'
        config = self._load_yaml_file(config_path)
        self._merge_config(config)

    def list_commands(self) -> None:
        print("Available commands:")
        for cmd, details in self.config.get('commands', {}).items():
            print(f"  {cmd}: {details.get('help', 'No description available')}")

    def show_version(self) -> None:
        # You'll want to import this from your package metadata
        print("ic version 0.1.0")

    def execute(self, args = None) -> int:
        
        __cmd_factory = CommandFactory(self.config)
        
        if args is None:
            args = sys.argv[1:]

        args = self.parser.parse_args(args)
        logging.info(f"Executing command: {args}")

        if args.version:
            self.show_version()
            return 0

        if args.list_commands or args.help or not args.command:
            self.list_commands()
            return 0

        cmd = __cmd_factory.get(args)
        if not cmd:
            print(f"Unknown command: {args.command}")
            self.list_commands()
            return 2

        return cmd.run(args)

def main():
    cli = CommandLineInterface()
    sys.exit(cli.execute())

if __name__ == '__main__':
    main() 
