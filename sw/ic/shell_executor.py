"""
Shell execution functionality for IC.
Provides a class for executing shell commands in a persistent shell environment.
"""

import subprocess
import logging
import sys
import threading
import queue
import os
import shlex
import re
import time

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class OutputReader:
    """Handles reading output from a pipe in a background thread."""
    
    def __init__(self, pipe, is_stderr=False):
        """
        Initialize the output reader.
        
        Args:
            pipe: The pipe to read from (stdout or stderr)
            is_stderr: Whether this reader is for stderr
        """
        self.pipe = pipe
        self.is_stderr = is_stderr
        self.queue = queue.Queue()
        self.thread = threading.Thread(
            target=self._reader_thread,
            daemon=True
        )
        self.thread.start()
    
    def _reader_thread(self):
        """Background thread to read from a pipe and put lines into a queue."""
        try:
            while True:
                line = self.pipe.readline()
                if not line:
                    break
                self.queue.put(line)
        except Exception as e:
            log.error(f"Reader thread error: {e}")
        #        finally:
        # self.queue.put(None)  # Signal EOF
    
    def get_line(self, timeout=0.1):
        """Get a line from the queue, returns None on timeout."""
        try:
            return self.queue.get(timeout=0.001)
        except queue.Empty:
            return None

def _replace(value, env):
    def _substitude(match):
        _match = match.group()[1:]
        if _match in env:
            _match = env[_match]

        return _match

    return re.sub(r"\$\w+", _substitude, value)

def _bash_cmd():
    if sys.platform == 'win32':
        return os.environ.get('BASH_PATH', 'c:\\msys64\\usr\\bin\\bash.exe')
    else:
        return os.environ.get('BASH_PATH', '/bin/bash')

class ShellExecutor:
    """Handles execution of shell commands in a single shell environment."""
    _modes = {
            'cmd':   { 'cmd': "cmd.exe",   'fmt': "echo CMD_STATUS: %error_level%\n"},
            'bash':  { 'cmd': _bash_cmd(), 'fmt': f"__status=$?; echo CMD_STATUS: $__status\n" },
    }
    
    def __init__(self, args=None, env={}, mode="bash", prefer_os_env=False):
        """
        Initialize the shell executor with a new shell process.
        
        Args:
            args: List of command line arguments to make available to shell scripts
        """
        self._mode = mode

        # Initialize environment with argument variables
        self.env = os.environ.copy()

        for name, value in env.items():
            if name in self.env:
                if prefer_os_env:
                    log.warning(f"ignoring {name} (already set to {self.env[name]})")
                    continue
            self.env[name] = _replace(value, self.env)

        log.error(f"GPR_PROJECT_PATH_FILE={self.env.get('GPR_PROJECT_PATH_FILE', None)}")
        if args:
            # Set individual argument variables (opt_1 through opt_5)
            for i, arg in enumerate(args.args, 1):
                self.env[f'opt_{i}'] = arg
            
            # Set all arguments as space-separated string
            self.env['options'] = ' '.join(shlex.quote(arg) for arg in args.args)
        
        self.process = subprocess.Popen(
            ShellExecutor._modes[self._mode]['cmd'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            env=self.env
        )
        # Create output readers
        self.stdout_reader = OutputReader(self.process.stdout, is_stderr=False)
        self.stderr_reader = OutputReader(self.process.stderr, is_stderr=True)

    def input(self, data):
        self.process.stdin.write(data)
        self.process.stdin.flush()


    def readline(self):
        line = self.stdout_reader.get_line()
        if not line:
            return None
        line = line.strip()
        if not line:
            return None

        log.info(f"{line}")
        if "CMD_STATUS:" in line:
            return int(line.split()[1])
        return line


    def execute_command(self, cmd: str) -> int:
        """
        Execute a single command and return its status code.
        Logs command output using the logger.
        
        Args:
            cmd: Shell command to execute
            
        Returns:
            int: Status code of the command
        """
        if not cmd.strip():
            return 0
            
        log.debug(f"> {cmd}")
        # Execute command and store its status in a variable
        self.input(cmd + "\n")
        self.input(ShellExecutor._modes[self._mode]['fmt'] + "\n")
        
        # Read and process output until we get the status code
        status_line = None
        while True:
            # Process stderr
            line = self.stderr_reader.get_line()
            if line and line.rstrip():
                log.warning(f"!! {line.rstrip()}")
                
            # Process stdout
            line = self.readline()
            if isinstance(line, int):
                return line

    def cleanup(self):
        """Clean up the shell process."""
        self.process.stdin.close()
        self.process.terminate() 
