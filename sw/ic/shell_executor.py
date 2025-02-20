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
        finally:
            self.queue.put(None)  # Signal EOF
    
    def get_line(self, timeout=0.1):
        """Get a line from the queue, returns None on timeout."""
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None

class ShellExecutor:
    """Handles execution of shell commands in a single shell environment."""
    
    def __init__(self, args=None):
        """
        Initialize the shell executor with a new shell process.
        
        Args:
            args: List of command line arguments to make available to shell scripts
        """
        # Initialize environment with argument variables
        self.env = os.environ.copy()
        if args:
            # Set individual argument variables (opt_1 through opt_5)
            for i, arg in enumerate(args[:5], 1):
                self.env[f'opt_{i}'] = arg
            
            # Set all arguments as space-separated string
            self.env['options'] = ' '.join(shlex.quote(arg) for arg in args)
        
        self.process = subprocess.Popen(
            '/bin/bash',
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
            
        log.info(f"Executing: {cmd}")
        # Execute command and store its status in a variable
        self.process.stdin.write(f"{cmd}; __status=$?; echo $__status\n")
        self.process.stdin.flush()
        
        # Read and process output until we get the status code
        status_line = None
        while status_line is None:
            # Process stdout
            line = self.stdout_reader.get_line()
            if line is not None:
                line = line.rstrip()
                if line.isdigit():
                    status_line = line
                else:
                    log.info(f"{line}")
            
            # Process stderr
            line = self.stderr_reader.get_line()
            if line is not None:
                log.warning(f"!! {line.rstrip()}")
                
        return int(status_line) if status_line is not None else 1

    def cleanup(self):
        """Clean up the shell process."""
        self.process.stdin.close()
        self.process.terminate() 