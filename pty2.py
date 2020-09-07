"""Pseudo terminal utilities v2."""

# Copyright (C) 2020 Soumendra Ganguly
#
# Prepared for cpython version >= 3.8
#
# Tested on Debian 10 GNU/Linux amd64,
# FreeBSD 12.1-RELEASE amd64,
# NetBSD 9.0 amd64,
# OpenBSD 6.7 amd64.
#
# To-do: Test on Solaris, Illumos, macOS, Cygwin, etc. Add Windows ConPTY support.

# v1 author: Steen Lumholt -- with additions by Guido.
# Copyright (C) 2001-2020 Python Software Foundation; All Rights Reserved

from select import select
from fcntl import ioctl
from struct import pack
import os
import sys
import tty
import signal

__all__ = ["openpty", "fork", "spawn"]

STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2

CHILD = 0

ALL_SIGNALS = signal.valid_signals()

HAVE_WINSZ = False
HAVE_WINCH = False
try:
    TIOCGWINSZ = tty.TIOCGWINSZ
    TIOCSWINSZ = tty.TIOCSWINSZ
    HAVE_WINSZ = True
    SIGWINCH = signal.SIGWINCH
    HAVE_WINCH = True
except AttributeError:
    pass

def _open_terminal():
    """Open pty master and return (master_fd, tty_name)."""
    for x in 'pqrstuvwxyzPQRST':
        for y in '0123456789abcdef':
            pty_name = '/dev/pty' + x + y
            try:
                fd = os.open(pty_name, os.O_RDWR)
            except OSError:
                continue
            return (fd, '/dev/tty' + x + y)
    raise OSError('out of pty devices')

def openpty():
    """openpty() -> (master_fd, slave_fd)
    Open a pty master/slave pair, using os.openpty() if possible."""

    try:
        return os.openpty()
    except (AttributeError, OSError):
        pass
    master_fd, slave_name = _open_terminal()
    slave_fd = slave_open(slave_name)
    return master_fd, slave_fd

def fork():
    """fork() -> (pid, master_fd)
    Fork and make the child a session leader with a controlling terminal."""

    try:
        pid, fd = os.forkpty()
    except (AttributeError, OSError):
        pass
    else:
        if pid == CHILD:
            try:
                os.setsid()
            except OSError:
                # os.forkpty() already set us session leader
                pass
        return pid, fd

    master_fd, slave_fd = openpty()
    pid = os.fork()
    if pid == CHILD:
        os.close(master_fd)
        tty.login(slave_fd)
    else:
        os.close(slave_fd)

    # Parent and child process.
    return pid, master_fd

def _writen(fd, data):
    """Write all the data to a descriptor."""
    while data:
        n = os.write(fd, data)
        data = data[n:]

def _read(fd):
    """Default read function."""
    return os.read(fd, 1024)

def _getmask():
    """Gets signal mask of current thread."""
    return signal.pthread_sigmask(signal.SIG_BLOCK, [])

def _sigblock():
    """Blocks all signals."""
    signal.pthread_sigmask(signal.SIG_BLOCK, ALL_SIGNALS)

def _sigreset(saved_mask):
    """Restores signal mask."""
    signal.pthread_sigmask(signal.SIG_SETMASK, saved_mask)

def _winresz(fd):
    """Resizes window.
    If current stdin and fd are terminals, then the window
    size of fd is set to that of current stdin and this
    window size is returned; None is returned otherwise."""
    try:
        s = pack('HHHH', 0, 0, 0, 0)
        w = ioctl(STDIN_FILENO, TIOCGWINSZ, s)
        ioctl(fd, TIOCSWINSZ, w)
        return w
    except OSError:
        pass

    return None

def _termset(slave_fd, slave_echo):
    """Set termios of current stdin and of pty slave.
    If current stdin is a tty, returns original termios
    thereof; returns None otherwise."""
    try:
        mode = tty.tcgetattr(STDIN_FILENO)
    except tty.error:
        mode = None

    if mode:
        new = list(mode)
        tty.mode_echo(new, slave_echo)
        tty.tcsetattr(slave_fd, tty.TCSAFLUSH, new)
        tty.mode_raw(new)
        tty.tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, new)
    else:
        new = tty.tcgetattr(slave_fd)
        tty.mode_echo(new, slave_echo)
        tty.tcsetattr(slave_fd, tty.TCSAFLUSH, new)

    return mode

def _winset(slave_fd, saved_mask, handle_sigwinch):
    """Set pty slave window size and SIGWINCH handler.
    Returns old SIGWINCH handler if relevant, None
    otherwise."""
    bkh = None
    can_resize_win = HAVE_WINSZ and _winresz(slave_fd)
    handle_sigwinch = handle_sigwinch and can_resize_win and HAVE_WINCH
    if handle_sigwinch:
        def _hwinch(signum, frame):
            """SIGWINCH handler."""
            _sigblock()
            try:
                new_slave_fd = os.open(slave_path, os.O_RDWR)
            except OSError:
                pass
            else:
                _winresz(new_slave_fd)
                os.close(new_slave_fd)
            _sigreset(saved_mask)

        bkh = signal.getsignal(SIGWINCH)
        slave_path = os.ttyname(slave_fd)
        try:
            signal.signal(SIGWINCH, _hwinch) # Fails if not called from main thread.
        except ValueError:
            bkh = None

    return bkh

def _mainloop(master_fd, saved_mask, master_read=_read, stdin_read=_read):
    """Parent copy loop for spawn.
    Copies
            pty master -> standard output   (master_read)
            standard input -> pty master    (stdin_read)
    To exit from this loop
        A. FreeBSD, OpenBSD, NetBSD return upon master EOF,
        B. Linux throws OSError when trying to read from master when
            1. ALL descriptors of slave are closed in parent AND
            2. child has exited."""
    fds = [master_fd, STDIN_FILENO]
    while True:
        _sigreset(saved_mask)
        rfds = select(fds, [], [])[0]
        _sigblock()
        if master_fd in rfds:
            try:
                data = master_read(master_fd)
            except OSError:
                data = b""
            if not data:
                return
            else:
                os.write(STDOUT_FILENO, data)
        if STDIN_FILENO in rfds:
            data = stdin_read(STDIN_FILENO)
            if not data:
                fds.remove(STDIN_FILENO)
            else:
                _writen(master_fd, data)

def spawn(argv, master_read=_read, stdin_read=_read, slave_echo=True, handle_sigwinch=False):
    """Spawn a process."""
    if type(argv) == type(''):
        argv = (argv,)
    sys.audit('pty.spawn', argv)

    saved_mask = _getmask()
    master_fd, slave_fd = openpty()
    mode = _termset(slave_fd, slave_echo)
    bkh = _winset(slave_fd, saved_mask, handle_sigwinch)
    pid = os.fork()
    if pid == CHILD:
        os.close(master_fd)
        tty.login(slave_fd)
        os.execlp(argv[0], *argv)

    _sigblock() # Reset during select() in _mainloop.
    os.close(slave_fd)

    _mainloop(master_fd, saved_mask, master_read, stdin_read)

    if bkh:
        signal.signal(SIGWINCH, bkh)
    if mode:
        tty.tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode)
    os.close(master_fd)
    _sigreset(saved_mask)

    return os.waitpid(pid, 0)[1]
