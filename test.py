#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021, Hedi Ziv
"""
Socket and Threading test.
"""

import argparse
import logging
from time import sleep
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
    f"maximum_num_of_iterations = 1000\n" \
    f"port = 11999\n" \
    f"buffer_size = 1024"

"""
================
GLOBAL VARIABLES
================
"""


verbosity = ''


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
==========
FLAG CLASS
==========
"""


class Flag:
    _flag = False

    def __init__(self, default: bool = False):
        assert isinstance(default, bool)
        self.set(default)

    def __del__(self):
        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def get(self) -> bool:
        logging.debug(f"Flag.get() returning {self._flag}")
        return self._flag

    def set(self, new_value: bool = True):
        assert isinstance(new_value, bool)
        logging.debug(f"Flag.set({new_value}")
        self._flag = new_value


"""
=====================================
MULTI-THREAD FLAG COMMUNICATION CLASS
=====================================
"""


class MultiThreadFlagCommunicationClass:
    """
    Server Class.
    """

    start_flag = None
    stop_flag = None
    condition = None

    def __init__(self, condition: Condition, start_flag: Flag, stop_flag: Flag):
        """
        Initialisations
        """

        _ = logging.getLogger(self.__class__.__name__)

        assert isinstance(condition, Condition)
        self.condition = condition
        assert isinstance(start_flag, Flag)
        self.start_flag = start_flag
        assert isinstance(stop_flag, Flag)
        self.stop_flag = stop_flag
        logging.debug(f'{str(self.__class__.__name__)} class instantiated.')

    def __del__(self):
        """ Destructor. """
        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def get_start_flag(self) -> bool:
        with self.condition:
            flag = self.start_flag.get()
        logging.debug(f"get start flag returning {flag}")
        return flag

    def set_start_flag(self, new_value: bool = True):
        assert isinstance(new_value, bool)
        with self.condition:
            self.start_flag.set(new_value)
        logging.debug(f"start flag set to {new_value}")

    def get_stop_flag(self) -> bool:
        with self.condition:
            flag = self.start_flag.get()
        logging.debug(f"get stop flag returning {flag}")
        return flag

    def set_stop_flag(self, new_value: bool = True):
        assert isinstance(new_value, bool)
        with self.condition:
            self.stop_flag.set(new_value)
        logging.debug(f"stop flag set to {new_value}")


"""
============
CLIENT CLASS
============
"""


class ListeningServerClass(Thread, MultiThreadFlagCommunicationClass):
    """
    Client Class.
    """

    buffer_size = 1
    server_socket = None

    def __init__(self, condition: Condition,
                 start_flag: Flag,
                 stop_flag: Flag,
                 socket_port: int,
                 buffer_size: int = 1):
        """
        Initialisations
        """

        Thread.__init__(self)
        MultiThreadFlagCommunicationClass.__init__(self, condition, start_flag, stop_flag)
        _ = logging.getLogger(self.__class__.__name__)

        assert isinstance(socket_port, int)
        assert socket_port > 1000  # valid range
        assert isinstance(buffer_size, int)
        assert buffer_size > 1
        self.buffer_size = buffer_size

        self.server_socket = socket(family=AF_INET, type=SOCK_DGRAM)
        self.server_socket.bind(("localhost", socket_port))
        logging.debug(f"listening client at port {socket_port} initiated")
        logging.debug(f'{str(self.__class__.__name__)} class instantiated.')

    def __del__(self):
        """ Destructor. """
        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def receiver_loop(self):
        global verbosity
        print("starting to listen")
        while not self.stop_flag.get():
            if kbhit() and getch().decode() == chr(27):  # ESC key pressed
                self.stop_flag.set()
                msg = f"ESC key pressed, {str(self.__class__.__name__)} thread stopping"
                if verbosity != "quiet":
                    print(msg)
                logging.debug(msg)
            received_values, _ = self.server_socket.recvfrom(self.buffer_size)
            sleep(0.4)
            msg = f"packet received: {received_values}"
            if not verbosity != "quiet":
                print(msg)
            logging.info(msg)
        print("receiver loop finished")
        logging.debug("receiver loop finished")

    def run(self):
        self.start_flag.set()
        self.receiver_loop()


"""
============
SERVER CLASS
============
"""


class TransmittingClientClass(Thread, MultiThreadFlagCommunicationClass):
    """
    Server Class.
    """

    maximum_num_of_iterations = 1
    server_socket = None
    client_socket_port = None

    def __init__(self,
                 condition: Condition,
                 start_flag: Flag,
                 stop_flag: Flag,
                 socket_port: int,
                 maximum_num_of_iterations: int = 1000):
        """
        Initialisations
        """

        Thread.__init__(self)
        MultiThreadFlagCommunicationClass.__init__(self, condition, start_flag, stop_flag)
        _ = logging.getLogger(self.__class__.__name__)

        assert isinstance(socket_port, int)
        assert socket_port > 1000  # valid range
        self.client_socket_port = socket_port
        assert isinstance(maximum_num_of_iterations, int)
        assert maximum_num_of_iterations > 1
        self.maximum_num_of_iterations = maximum_num_of_iterations

        self.server_socket = socket(family=AF_INET, type=SOCK_DGRAM)
        logging.debug(f"transmitting server at port {socket_port} initiated")
        logging.debug(f'{str(self.__class__.__name__)} class instantiated.')

    def __del__(self):
        """ Destructor. """
        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def transmitter_loop(self):
        global verbosity
        cnt = 0
        print("starting to transmit")
        while not self.stop_flag.get():
            if kbhit() and getch().decode() == chr(27):  # ESC key pressed
                self.stop_flag.set()
                msg = f"ESC key pressed, {str(self.__class__.__name__)} thread stopping"
                if verbosity != "quiet":
                    print(msg)
                logging.debug(msg)
            self.server_socket.sendto(str.encode(str(cnt)), ("localhost", self.client_socket_port))
            if verbosity != "quiet":
                print(f"sending value {cnt}")
            sleep(0.5)
            cnt += 1
        print("finished transmitting")
        logging.debug("transmitter loop finished")

    def run(self):
        while not self.start_flag.get():
            logging.debug("waiting for start_flag")
            sleep(0.1)
        self.transmitter_loop()


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
    port = 11999
    buffer_size = 64
    condition = Condition()
    start_flag = Flag(default=False)
    stop_flag = Flag(default=False)

    def __init__(self, maximum_num_of_iterations: int, port: int, buffer_size: int):
        """
        Initialisations
        """

        _ = logging.getLogger(self.__class__.__name__)
        logging.debug(f'{str(self.__class__.__name__)} class instantiated.')

        assert isinstance(maximum_num_of_iterations, int)
        assert maximum_num_of_iterations > 1
        self.maximum_num_of_iterations = maximum_num_of_iterations

        assert isinstance(port, int)
        assert port > 1000  # valid range
        self.port = port

        assert isinstance(buffer_size, int)
        assert buffer_size > 0
        self.buffer_size = buffer_size

    def __del__(self):
        """ Destructor. """

        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def run(self):
        transmitter = TransmittingClientClass(self.condition, self.start_flag, self.stop_flag,
                                              self.port, self.maximum_num_of_iterations)
        # transmitter = Thread(name="Transmitter", target=TransmittingClientClass,
        #                      args=(self.condition, self.start_flag, self.stop_flag, self.port, self.maximum_num_of_iterations))
        listener = ListeningServerClass(self.condition, self.start_flag, self.stop_flag,
                                        self.port, self.buffer_size)
        # listener = Thread(name="Listener", target=ListeningServerClass,
        #                   args=(self.condition, self.start_flag, self.stop_flag, self.port, self.buffer_size))

        transmitter.start()
        listener.start()

        transmitter.join()
        # listener.join(timeout=10)

        logging.debug("MainClass.run() finished running")


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
    port = 11999
    buffer_size = 64

    def __init__(self, config_path: str):
        """
        Initialisations
        """

        _ = logging.getLogger(self.__class__.__name__)
        logging.debug(f'{str(self.__class__.__name__)} class instantiated.')

        assert isinstance(config_path, str)
        config = Config(CONFIG_VERSION, config_path, DEFAULT_CFG)
        self.maximum_num_of_iterations = int(config["maximum_num_of_iterations"])
        self.port = int(config["port"])
        self.buffer_size = int(config["buffer_size"])

    def __del__(self):
        """ Destructor. """

        # destructor content here if required
        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def run(self):
        """
        Main program.
        """
        main_class = MainClass(self.maximum_num_of_iterations, self.port, self.buffer_size)
        main_class.run()


"""
======================
COMMAND LINE INTERFACE
======================
"""


def main():
    """ Argument Parser and Main Class instantiation. """

    global verbosity

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

    # ---------------------------------
    # Debug mode
    # ---------------------------------

    assert isinstance(args.debug, bool)
    assert isinstance(args.verbose, bool)
    assert isinstance(args.quiet, bool)

    console = logging.StreamHandler()
    if args.debug:
        console.setLevel(logging.DEBUG)
        verbosity = "debug"
    elif args.verbose:
        console.setLevel(logging.INFO)
        verbosity = "verbose"
    else:  # default
        console.setLevel(logging.WARNING)
        verbosity = "quiet"
    formatter = logging.Formatter('%(threadName)-8s, %(name)-15s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    logging.getLogger('main')
    logging.info(f"Successfully opened log file named: {log_filename}")
    logging.debug(f"Program run with the following arguments: {str(args)}")

    # ---------------------------------
    # Instantiation
    # ---------------------------------

    arg_processing = ArgumentsAndConfigProcessing(config_path=args.config[0])
    arg_processing.run()
    logging.debug('Program execution completed. Starting clean-up.')


if __name__ == "__main__":
    main()
