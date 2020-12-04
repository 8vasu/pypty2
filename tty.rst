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
   field names are *ws_row*, *ws_col*, *ws_xpixel*, and *ws_ypixel*. If *fd*
   is not :const:`None`, then get window size of tty of which *fd* is a file
   descriptor. If *fd* is :const:`None`, then create the :class:`winsize` object
   based on the *row*, *col*, *xpixel*, and *ypixel* values provided.


.. method:: winsize.row(num=None)

   Set *ws_row* to *num* if *num* is not :const:`None`; return *ws_row*
   otherwise. The default value of *num* is :const:`None`.


.. method:: winsize.col(num=None)

   Set *ws_col* to *num* if *num* is not :const:`None`; return *ws_col*
   otherwise. The default value of *num* is :const:`None`.


.. method:: winsize.xpixel(num=None)

   Set *ws_xpixel* to *num* if *num* is not :const:`None`; return *ws_xpixel*
   otherwise. The default value of *num* is :const:`None`.


.. method:: winsize.ypixel(num=None)

   Set *ws_ypixel* to *num* if *num* is not :const:`None`; return *ws_ypixel*
   otherwise. The default value of *num* is :const:`None`.


.. method:: winsize.getwinsize(fd)

   Get window size of tty of which *fd* is a file descriptor. If *fd* is not a
   descriptor of a tty, then :exc:`OSError` is raised.


.. method:: winsize.setwinsize(fd)

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

   Makes the calling process a session leader; if *fd* is a descriptor of a
   tty, then that tty becomes the standard input, the standard output, the
   standard error, and the controlling tty of the calling process. Closes *fd*.


.. seealso::

   Module :mod:`termios`
      Low-level terminal control interface.

