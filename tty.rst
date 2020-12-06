:mod:`tty` --- Common tty operations
====================================

.. module:: tty
   :platform: Unix
   :synopsis: Utility functions that perform common tty operations.

.. moduleauthor:: Steen Lumholt
.. sectionauthor:: Moshe Zadka <moshez@zadka.site.co.il>
.. sectionauthor:: Soumendra Ganguly <soumendra@tamu.edu>

**Source code:** :source:`Lib/tty.py`

--------------

The :mod:`tty` module defines various functions that perform common tty
operations.

Because it requires the :mod:`termios` module, it will work only on Unix.

winsize Objects
---------------

.. data:: HAVE_WINSZ

   :const:`True` if both :const:`termios.TIOCGWINSZ` and :const:`termios.TIOCSWINSZ`
   are defined; :const:`False` otherwise. The :class:`winsize` objects are implemented
   if and only if this is :const:`True`.


.. class:: winsize(row=0, col=0, xpixel=0, ypixel=0, fd=None)

   Create a :class:`winsize` object, which represents a struct winsize; the
   attributes are *ws_row*, *ws_col*, *ws_xpixel*, and *ws_ypixel*; these are
   all nonnegative integers. If *fd* is not :const:`None`, then get window
   size of tty of which *fd* is a file descriptor. If *fd* is :const:`None`,
   then set the attributes based on the values of *row*, *col*, *xpixel*, and
   *ypixel*.


.. method:: winsize.tcgetwinsize(fd)

   Get window size of tty of which *fd* is a file descriptor. If *fd* is not a
   descriptor of a tty, then :exc:`OSError` is raised.


.. method:: winsize.tcsetwinsize(fd)

   Set window size of tty of which *fd* is a file descriptor. If *fd* is not a
   descriptor of a tty, then :exc:`OSError` is raised.


Termios Functions
-----------------

.. function:: mkecho(mode, echo=True)

   Set ECHO in the tty attribute list *mode*, which is a list like the one
   returned by :func:`termios.tcgetattr`, if *echo* is :const:`True` or is
   omitted. Unset ECHO if *echo* is :const:`False`.


.. function:: mkraw(mode)

   Convert the tty attribute list *mode*, which is a list like the one returned
   by :func:`termios.tcgetattr`, to that of a tty in raw mode.


.. function:: mkcbreak(mode)

   Convert the tty attribute list *mode*, which is a list like the one returned
   by :func:`termios.tcgetattr`, to that of a tty in cbreak mode.


.. function:: setraw(fd, when=termios.TCSAFLUSH)

   Set the tty of which *fd* is a file descriptor to raw mode. If *when*
   is omitted, then it defaults to :const:`termios.TCSAFLUSH`; *when* is passed
   to :func:`termios.tcsetattr`. The return value of :func:`termios.tcgetattr`
   is saved before setting *fd* to raw mode; this value is returned.


.. function:: setcbreak(fd, when=termios.TCSAFLUSH)

   Set the tty of which *fd* is a file descriptor to cbreak mode. If *when*
   is omitted, then it defaults to :const:`termios.TCSAFLUSH`; *when* is passed
   to :func:`termios.tcsetattr`. The return value of :func:`termios.tcgetattr`
   is saved before setting *fd* to raw mode; this value is returned.


Miscellaneous Functions
-----------------------

.. function:: login_tty(fd)

   Prepare the tty of which *fd* is a file descriptor for a new login session:
   make the calling process a session leader; make the tty the controlling tty,
   the stdin, the stdout, and the stderr of the calling process; close *fd*.


.. seealso::

   Module :mod:`termios`
      Low-level terminal control interface.

