#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021, Hedi Ziv
"""
Socket and Threading test.
"""

import argparse
import logging
from msvcrt import kbhit, getch

from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread, Condition

from tools import Config

"""
=========
CONSTANTS
=========
"""

DESCRIPTION = \
    "Socket and Threading test."

CONFIG_VERSION = 0.1  # must specify minimal configuration file version here

DEFAULT_CFG = \
    f"# test.py configuration file.\n" \
    f"# use # to mark comments.  Note # has to be first character in line.\n" \
    f"\n" \
    f"config_version = {CONFIG_VERSION}\n" \
    f"\n" \
    f"############################\n" \
    f"# important file locations #\n" \
    f"############################\n" \
    f"# use slash (/) or single back-slash (\\) as path separators.\n" \
    f"\n" \
    f"default_destination_directory = .\\tmp\n" \
    f"\n" \
    f"maximum_num_of_iterations = 1000"

"""
================
GLOBAL VARIABLES
================
"""


"""
=========
FUNCTIONS
=========
"""


def is_number(string_value: str):
    assert isinstance(string_value, str)
    try:
        float(string_value)
        return True
    except ValueError:
        return False


"""
==================
MULTI-THREAD CLASS
==================
"""


class MultiThreadClass(Thread):
    """
    Server Class.
    """

    flag = False
    condition = None

    def __init__(self, condition: Condition, flag: bool):
        """
        Initialisations
        """

        Thread.__init__(self)
        _ = logging.getLogger(self.__class__.__name__)

        assert isinstance(condition, Condition)
        self.condition = condition
        assert isinstance(flag, bool)
        self.flag = flag
        logging.debug(f'{str(self.__class__.__name__)} class instantiated.')

    def __del__(self):
        """ Destructor. """

        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def get_stop_flag(self) -> bool:
        self.condition.acquire()
        stop_flag = self.flag
        self.condition.release()
        return stop_flag

    def set_stop_flag(self, new_value: bool = True):
        assert isinstance(new_value, bool)
        self.condition.acquire()
        self.flag = new_value
        self.condition.release()


"""
============
CLIENT CLASS
============
"""


class ListeningClientClass(MultiThreadClass):
    """
    Client Class.
    """

    buffer_size = 1
    client_socket = None

    def __init__(self, condition: Condition,
                 stop_flag: bool,
                 socket_port: int,
                 buffer_size: int = 1):
        """
        Initialisations
        """

        MultiThreadClass.__init__(self, condition=condition, flag=stop_flag)
        _ = logging.getLogger(self.__class__.__name__)

        assert isinstance(socket_port, int)
        assert socket_port > 1000  # valid range
        assert isinstance(buffer_size, int)
        assert buffer_size > 1
        self.buffer_size = buffer_size

        self.client_socket = socket(AF_INET, SOCK_DGRAM)
        self.client_socket.bind(("localhost", socket_port))
        # self.client_socket.listen(1)  # maximum 1 connection
        logging.debug(f"listening client at port {socket_port} initiated")
        logging.debug(f'{str(self.__class__.__name__)} class instantiated.')

    def __del__(self):
        """ Destructor. """

        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def run(self):
        while not self.get_stop_flag():
            if kbhit() and getch().decode() == chr(27):  # ESC key pressed
                self.set_stop_flag()
                logging.debug("ESC key pressed, listening client thread stopping")
            received_values = self.client_socket.recv(self.buffer_size)
            logging.info(f"packet received: {received_values}")
        logging.debug("stop flagged - server loop stopped")


"""
============
SERVER CLASS
============
"""


class TransmittingServerClass(MultiThreadClass):
    """
    Server Class.
    """

    maximum_num_of_iterations = 1
    server_socket = None

    def __init__(self, condition: Condition,
                 stop_flag: bool,
                 socket_port: int,
                 maximum_num_of_iterations: int = 1000):
        """
        Initialisations
        """

        MultiThreadClass.__init__(self, condition=condition, flag=stop_flag)
        _ = logging.getLogger(self.__class__.__name__)

        assert isinstance(socket_port, int)
        assert socket_port > 1000  # valid range
        assert isinstance(maximum_num_of_iterations, int)
        assert maximum_num_of_iterations > 1
        self.maximum_num_of_iterations = maximum_num_of_iterations

        self.server_socket = socket(AF_INET, SOCK_DGRAM)
        # self.server_socket.connect(("localhost", socket_port))
        logging.debug(f"transmitting server at port {socket_port} initiated")
        logging.debug(f'{str(self.__class__.__name__)} class instantiated.')

    def __del__(self):
        """ Destructor. """

        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def run(self):
        cnt = 0
        while not self.get_stop_flag():
            if kbhit() and getch().decode() == chr(27):  # ESC key pressed
                self.set_stop_flag()
                logging.debug("ESC key pressed, transmitting server thread stopping")
            self.server_socket.send((cnt))
            cnt += 1
        logging.debug("stop flagged - server loop stopped")


