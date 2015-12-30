#!/usr/bin/python
from __future__ import print_function
from __future__ import division

from astParser import OperationParser
from time import time
import sys


if __name__ == '__main__':
    t1 = time()

    print("Using ast operator to perform operations", file=sys.stderr)

    data = []

    if len(sys.argv) < 2:
        print("Input file not defined", file=sys.stderr)
        sys.exit(-1)
    else:
        data = open(sys.argv[1], "r").read()

    for line in filter(None, data.split('\n')):
        try:
            print("%s" % OperationParser().get_result(line))
        except Exception, e:
            print("[%s] could not be parsed into a"
                  " valid arithmetic operation" % line, file=sys.stderr)

    t2 = time()
    print("Time: %s" % (t2 - t1), file=sys.stderr)
