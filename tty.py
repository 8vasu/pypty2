"""Terminal utilities."""

# Author: Steen Lumholt

# v2.0: Soumendra Ganguly <soumendra@tamu.edu>

from termios import *
from fcntl import ioctl
from struct import pack, unpack
import os

__all__ = ["mkecho", "mkraw", "mkcbreak", "setraw", "setcbreak", "login_tty", "HAVE_WINSZ", "winsize"]

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

def mkecho(mode, echo=True):
    """Set/unset ECHO."""
    if echo:
        mode[LFLAG] |= ECHO
    else:
        mode[LFLAG] &= ~ECHO

def mkraw(mode):
    """raw mode termios"""
    # Clear all POSIX.1-2017 input mode flags.
    mode[IFLAG] &= ~(IGNBRK | BRKINT | IGNPAR | PARMRK | INPCK | ISTRIP |
                     INLCR | IGNCR | ICRNL | IXON | IXANY | IXOFF)

    # Do not post-process output.
    mode[OFLAG] &= ~(OPOST)

    # Disable parity generation and detection; clear character size mask;
    # let character size be 8 bits.
    mode[CFLAG] &= ~(PARENB | CSIZE)
    mode[CFLAG] |= CS8

    # Do not echo characters (including NL); disable canonical input; disable
    # the checking of characters against the special control characters INTR,
    # QUIT, and SUSP (disable sending of signals using control characters);
    # disable any implementation-defined special control characters not
    # currently controlled by ICANON, ISIG, IXON, or IXOFF.
    mode[LFLAG] &= ~(ECHO | ECHONL | ICANON | ISIG | IEXTEN)

    # POSIX.1-2017, 11.1.7 Non-Canonical Mode Input Processing,
    # Case B: MIN>0, TIME=0
    # A pending read shall block until MIN (here 1) bytes are received,
    # or a signal is received.
    mode[CC][VMIN] = 1
    mode[CC][VTIME] = 0

def mkcbreak(mode):
    """cbreak mode termios"""
    # Do not map CR to NL on input.
    mode[IFLAG] &= ~(ICRNL)

    # Do not echo characters; disable canonical input.
    mode[LFLAG] &= ~(ECHO | ICANON)

    # POSIX.1-2017, 11.1.7 Non-Canonical Mode Input Processing,
    # Case B: MIN>0, TIME=0
    # A pending read shall block until MIN (here 1) bytes are received,
    # or a signal is received.
    mode[CC][VMIN] = 1
    mode[CC][VTIME] = 0

def setraw(fd, when=TCSAFLUSH):
    """Put terminal into raw mode.
    Returns original termios."""
    mode = tcgetattr(fd)
    new = list(mode)
    mkraw(new)
    tcsetattr(fd, when, new)
    return mode

def setcbreak(fd, when=TCSAFLUSH):
    """Put terminal into cbreak mode.
    Returns original termios."""
    mode = tcgetattr(fd)
    new = list(mode)
    mkcbreak(new)
    tcsetattr(fd, when, new)
    return mode

def login_tty(fd):
    """Prepare a terminal for a new login session.
    Makes the calling process a session leader; the tty of which
    fd is a file descriptor becomes the controlling tty, the stdin,
    the stdout, and the stderr of the calling process. Closes fd."""
    # Establish a new session.
    os.setsid()

    # The tty becomes the controlling terminal.
    try:
        ioctl(fd, TIOCSCTTY)
    except (NameError, OSError):
        # Fallback method; from Advanced Programming in the UNIX(R)
        # Environment, Third edition, 2013, Section 9.6 - Controlling Terminal:
        # "Systems derived from UNIX System V allocate the controlling
        # terminal for a session when the session leader opens the first
        # terminal device that is not already associated with a session, as
        # long as the call to open does not specify the O_NOCTTY flag."
        tmp_fd = os.open(os.ttyname(fd), os.O_RDWR)
        os.close(tmp_fd)

    # The tty becomes stdin/stdout/stderr.
    os.dup2(fd, STDIN_FILENO)
    os.dup2(fd, STDOUT_FILENO)
    os.dup2(fd, STDERR_FILENO)
    if fd != STDIN_FILENO and fd != STDOUT_FILENO and fd != STDERR_FILENO:
        os.close(fd)

try:
    from termios import TIOCGWINSZ, TIOCSWINSZ
    HAVE_WINSZ = True

    class winsize:

        def __init__(self, row=0, col=0, xpixel=0, ypixel=0, fd=None):
            """Creates winsize object.
            If fd is not None, gets window size of tty of which fd is a
            file descriptor. If fd is None, creates the winsize object
            based on the row, col, xpixel, and ypixel values provided."""
            if fd != None:
                self.tcgetwinsize(fd)
            else:
                self.ws_row = row
                self.ws_col = col
                self.ws_xpixel = xpixel
                self.ws_ypixel = ypixel

        def __setattr__(self, name, value):
            if not isinstance(value, int) or value < 0:
                raise TypeError("expected nonnegative integer")
            else:
                super().__setattr__(name, value)

        def __eq__(self, obj):
            if isinstance(obj, self.__class__):
                return self.__dict__ == obj.__dict__
            else:
                return False

        def __repr__(self):
            return f"winsize(ws_row={self.ws_row}, ws_col={self.ws_col}, ws_xpixel={self.ws_xpixel}, ws_ypixel={self.ws_ypixel})"

        def __str__(self):
            return f"(row={self.ws_row}, col={self.ws_col}, xpixel={self.ws_xpixel}, ypixel={self.ws_ypixel})"

        def tcgetwinsize(self, fd):
            """Gets window size of tty of which fd is a file descriptor."""
            # If fd is not a file descriptor of a tty, then OSError is raised.
            s = pack("HHHH", 0, 0, 0, 0)
            w = unpack("HHHH", ioctl(fd, TIOCGWINSZ, s))
            self.ws_row, self.ws_col, self.ws_xpixel, self.ws_ypixel = w

        def tcsetwinsize(self, fd):
            """Sets window size of tty of which fd is a file descriptor."""
            # If fd is not a file descriptor of a tty, then OSError is raised.
            ioctl(fd, TIOCSWINSZ, pack("HHHH", self.ws_row, self.ws_col,
                                       self.ws_xpixel, self.ws_ypixel))
except ImportError:
    HAVE_WINSZ = False

    class winsize:

        def __init__(self, row=0, col=0, xpixel=0, ypixel=0):
            raise NotImplementedError("termios.TIOCGWINSZ and/or termios.TIOCSWINSZ undefined")
