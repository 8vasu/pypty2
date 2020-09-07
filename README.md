# pypty2

Revised cpython pty library meant to be a drop-in replacement for Lib/pty.py

Improvements in pty2:

1. Tested on Linux, FreeBSD, OpenBSD, and NetBSD. Fixes hang on FreeBSD. See bpo-26228.
2. Adds terminal window resizing support to pty.spawn() -> pty2.spawn() by registering
   a SIGWINCH handler (optional). When using tiling window managers, GUI windows are
   frequently resized; resizing the terminal emulators's GUI window resizes the underlying
   terminal; if terminal window size is not properly set, then program output can be hard
   to visually parse. See bpo-41494, bpo-41541.
3. pty2.spawn() appropriately sets current stdin and slave termios. Optionally lets the
   programmer turn off ECHO in slave termios.
4. Blocks signals when necessary. Read CHANGES for details.
5. Improves fallback code in pty.fork() -> pty2.fork() by using tty.login(), which uses
   TIOCSCTTY if possible. tty.login() is reused in pty2.spawn().

Improvements in tty:

1. Added tty.mode_echo(), tty.mode_raw(), tty.login() to increase code reusability.
2. tty.setraw() and tty.setcbreak() now return original termios to avoid multiple tty.tcgetattr()s.