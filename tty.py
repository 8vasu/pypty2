"""Termios module extensions"""

# Author: Steen Lumholt

# Additions: Soumendra Ganguly <soumendra@tamu.edu>

from termios import *
from fcntl import ioctl
from struct import pack, unpack
import errno
import os
import signal

__all__ = ["cfmakeecho", "cfmakeraw", "cfmakecbreak", "setraw", "setcbreak",
           "HAVE_WINSZ", "winsize", "HAVE_WINCH"]

# Indices for termios list.
IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6

def cfmakeecho(mode, echo=True):
    """Set/unset ECHO."""
    if echo:
        mode[LFLAG] |= ECHO
    else:
        mode[LFLAG] &= ~ECHO

def cfmakeraw(mode):
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

def cfmakecbreak(mode):
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
    cfmakeraw(new)
    tcsetattr(fd, when, new)
    return mode

def setcbreak(fd, when=TCSAFLUSH):
    """Put terminal into cbreak mode.
    Returns original termios."""
    mode = tcgetattr(fd)
    new = list(mode)
    cfmakecbreak(new)
    tcsetattr(fd, when, new)
    return mode

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

        # tcgetwinsize() and tcsetwinsize() are expected to be included in
        # IEEE Std 1003.1 ("POSIX.1") issue 8 as a part of termios.h;
        # please see: https://www.austingroupbugs.net/view.php?id=1151#c3856
        #
        # If and when that happens in the future, termios.tcgetwinsize() and
        # termios.tcsetwinsize() should be implemented, and the following
        # methods should be updated to use them instead of relying upon
        # ioctl()+TIOCGWINSZ/TIOCSWINSZ, pack(), and unpack().
        def tcgetwinsize(self, fd):
            """Gets window size of tty of which fd is a file descriptor."""
            s = pack("HHHH", 0, 0, 0, 0)
            try:
                w = unpack("HHHH", ioctl(fd, TIOCGWINSZ, s))
            except OSError as e:
                raise error(e.errno, os.strerror(e.errno)) from e # termios.error
            self.ws_row, self.ws_col, self.ws_xpixel, self.ws_ypixel = w

        def tcsetwinsize(self, fd):
            """Sets window size of tty of which fd is a file descriptor."""
            try:
                ioctl(fd, TIOCSWINSZ, pack("HHHH", self.ws_row, self.ws_col,
                                           self.ws_xpixel, self.ws_ypixel))
            except OSError as e:
                raise error(e.errno, os.strerror(e.errno)) from e # termios.error
except ImportError:
    HAVE_WINSZ = False

    class winsize:

        def __init__(self, row=0, col=0, xpixel=0, ypixel=0):
            raise NotImplementedError("termios.TIOCGWINSZ and/or termios.TIOCSWINSZ undefined")

if HAVE_WINSZ and hasattr(signal, "SIGWINCH"):
    HAVE_WINCH = True
else:
    HAVE_WINCH = False
