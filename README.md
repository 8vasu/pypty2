# pypty2

Revised cpython pty library meant to be a drop-in replacement for Lib/pty.py

Improvements in pty2:

1. Tested on Linux, FreeBSD, OpenBSD, and NetBSD. Fixes hang on FreeBSD. See bpo-26228.
2. Like openpty(3) and forkpty(3), pty2.openpty() and pty2.fork() accept slave termios
   and slave winsize as arguments.
3. pty2.spawn() appropriately sets current stdin termios, slave termios, and slave winsize.
   Optionally lets the programmer turn off ECHO in slave termios.
4. Adds pty slave window resizing support to pty.spawn() -> pty2.spawn() by registering
   a SIGWINCH handler (optional argument). Consider the following practical scenarios.
      1. Creating split windows/panes while using a terminal multiplexer ( such as screen or tmux )
         resizes stdin's terminal.
      2. When using tiling window managers ( such as i3wm ), GUI windows ( such as X windows ) are
         frequently resized; resizing the terminal emulator's ( such as xterm ) GUI window resizes
         stdin's terminal.
      3. When using GNU Emacs, it is common to split a frame to create an ansi-term window; the
         ansi-term window can be resized later; this also leads to stdin's terminal being resized.

    In all of the above scenarios, pty.spawn() does not update the slave window size accordingly; this
    makes program output hard to visually parse. pty2.spawn() does not have this limitation. See bpo-41494,
    bpo-41541.
5. Blocks signals when necessary. Read CHANGES for details.
6. Improves fallback code in pty.fork() -> pty2.fork() by using tty.login(), which uses
   TIOCSCTTY if possible. tty.login() is reused in pty2.spawn().

Improvements in tty:

1. Adds tty.mode_echo(), tty.mode_raw(), tty.getwinsz(), tty.login() to increase code reusability.
2. tty.setraw() and tty.setcbreak() now return original termios to avoid multiple tty.tcgetattr()s.