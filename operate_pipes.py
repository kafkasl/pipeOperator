#!/usr/bin/python
from __future__ import print_function

from astParser import OperationParser

from functools import reduce
from time import time

import multiprocessing
import os
import sys
import signal


# OS pipes implementation ===============================================

DEFAULT_CHUNK_SIZE = 20000
IO_TIME = 0.0


def read(pipe, end_char='\n'):
    char = os.read(pipe, 1)
    string = ""
    if char == end_char:
        return char
    else:
        while char != end_char:
            if char != ' ':
                string += char
            char = os.read(pipe, 1)
        return string


class PipeOperator():

    END_MARK = "\n"

    def __init__(self, r, w, locks):
        self.read_pipe = r
        self.write_pipe = w
        self.locks = locks
        self.terminate = False
        signal.signal(signal.SIGUSR1, self._handle_signal)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.close(self.read_pipe)
        os.close(self.write_pipe)
        os._exit(0)

    def _handle_signal(self, signum, stack):
        self.terminate = True

    def _is_busy(self):
        return self.lock.locked()

    def _operate(self, op):

        try:
            result = OperationParser().get_result(op)
        except Exception, e:
            result = "Operation [%s] could not be evaluated -> %s" % (op, e)
        return result

    def _send_to_master(self, message):

        try:
            os.write(self.write_pipe, ("%s\n" % message))
            os.write(self.write_pipe, "%s" % self.END_MARK)
            return True
        except Exception, e:
            print("Communication from thread to master failed for message"
                  "[%s]\n%s" % (message, e))
            pass
        return False

    def start(self):

        read_lock, write_lock = self.locks
        end = False

        while not self.terminate:
            ops = []
            read_lock.release()

            counter = 0
            while not end and not self.terminate:
                try:
                    line = read(self.read_pipe)
                    if line:
                        if line == self.END_MARK:
                            end = True
                        else:
                            ops.append(line)
                            counter += 1
                except Exception, e:
                    pass
            try:
                if end:
                    results = map(self._operate, ops)
                    results = ["%s=%s" % (op, r) for op, r in zip(ops, results)]
                    results = reduce(lambda x, y: "%s\n%s" % (x, y), results)

                    write_lock.release()
                    if self._send_to_master(results):
                        end = False
            except Exception, e:
                print("Problem while operating and sending"
                      "results -> %s" % e, file=sys.stderr)
                os._exit(-1)


class PipeOperatorsManager:
    END_MARK = PipeOperator.END_MARK

    def __init__(self):
        self.pids = []
        self.master_pipes = {}
        self.locks = {}
        self.pending_results = {}
        self.data = []
        self.total_op = 0
        self.sent_op = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Closing master resources [%s threads]" % len(self.master_pipes),
              file=sys.stderr)

        for pid in self.pids:
            r, w = self.master_pipes[pid]
            os.kill(pid, signal.SIGUSR1)

        for pid in self.pids:
            os.waitpid(pid, 0)
            print("Process %s: closed" % pid, file=sys.stderr)

    def _create_threads(self, available_threads):
        pid = 1

        while pid and available_threads:
            master, thread = multiprocessing.Lock(), multiprocessing.Lock()
            master.acquire(True)
            thread.acquire(True)
            r_param, w_param = os.pipe()
            r_result, w_result = os.pipe()
            pid = os.fork()

            if pid:

                os.close(r_param)
                os.close(w_result)

                self.locks[pid] = (master, thread)

                self.master_pipes[pid] = r_result, w_param
                self.pending_results[pid] = False
                self.pids.append(pid)
                available_threads -= 1
            else:
                os.close(w_param)
                os.close(r_result)

                with PipeOperator(r_param, w_result, (master, thread)) as po:
                    po.start()

    def _receive_and_print_result(self, thread_id):

        read_pipe, _ = self.master_pipes[thread_id]

        counter = 0
        end = False
        while not end:
            try:
                global IO_TIME
                t = time()
                line = read(read_pipe)
                t2 = time()
                IO_TIME += (t2-t)

                if line:
                    if line == self.END_MARK:
                        end = True
                    else:
                        print("%s" % line)
                        counter += 1

            except Exception, e:
                print("Couldn't read line\n%s" % e, file=sys.stderr)

    def _send_chunk_to_thread(self, thread_id):

        _, w_param = self.master_pipes[thread_id]
        message = ""

        if len(self.data) > 0:
            message = "%s\n" % ('\n'.join(self.data[0:self.chunks_size]))

            self.sent_op += min(self.chunks_size, len(data))
            del self.data[0:self.chunks_size]

            pending_write = True

            while pending_write:
                try:
                    global IO_TIME
                    t = time()

                    os.write(w_param, "%s" % message)
                    os.write(w_param, "%s" % self.END_MARK)

                    t2 = time()
                    IO_TIME += (t2-t)
                    pending_write = False
                except Exception, e:
                    print("TIMEOUT: Problem sending chunk %s" % e, file=sys.stderr)
                    pass

    def solve(self, data, available_threads, chunks_size):

        self.data = filter(None, data.split("\n"))
        self.total_op = len(self.data)
        self.chunks_size = chunks_size

        print("Creating %s threads..." % available_threads, file=sys.stderr)
        self._create_threads(available_threads)

        pending_data = self.sent_op < self.total_op

        print("Performing operations...", file=sys.stderr)

        while any(self.pending_results.itervalues()) or pending_data:
            for pid in self.pids:
                l1, l2 = self.locks[pid]

                if pending_data and l1.acquire(False):
                    self._send_chunk_to_thread(pid)
                    self.pending_results[pid] = True
                    pending_data = self.sent_op < self.total_op

            for pid in self.pids:
                l1, l2 = self.locks[pid]

                if l2.acquire(False):
                    self._receive_and_print_result(pid)
                    self.pending_results[pid] = False


if __name__ == '__main__':
    t1 = time()

    print("Using python OS's pipes to perform operations in a different "
          "thread.\n", file=sys.stderr)

    available_threads = (multiprocessing.cpu_count() - 1)
    chunks_size = DEFAULT_CHUNK_SIZE
    data = []

    if len(sys.argv) < 2:
        print("Input file not defined", file=sys.stderr)
        sys.exit(-1)
    else:
        data = open(sys.argv[1], "r").read()
        if len(sys.argv) == 3:
            chunks_size = int(sys.argv[2])
        elif len(sys.argv) == 4:
            available_threads = int(sys.argv[3])

    with PipeOperatorsManager() as pom:
        try:
            pom.solve(data, available_threads, chunks_size)
            print("Operation's batch process ended", file=sys.stderr)
        except Exception, e:
            print("POM problem -> %s" % e, file=sys.stderr)

    t2 = time()
    print("Time: %s" % (t2 - t1), file=sys.stderr)
    print("IO Time: %s" % IO_TIME, file=sys.stderr)
