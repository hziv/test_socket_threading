#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021, Hedi Ziv
"""
Socket and Threading test.
"""

from typing import Union
import argparse
import logging
from time import sleep
from msvcrt import kbhit, getch

from socket import socket, timeout, error, AF_INET, SOCK_DGRAM
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
===========
STATE CLASS
===========
"""


class State:
    _approved_values = list()
    _state = None

    def __init__(self, approved_values: Union[tuple, list]):
        """
        Initialisations
        @param approved_values: list of approved state machine values, 1st value used as default
        """
        _ = logging.getLogger(self.__class__.__name__)
        assert isinstance(approved_values, (tuple, list))
        assert len(approved_values) > 0
        self._approved_values = approved_values
        self._state = self._approved_values[0]

    def __del__(self):
        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    @property
    def state(self) -> Union[None, str, int]:
        return self._state

    @state.setter
    def state(self, new_value: Union[str, int]):
        assert isinstance(new_value, (str, int))
        assert new_value in self._approved_values
        self._state = new_value


"""
=====================================
MULTI-THREAD FLAG COMMUNICATION CLASS
=====================================
"""


class MultiThreadStateCommunicationClass:
    """
    Server Class.
    """

    _state = None
    _condition = None

    def __init__(self, condition: Condition, state: State):
        """
        Initialisations
        @param condition: pointer to Condition object
        @param state: pointer to State object
        """
        _ = logging.getLogger(self.__class__.__name__)

        assert isinstance(condition, Condition)
        self._condition = condition
        assert isinstance(state, State)
        self._state = state
        logging.debug(f'{str(self.__class__.__name__)} class instantiated.')

    def __del__(self):
        """ Destructor. """
        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    @property
    def state(self):
        global verbosity
        with self._condition:
            ret = self._state.state
        logging.debug(f"state.get() = {ret}")
        return ret

    @state.setter
    def state(self, new_value: Union[str, int]):
        with self._condition:
            self._state.state = new_value
        logging.debug(f"state.set({new_value})")


"""
============
CLIENT CLASS
============
"""


class ListeningServerClass(Thread, MultiThreadStateCommunicationClass):
    """
    Client Class.
    """

    buffer_size = 1
    server_socket = None

    def __init__(self, condition: Condition,
                 state: State,
                 socket_port: int,
                 buffer_size: int = 1):
        """
        Initialisations
        """

        Thread.__init__(self, name="Listener")
        MultiThreadStateCommunicationClass.__init__(self, condition, state)
        _ = logging.getLogger(self.__class__.__name__)

        assert isinstance(socket_port, int)
        assert socket_port > 1000  # valid range
        assert isinstance(buffer_size, int)
        assert buffer_size > 1
        self.buffer_size = buffer_size

        self.server_socket = socket(family=AF_INET, type=SOCK_DGRAM)
        self.server_socket.bind(("localhost", socket_port))
        self.server_socket.settimeout(2)  # two seconds
        logging.debug(f"listening client at port {socket_port} initiated")
        logging.debug(f'{str(self.__class__.__name__)} class instantiated.')

    def __del__(self):
        """ Destructor. """
        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def receiver_loop(self):
        global verbosity
        retry_cnt = 2  # retry twice
        logging.info("starting to listen")
        while self.state == "running" and retry_cnt > 0:
            if kbhit() and getch().decode() == chr(27):  # ESC key pressed
                self.state = "listener_server_stopped"
                logging.info(f"ESC key pressed, {str(self.__class__.__name__)} thread stopping")
            try:
                received_values, _ = self.server_socket.recvfrom(self.buffer_size)
            except timeout as e:
                logging.debug(f"socket recvfrom() timed-out ({e}), retrying")
                retry_cnt -= 1
                continue
            except error as e:
                logging.error(f"socket recvfrom() exception, error: {e}")
                break
            sleep(0.4)  # TODO: only for debugging, remember to remove
            msg = f"packet received: {received_values}"
            if not verbosity != "quiet":
                print(msg)
            logging.info(msg)
        if self.state != "listener_server_stopped":
            self.state = "listener_server_stopped"
        logging.info("receiver loop finished")

    def run(self):
        if self.state == "idle":
            self.state = "listener_server_ready"
        while self.state != "transmitter_client_ready":
            if self.state == "running":
                break
            logging.debug("waiting for transmitter_client_ready")
            sleep(0.5)
        if self.state != "running":
            self.state = "running"
        self.receiver_loop()
        logging.debug(f"{str(self.__class__.__name__)}.run() finished")


"""
============
SERVER CLASS
============
"""


class TransmittingClientClass(Thread, MultiThreadStateCommunicationClass):
    """
    Server Class.
    """

    maximum_num_of_iterations = 1
    server_socket = None
    client_socket_port = None

    def __init__(self,
                 condition: Condition,
                 state: State,
                 socket_port: int,
                 maximum_num_of_iterations: int = 1000):
        """
        Initialisations
        """

        Thread.__init__(self, name="Transmitter")
        MultiThreadStateCommunicationClass.__init__(self, condition, state)
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
        logging.info("starting to transmit")
        while self.state != "listener_server_stopped":
            if kbhit() and getch().decode() == chr(27):  # ESC key pressed
                self.state = "transmitter_client_stopped"
                logging.info(f"ESC key pressed, {str(self.__class__.__name__)} thread flagging listener to stop")
            self.server_socket.sendto(str.encode(str(cnt)), ("localhost", self.client_socket_port))
            if verbosity != "quiet":
                print(f"sending value {cnt}")
            sleep(0.5)  # TODO: only for debugging, remember to remove
            cnt += 1
        logging.info("finished transmitting")

    def run(self):
        if self.state == "idle":
            self.state = "transmitter_client_ready"
        while self.state != "listener_server_ready":
            if self.state == "running":
                break
            logging.debug("waiting for listener_server_ready")
            sleep(0.5)
        if self.state != "running":
            self.state = "running"
        self.transmitter_loop()
        logging.debug(f"{str(self.__class__.__name__)}.run() finished")


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
    state = State(approved_values=["idle",
                                   "transmitter_client_ready",
                                   "listener_server_ready",
                                   "running",
                                   "transmitter_client_stopped",
                                   "listener_server_stopped"])

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
        transmitter = TransmittingClientClass(self.condition, self.state,
                                              self.port, self.maximum_num_of_iterations)
        # transmitter = Thread(name="Transmitter", target=TransmittingClientClass,
        #                      args=(self.condition, self.start_flag, self.stop_flag, self.port, self.maximum_num_of_iterations))
        listener = ListeningServerClass(self.condition, self.state,
                                        self.port, self.buffer_size)
        # listener = Thread(name="Listener", target=ListeningServerClass,
        #                   args=(self.condition, self.start_flag, self.stop_flag, self.port, self.buffer_size))

        transmitter.start()
        listener.start()

        transmitter.join(5)
        listener.join(5)

        logging.debug(f"{str(self.__class__.__name__)}.run() finished running")


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
