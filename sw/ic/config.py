"""
Configuration management for IC.
Handles loading and merging of YAML configuration files.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """Manages IC configuration loading and merging."""

    def __init__(self):
        self.default_config = self._get_default_config_path()
        self.project_config = Path('.ic.yml')
        self.user_global_config = Path(os.path.expanduser('~/.config/ic/ic.yml'))
        self.user_home_config = Path(os.path.expanduser('~/.ic.yml'))

    def _get_default_config_path(self) -> Path:
        """Get path to default configuration installed with package."""
        package_dir = Path(__file__).parent
        return package_dir / 'data' / 'default.yml'

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file if it exists, return empty dict if not."""
        try:
            if path.exists():
                with open(path, 'r') as f:
                    return yaml.safe_load(f) or {}
        except (yaml.YAMLError, OSError) as e:
            print(f"Warning: Error loading {path}: {e}")
        return {}

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configurations, with override taking precedence."""
        result = base.copy()
        
        if 'commands' in override:
            if 'commands' not in result:
                result['commands'] = {}
            result['commands'].update(override['commands'])

        return result

    def get(self) -> Dict[str, Any]:
        """
        Load and merge all configuration files in the correct sequence.
        Later files override earlier ones.
        """
        # Start with default config (required)
        if not self.default_config.exists():
            raise FileNotFoundError(f"Default configuration not found at {self.default_config}")
        
        config = self._load_yaml(self.default_config)

        # Load and merge optional configs in sequence
        optional_configs = [
            self.project_config,
            self.user_global_config,
            self.user_home_config
        ]

        for config_path in optional_configs:
            next_config = self._load_yaml(config_path)
            config = self._merge_configs(config, next_config)

        return config 