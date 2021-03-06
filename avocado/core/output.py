# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright: Red Hat Inc. 2013-2014
# Author: Lucas Meneghel Rodrigues <lmr@redhat.com>

"""
Manages output and logging in avocado applications.
"""
import logging
import os
import sys

from .settings import settings
from ..utils import path as utils_path


class FilterError(logging.Filter):

    def filter(self, record):
        return record.levelno >= logging.ERROR


class FilterInfo(logging.Filter):

    def filter(self, record):
        return record.levelno == logging.INFO


class ProgressStreamHandler(logging.StreamHandler):

    """
    Handler class that allows users to skip new lines on each emission.
    """

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            skip_newline = False
            if hasattr(record, 'skip_newline'):
                skip_newline = record.skip_newline
            stream.write(msg)
            if not skip_newline:
                stream.write('\n')
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


class PagerNotFoundError(Exception):
    pass


class Paginator(object):

    """
    Paginator that uses less to display contents on the terminal.

    Contains cleanup handling for when user presses 'q' (to quit less).
    """

    def __init__(self):
        try:
            paginator = "%s -FRSX" % utils_path.find_command('less')
        except utils_path.CmdNotFoundError:
            paginator = None

        paginator = os.environ.get('PAGER', paginator)

        if paginator is None:
            self.pipe = sys.stdout
        else:
            self.pipe = os.popen(paginator, 'w')

    def __del__(self):
        self.close()

    def close(self):
        try:
            self.pipe.close()
        except Exception:
            pass

    def write(self, msg):
        try:
            self.pipe.write(msg)
        except Exception:
            pass


def get_paginator():
    """
    Get a paginator.

    The paginator is whatever the user sets as $PAGER, or 'less', or if all
    else fails, sys.stdout. It is a useful feature inspired in programs such
    as git, since it lets you scroll up and down large buffers of text,
    increasing the program's usability.
    """
    return Paginator()


