# pypty2

Revised cpython pty library meant to be a drop-in replacement for Lib/pty.py

Improvements:

1. Tested on Linux, FreeBSD, OpenBSD, and NetBSD. Fixes hang on FreeBSD. See bpo-26228.
2. Adds terminal window resizing support in spawn() by registering a SIGWINCH handler (optional).
   When using tiling window managers, GUI windows are frequently resized; resizing the
   terminal emulators's GUI window resizes the underlying terminal; if terminal window
   size is not properly set, then program output can be hard to visually parse. See bpo-41494,
   bpo-41541.
3. Properly sets current stdin and slave termios. Optionally lets the programmer turn off ECHO in slave termios.
4. Blocks signals when necessary. Read CHANGES for details.