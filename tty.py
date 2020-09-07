"""Terminal utilities."""

# Author: Steen Lumholt.

# Additions by Soumendra Ganguly.

from termios import *
from fcntl import ioctl
import os

__all__ = ["mode_echo", "mode_raw", "setraw", "setcbreak", "login"]

STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2

# Indices for termios list.
IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6

def mode_echo(mode, echo=True):
    """Set/unset ECHO."""
    if echo:
        mode[LFLAG] |= ECHO
    else:
        mode[LFLAG] &= ~ECHO

def mode_raw(mode):
    """Raw mode termios."""
    mode[IFLAG] &= ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON)
    mode[OFLAG] &= ~(OPOST)
    mode[CFLAG] &= ~(CSIZE | PARENB)
    mode[CFLAG] |= CS8
    mode[LFLAG] &= ~(ECHO | ICANON | IEXTEN | ISIG)
    mode[CC][VMIN] = 1
    mode[CC][VTIME] = 0

def setraw(fd, when=TCSAFLUSH):
    """Put terminal into a raw mode.
    Returns original termios."""
    mode = tcgetattr(fd)
    new = list(mode)
    mode_raw(new)
    tcsetattr(fd, when, new)
    return mode

def setcbreak(fd, when=TCSAFLUSH):
    """Put terminal into a cbreak mode."""
    mode = tcgetattr(fd)
    new = list(mode)
    new[LFLAG] &= ~(ECHO | ICANON)
    new[CC][VMIN] = 1
    new[CC][VTIME] = 0
    tcsetattr(fd, when, new)
    return mode

def login(fd):
    """Makes the calling process a session leader; if fd is a
    descriptor of a tty, then that tty becomes the stdin, stdout,
    stderr, and controlling tty of the calling process. Closes fd."""
    # Establish a new session.
    os.setsid()

    # The tty becomes stdin/stdout/stderr.
    os.dup2(fd, STDIN_FILENO)
    os.dup2(fd, STDOUT_FILENO)
    os.dup2(fd, STDERR_FILENO)
    if (fd > STDERR_FILENO):
        os.close(fd)

    # The tty becomes the controlling terminal.
    try:
        ioctl(STDOUT_FILENO, TIOCSCTTY)
    except (NameError, OSError):
        tmp_fd = os.open(os.ttyname(STDOUT_FILENO), os.O_RDWR)
        os.close(tmp_fd)