"""
==================
MAIN PROGRAM CLASS
==================
"""


class MainClass:
    """
    Main Class.
    """

    maximum_num_of_iterations = 1
    condition = Condition()
    flag = False

    def __init__(self, maximum_num_of_iterations: int):
        """
        Initialisations
        """

        _ = logging.getLogger(self.__class__.__name__)
        logging.debug(f'{str(self.__class__.__name__)} class instantiated.')

        assert isinstance(maximum_num_of_iterations, int)
        assert maximum_num_of_iterations > 1
        self.maximum_num_of_iterations = maximum_num_of_iterations

    def __del__(self):
        """ Destructor. """

        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def run(self):
        port = 11999
        server = TransmittingServerClass(self.condition, self.flag, port, 1000)
        server.start()
        server.join()
        logging.debug("server started in main")
        client = ListeningClientClass(self.condition, self.flag, port, 64)
        client.start()
        client.join()
        logging.debug("client started in main")


"""
========================
ARGUMENT SANITY CHECKING
========================
"""


class ArgumentsAndConfigProcessing:
    """
    Argument parsing and default value population (from config).
    """

    maximum_num_of_iterations = 1

    def __init__(self, config_path: str):
        """
        Initialisations
        """

        _ = logging.getLogger(self.__class__.__name__)
        logging.debug(f'{str(self.__class__.__name__)} class instantiated.')

        assert isinstance(config_path, str)
        config = Config(CONFIG_VERSION, config_path, DEFAULT_CFG)
        self.maximum_num_of_iterations = int(config["maximum_num_of_iterations"])

    def __del__(self):
        """ Destructor. """

        # destructor content here if required
        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def run(self):
        """
        Main program.
        """
        main_class = MainClass(self.maximum_num_of_iterations)
        main_class.run()


"""
======================
COMMAND LINE INTERFACE
======================
"""


def main():
    """ Argument Parser and Main Class instantiation. """

    # ---------------------------------
    # Parse arguments
    # ---------------------------------

    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter)

    no_extension_default_name = parser.prog.rsplit('.', 1)[0]
    parser.add_argument('-c', dest='config', nargs=1, type=str, default=[f"./{no_extension_default_name}.cfg"],
                        help=f"path to config file. ./{no_extension_default_name}.cfg by default")

    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('-d', '--debug', help='sets verbosity to display debug level messages',
                        action="store_true")
    group1.add_argument('-v', '--verbose', help='sets verbosity to display information level messages',
                        action="store_true")
    group1.add_argument('-q', '--quiet', help='sets verbosity to display error level messages',
                        action="store_true")

    args = parser.parse_args()

    # ---------------------------------
    # Preparing LogFile formats
    # ---------------------------------

    assert isinstance(args.config, list)
    assert len(args.config) == 1
    assert isinstance(args.config[0], str)

    log_filename = f'{no_extension_default_name}.log'
    try:
        logging.basicConfig(filename=log_filename, filemode='a', datefmt='%Y/%m/%d %I:%M:%S %p', level=logging.DEBUG,
                            format='%(asctime)s, %(threadName)-8s, %(name)-15s %(levelname)-8s - %(message)s')
    except PermissionError as err:
        raise PermissionError(f'Error opening log file {log_filename}. File might already be opened by another '
                              f'application. Error: {err}\n')

    console = logging.StreamHandler()
    if args.debug:
        console.setLevel(logging.DEBUG)
    elif args.verbose:
        console.setLevel(logging.INFO)
    else:  # default
        console.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(threadName)-8s, %(name)-15s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    logging.getLogger('main')
    logging.info(f"Successfully opened log file named: {log_filename}")
    logging.debug(f"Program run with the following arguments: {str(args)}")

    # ---------------------------------
    # Debug mode
    # ---------------------------------

    assert isinstance(args.debug, bool)
    assert isinstance(args.verbose, bool)
    assert isinstance(args.quiet, bool)

    # ---------------------------------
    # Instantiation
    # ---------------------------------

    arg_processing = ArgumentsAndConfigProcessing(config_path=args.config[0])
    arg_processing.run()
    logging.debug('Program execution completed. Starting clean-up.')


if __name__ == "__main__":
    main()
