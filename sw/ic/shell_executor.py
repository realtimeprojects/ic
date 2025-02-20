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

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class OutputReader:
    """Handles reading output from a pipe in a background thread."""
    
    def __init__(self, pipe, stream=None):
        """
        Initialize the output reader.
        
        Args:
            pipe: The pipe to read from (stdout or stderr)
            stream: Optional output stream to write to (sys.stdout or sys.stderr)
        """
        self.pipe = pipe
        self.stream = stream
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
                if self.stream:
                    self.stream.write(line)
                    self.stream.flush()
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
    
    def __init__(self):
        """Initialize the shell executor with a new shell process."""
        self.process = subprocess.Popen(
            '/bin/bash',
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        # Create output readers
        self.stdout_reader = OutputReader(self.process.stdout, sys.stdout)
        self.stderr_reader = OutputReader(self.process.stderr, sys.stderr)

    def execute_command(self, cmd: str) -> int:
        """
        Execute a single command and return its status code.
        Prints command output in real-time.
        
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
            if line is None:
                continue
            if line.rstrip().isdigit():
                status_line = line.rstrip()
                break
                
        return int(status_line) if status_line is not None else 1

    def cleanup(self):
        """Clean up the shell process."""
        self.process.stdin.close()
        self.process.terminate() 