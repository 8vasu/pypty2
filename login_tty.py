from fcntl import ioctl
import os

STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2

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
    #if fd > STDERR_FILENO:
    if fd != STDIN_FILENO and fd != STDOUT_FILENO and fd != STDERR_FILENO:
        os.close(fd)