def add_console_handler(logger):
    """
    Add a console handler to a logger.

    :param logger: `logging.Logger` instance.
    """
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(fmt='%(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


class TermSupport(object):

    COLOR_BLUE = '\033[94m'
    COLOR_GREEN = '\033[92m'
    COLOR_YELLOW = '\033[93m'
    COLOR_RED = '\033[91m'
    COLOR_DARKGREY = '\033[90m'

    CONTROL_END = '\033[0m'

    MOVE_BACK = '\033[1D'
    MOVE_FORWARD = '\033[1C'

    ESCAPE_CODES = [COLOR_BLUE, COLOR_GREEN, COLOR_YELLOW, COLOR_RED,
                    COLOR_DARKGREY, CONTROL_END, MOVE_BACK, MOVE_FORWARD]

    """
    Class to help applications to colorize their outputs for terminals.

    This will probe the current terminal and colorize ouput only if the
    stdout is in a tty or the terminal type is recognized.
    """

    allowed_terms = ['linux', 'xterm', 'xterm-256color', 'vt100', 'screen',
                     'screen-256color']

    def __init__(self):
        self.HEADER = self.COLOR_BLUE
        self.PASS = self.COLOR_GREEN
        self.SKIP = self.COLOR_YELLOW
        self.FAIL = self.COLOR_RED
        self.INTERRUPT = self.COLOR_RED
        self.ERROR = self.COLOR_RED
        self.WARN = self.COLOR_YELLOW
        self.PARTIAL = self.COLOR_YELLOW
        self.ENDC = self.CONTROL_END
        self.LOWLIGHT = self.COLOR_DARKGREY
        self.enabled = True
        term = os.environ.get("TERM")
        colored = settings.get_value('runner.output', 'colored',
                                     key_type='bool')
        if ((not colored) or (not os.isatty(1)) or
                (term not in self.allowed_terms)):
            self.disable()

    def disable(self):
        """
        Disable colors from the strings output by this class.
        """
        self.enabled = False
        self.HEADER = ''
        self.PASS = ''
        self.SKIP = ''
        self.FAIL = ''
        self.INTERRUPT = ''
        self.ERROR = ''
        self.WARN = ''
        self.PARTIAL = ''
        self.ENDC = ''
        self.LOWLIGHT = ''
        self.MOVE_BACK = ''
        self.MOVE_FORWARD = ''

    def header_str(self, msg):
        """
        Print a header string (blue colored).

        If the output does not support colors, just return the original string.
        """
        return self.HEADER + msg + self.ENDC

    def fail_header_str(self, msg):
        """
        Print a fail header string (red colored).

        If the output does not support colors, just return the original string.
        """
        return self.FAIL + msg + self.ENDC

    def warn_header_str(self, msg):
        """
        Print a warning header string (yellow colored).

        If the output does not support colors, just return the original string.
        """
        return self.WARN + msg + self.ENDC

    def healthy_str(self, msg):
        """
        Print a healthy string (green colored).

        If the output does not support colors, just return the original string.
        """
        return self.PASS + msg + self.ENDC

    def partial_str(self, msg):
        """
        Print a string that denotes partial progress (yellow colored).

        If the output does not support colors, just return the original string.
        """
        return self.PARTIAL + msg + self.ENDC

    def pass_str(self):
        """
        Print a pass string (green colored).

        If the output does not support colors, just return the original string.
        """
        return self.MOVE_BACK + self.PASS + 'PASS' + self.ENDC

    def skip_str(self):
        """
        Print a skip string (yellow colored).

        If the output does not support colors, just return the original string.
        """
        return self.MOVE_BACK + self.SKIP + 'SKIP' + self.ENDC

    def fail_str(self):
        """
        Print a fail string (red colored).

        If the output does not support colors, just return the original string.
        """
        return self.MOVE_BACK + self.FAIL + 'FAIL' + self.ENDC

    def error_str(self):
        """
        Print a error string (red colored).

        If the output does not support colors, just return the original string.
        """
        return self.MOVE_BACK + self.ERROR + 'ERROR' + self.ENDC

    def interrupt_str(self):
        """
        Print an interrupt string (red colored).

        If the output does not support colors, just return the original string.
        """
        return self.MOVE_BACK + self.INTERRUPT + 'INTERRUPT' + self.ENDC

    def warn_str(self):
        """
        Print an warning string (yellow colored).

        If the output does not support colors, just return the original string.
        """
        return self.MOVE_BACK + self.WARN + 'WARN' + self.ENDC


term_support = TermSupport()


class LoggingFile(object):

    """
    File-like object that will receive messages pass them to logging.
    """

    def __init__(self, prefix='', level=logging.DEBUG,
                 logger=[logging.getLogger()]):
        """
        Constructor. Sets prefixes and which logger is going to be used.

        :param prefix - The prefix for each line logged by this object.
        """

        self._prefix = prefix
        self._level = level
        self._buffer = []
        if not isinstance(logger, list):
            logger = [logger]
        self._logger = logger

    def write(self, data):
        """"
        Writes data only if it constitutes a whole line. If it's not the case,
        store it in a buffer and wait until we have a complete line.
        :param data - Raw data (a string) that will be processed.
        """
        # splitlines() discards a trailing blank line, so use split() instead
        data_lines = data.split('\n')
        if len(data_lines) > 1:
            self._buffer.append(data_lines[0])
            self._flush_buffer()
        for line in data_lines[1:-1]:
            self._log_line(line)
        if data_lines[-1]:
            self._buffer.append(data_lines[-1])

    def writelines(self, lines):
        """"
        Writes itertable of lines

        :param lines: An iterable of strings that will be processed.
        """
        for data in lines:
            self.write(data)

    def _log_line(self, line):
        """
        Passes lines of output to the logging module.
        """
        for lg in self._logger:
            lg.log(self._level, self._prefix + line)

    def _flush_buffer(self):
        if self._buffer:
            self._log_line(''.join(self._buffer))
            self._buffer = []

    def flush(self):
        self._flush_buffer()

    def isatty(self):
        return False


class Throbber(object):

    """
    Produces a spinner used to notify progress in the application UI.
    """
    STEPS = ['-', '\\', '|', '/']
    # Only print a throbber when we're on a terminal
    if term_support.enabled:
        MOVES = [term_support.MOVE_BACK + STEPS[0],
                 term_support.MOVE_BACK + STEPS[1],
                 term_support.MOVE_BACK + STEPS[2],
                 term_support.MOVE_BACK + STEPS[3]]
    else:
        MOVES = ['', '', '', '']

    def __init__(self):
        self.position = 0

    def _update_position(self):
        if self.position == (len(self.MOVES) - 1):
            self.position = 0
        else:
            self.position += 1

    def render(self):
        result = self.MOVES[self.position]
        self._update_position()
        return result


class View(object):

    """
    Takes care of both disk logs and stdout/err logs.
    """

    def __init__(self, app_args=None, console_logger='avocado.app',
                 use_paginator=False):
        """
        Set up the console logger and the paginator mode.

        :param console_logger: logging.Logger identifier for the main app
                               logger.
        :type console_logger: str
        :param use_paginator: Whether to use paginator mode. Set it to True if
                              the program is supposed to output a large list of
                              lines to the user and you want the user to be able
                              to scroll through them at will (think git log).
        """
        self.app_args = app_args
        self.use_paginator = use_paginator
        self.console_log = logging.getLogger(console_logger)
        if self.use_paginator:
            self.paginator = get_paginator()
        else:
            self.paginator = None
        self.throbber = Throbber()
        self.tests_info = {}

    def cleanup(self):
        if self.use_paginator:
            self.paginator.close()

    def notify(self, event='message', msg=None, skip_newline=False):
        mapping = {'message': self._log_ui_header,
                   'minor': self._log_ui_minor,
                   'error': self._log_ui_error,
                   'warning': self._log_ui_warning,
                   'partial': self._log_ui_partial}
        if msg is not None:
            mapping[event](msg=msg, skip_newline=skip_newline)

    def notify_progress(self, progress):
        """
        Give an interactive indicator of the test progress

        :param progress: if indication of progress came explicitly from the
                         test. If false, it means the test process is running,
                         but not communicating test specific progress.
        :type progress: bool
        :rtype: None
        """
        if progress:
            self._log_ui_healthy(self.throbber.render(), True)
        else:
            self._log_ui_partial(self.throbber.render(), True)

    def add_test(self, state):
        self._log(msg=self._get_test_tag(state['tagged_name']),
                  skip_newline=True)

    def set_test_status(self, status, state):
        """
        Log a test status message
        :param status: the test status
        :param state: test state (used to get 'time_elapsed')
        """
        mapping = {'PASS': term_support.pass_str,
                   'ERROR': term_support.error_str,
                   'FAIL': term_support.fail_str,
                   'SKIP': term_support.skip_str,
                   'WARN': term_support.warn_str,
                   'INTERRUPTED': term_support.interrupt_str}
        if status == 'SKIP':
            msg = mapping[status]()
        else:
            msg = mapping[status]() + " (%.2f s)" % state['time_elapsed']
        self._log_ui_info(msg)

    def set_tests_info(self, info):
        self.tests_info.update(info)

    def _get_test_tag(self, test_name):
        return (' (%s/%s) %s:  ' %
                (self.tests_info['tests_run'],
                 self.tests_info['tests_total'], test_name))

    def _log(self, msg, level=logging.INFO, skip_newline=False):
        """
        Write a message to the avocado.app logger or the paginator.

        :param msg: Message to write
        :type msg: string
        """
        silent = False
        show_job_log = False
        if self.app_args is not None:
            if hasattr(self.app_args, 'silent'):
                silent = self.app_args.silent
            if hasattr(self.app_args, 'show_job_log'):
                show_job_log = self.app_args.show_job_log
        if not (silent or show_job_log):
            if self.use_paginator and (level < logging.ERROR):
                if not skip_newline:
                    msg += '\n'
                self.paginator.write(msg)
            else:
                extra = {'skip_newline': skip_newline}
                self.console_log.log(level=level, msg=msg, extra=extra)

    def _log_ui_info(self, msg, skip_newline=False):
        """
        Log a :mod:`logging.INFO` message to the UI.

        :param msg: Message to write.
        """
        self._log(msg, level=logging.INFO, skip_newline=skip_newline)

    def _log_ui_error_base(self, msg, skip_newline=False):
        """
        Log a :mod:`logging.ERROR` message to the UI.

        :param msg: Message to write.
        """
        self._log(msg, level=logging.ERROR, skip_newline=skip_newline)

    def _log_ui_healthy(self, msg, skip_newline=False):
        """
        Log a message that indicates that things are going as expected.

        :param msg: Message to write.
        """
        self._log_ui_info(term_support.healthy_str(msg), skip_newline)

    def _log_ui_partial(self, msg, skip_newline=False):
        """
        Log a message that indicates something (at least) partially OK

        :param msg: Message to write.
        """
        self._log_ui_info(term_support.partial_str(msg), skip_newline)

    def _log_ui_header(self, msg, skip_newline=False):
        """
        Log a header message.

        :param msg: Message to write.
        """
        self._log_ui_info(term_support.header_str(msg), skip_newline)

    def _log_ui_minor(self, msg, skip_newline=False):
        """
        Log a minor message.

        :param msg: Message to write.
        """
        self._log_ui_info(msg, skip_newline)

    def _log_ui_error(self, msg, skip_newline=False):
        """
        Log an error message (useful for critical errors).

        :param msg: Message to write.
        """
        self._log_ui_error_base(term_support.fail_header_str(msg), skip_newline)

    def _log_ui_warning(self, msg, skip_newline=False):
        """
        Log a warning message (useful for warning messages).

        :param msg: Message to write.
        """
        self._log_ui_info(term_support.warn_header_str(msg), skip_newline)

    def start_file_logging(self, logfile, loglevel, unique_id):
        """
        Start the main file logging.

        :param logfile: Path to file that will receive logging.
        :param loglevel: Level of the logger. Example: :mod:`logging.DEBUG`.
        :param unique_id: job.Job() unique id attribute.
        """
        self.job_unique_id = unique_id
        self.debuglog = logfile
        self.file_handler = logging.FileHandler(filename=logfile)
        self.file_handler.setLevel(loglevel)

        fmt = ('%(asctime)s %(module)-16.16s L%(lineno)-.4d %('
               'levelname)-5.5s| %(message)s')
        formatter = logging.Formatter(fmt=fmt, datefmt='%H:%M:%S')

        self.file_handler.setFormatter(formatter)
        test_logger = logging.getLogger('avocado.test')
        test_logger.addHandler(self.file_handler)
        test_logger.setLevel(loglevel)
        root_logger = logging.getLogger()
        root_logger.addHandler(self.file_handler)
        root_logger.setLevel(loglevel)

    def stop_file_logging(self):
        """
        Simple helper for removing a handler from the current logger.
        """
        test_logger = logging.getLogger('avocado.test')
        linux_logger = logging.getLogger('avocado.linux')
        root_logger = logging.getLogger()
        test_logger.removeHandler(self.file_handler)
        linux_logger.removeHandler(self.file_handler)
        root_logger.removeHandler(self.file_handler)
        self.file_handler.close()
