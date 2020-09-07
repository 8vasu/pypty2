#!/usr/bin/env python3
import argparse
import os
import sys
import time
import pty2

parser = argparse.ArgumentParser()
parser.add_argument('-a', dest='append', action='store_true')
parser.add_argument('-p', dest='use_python', action='store_true')
parser.add_argument('filename', nargs='?', default='typescript')
options = parser.parse_args()

shell = sys.executable if options.use_python else os.environ.get('SHELL', 'sh')
filename = options.filename
mode = 'ab' if options.append else 'wb'

with open(filename, mode) as script:
    def read(fd):
        data = os.read(fd, 1024)
        script.write(data)
        return data

    print('Script started, file is', filename)
    script.write(('Script started on %s\n' % time.asctime()).encode())

    pty2.spawn(shell, read)

    script.write(('Script done on %s\n' % time.asctime()).encode())
    print('Script done, file is', filename)


"""
SIGWINCH test
--------------

$ tty
<output should look something like /dev/tty0>

$ stty size
<output should look like 25 80 where 25 is # of rows, 80 is # of columns>

$ python3 ./demo.py

To send SIGWINCH to "python3 ./demo.py", do the following.
On linux:
$ stty -F /dev/tty0 rows 25 cols 20
On BSDs:
$ stty -f /dev/tty0 rows 25 cols 20

Note: "stty size" is equivalent to "echo $(tput lines) $(tput cols)".
"""
