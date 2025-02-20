import argparse
import sys
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

class CommandLineInterface:
    def __init__(self):
        self.config = {}
        self.parser = self._create_parser()
        self._load_default_config()

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description='IC Command Line Interface')
        parser.add_argument('command', nargs='?', help='Command to execute')
        parser.add_argument('args', nargs=argparse.REMAINDER, help='Command arguments')
        parser.add_argument('-help', action='store_true', help='Display help')
        parser.add_argument('-version', action='store_true', help='Display version')
        parser.add_argument('-list-commands', action='store_true', help='List available commands')
        return parser

    def _load_default_config(self) -> None:
        default_config_path = Path(__file__).parent / 'data' / 'default.yml'
        try:
            with open(default_config_path) as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            sys.exit('Error: Default configuration file not found')
        except yaml.YAMLError:
            sys.exit('Error: Invalid YAML in default configuration')

    def list_commands(self) -> None:
        print("Available commands:")
        for cmd, details in self.config.get('commands', {}).items():
            print(f"  {cmd}: {details.get('help', 'No description available')}")

    def show_version(self) -> None:
        # You'll want to import this from your package metadata
        print("ic version 0.1.0")

    def execute(self, args: Optional[list] = None) -> int:
        if args is None:
            args = sys.argv[1:]

        parsed_args = self.parser.parse_args(args)

        if parsed_args.version:
            self.show_version()
            return 0

        if parsed_args.list_commands or parsed_args.help or not parsed_args.command:
            self.list_commands()
            return 0

        if parsed_args.command not in self.config.get('commands', {}):
            print(f"Unknown command: {parsed_args.command}")
            self.list_commands()
            return 2

        # Here you would implement actual command execution
        # For now, we'll just print the command that would be executed
        command_config = self.config['commands'][parsed_args.command]
        print(f"Would execute: {command_config['shell']}")
        return 0

def main():
    cli = CommandLineInterface()
    sys.exit(cli.execute())

if __name__ == '__main__':
    main() 