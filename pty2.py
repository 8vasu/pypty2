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

HAVE_WINCH = False
if tty.HAVE_WINSZ:
    try:
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

def openpty(mode=None, winsz=None):
    """openpty() -> (master_fd, slave_fd)
    Open a pty master/slave pair, using os.openpty() if possible."""

    try:
        master_fd, slave_fd = os.openpty()
    except (AttributeError, OSError):
        master_fd, slave_name = _open_terminal()
        slave_fd = slave_open(slave_name)

    if mode:
        tty.tcsetattr(slave_fd, tty.TCSAFLUSH, mode)
    if tty.HAVE_WINSZ and winsz:
        tty.setwinsize(slave_fd, winsz)

    return master_fd, slave_fd

def fork(mode=None, winsz=None):
    """fork() -> (pid, master_fd)
    Fork and make the child a session leader with a controlling terminal."""

    if not mode and not winsz:
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

    master_fd, slave_fd = openpty(mode, winsz)
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

def _pty_setup(slave_echo):
    """Opens a pty pair. If current stdin is a tty, then
    applies current stdin's termios and winsize to the slave,
    sets current stdin to raw mode. Returns (master, slave,
    original stdin mode/None, stdin winsize/None)."""
    mode = None
    winsz = None
    try:
        mode = tty.tcgetattr(STDIN_FILENO)
    except tty.error:
        master_fd, slave_fd = openpty()

        _mode = tty.tcgetattr(slave_fd)
        tty.mode_echo(_mode, slave_echo)
        tty.tcsetattr(slave_fd, tty.TCSAFLUSH, _mode)
    else:
        if tty.HAVE_WINSZ:
            winsz = tty.getwinsize(STDIN_FILENO)

        _mode = list(mode)
        tty.mode_echo(_mode, slave_echo)

        master_fd, slave_fd = openpty(_mode, winsz)

        tty.mode_raw(_mode)
        tty.tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, _mode)

    return master_fd, slave_fd, mode, winsz

def _winchset(slave_fd, saved_mask, handle_winch):
    """Installs SIGWINCH handler. Returns old SIGWINCH
    handler if relevant; returns None otherwise."""
    bkh = None
    if handle_winch:
        def _hwinch(signum, frame):
            """SIGWINCH handler."""
            _sigblock()
            new_slave_fd = os.open(slave_path, os.O_RDWR)
            tty.setwinsize(new_slave_fd, tty.getwinsize(STDIN_FILENO))
            os.close(new_slave_fd)
            _sigreset(saved_mask)

        slave_path = os.ttyname(slave_fd)
        try:
            # Raises ValueError if not called from main thread.
            bkh = signal.signal(SIGWINCH, _hwinch)
        except ValueError:
            pass

    return bkh

def _copy(master_fd, saved_mask=set(), master_read=_read, stdin_read=_read):
    """Parent copy loop for spawn.
    Copies
            pty master -> standard output   (master_read)
            standard input -> pty master    (stdin_read)
    To exit from this loop
        A. FreeBSD, OpenBSD, NetBSD return no data upon reading master EOF,
        B. Linux throws OSError when trying to read from master when
            1. ALL descriptors of slave are closed in parent AND
            2. child has exited."""
    fds = [master_fd, STDIN_FILENO]
    args = [fds, [], []]
    while True:
        _sigreset(saved_mask)
        rfds = select(*args)[0]
        _sigblock()
        if not rfds:
            return
        if master_fd in rfds:
            try:
                data = master_read(master_fd)
            except OSError:
                data = b""
            if not data:
                fds.remove(master_fd)
                args.append(0.01) # set timeout
            else:
                os.write(STDOUT_FILENO, data)
        if STDIN_FILENO in rfds:
            data = stdin_read(STDIN_FILENO)
            if not data:
                fds.remove(STDIN_FILENO)
            else:
                _writen(master_fd, data)

def spawn(argv, master_read=_read, stdin_read=_read, slave_echo=True, handle_winch=False):
    """Spawn a process."""
    if type(argv) == type(''):
        argv = (argv,)
    sys.audit('pty.spawn', argv)

    saved_mask = _getmask()
    _sigblock() # Reset during select() in _copy.

    master_fd, slave_fd, mode, winsz = _pty_setup(slave_echo)
    handle_winch = handle_winch and (winsz != None) and HAVE_WINCH
    bkh = _winchset(slave_fd, saved_mask, handle_winch)

    pid = os.fork()
    if pid == CHILD:
        os.close(master_fd)
        tty.login(slave_fd)
        _sigreset(saved_mask)
        os.execlp(argv[0], *argv)

    os.close(slave_fd)

    try:
        _copy(master_fd, saved_mask, master_read, stdin_read)
    finally:
        if mode:
            tty.tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode)

    if bkh:
        signal.signal(SIGWINCH, bkh)
    os.close(master_fd)
    _sigreset(saved_mask)

    return os.waitpid(pid, 0)[1]
