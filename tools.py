#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2022, Hedi Ziv
"""
Various utility tools commonly used.
"""


from typing import Union
import logging
from os import linesep
from os.path import isfile, split


"""
=========
CONSTANTS
=========
"""


_CONFIG_VERSION = 0.1  # must specify minimal configuration file version here

_DEFAULT_CFG = \
    f"# tools.py configuration file.\n" \
    f"# use # to mark comments.  Note # has to be first character in line.\n" \
    f"\n" \
    f"config_version = {_CONFIG_VERSION}\n" \
    f"\n" \
    f"############################\n" \
    f"# important file locations #\n" \
    f"############################\n" \
    f"# use slash (/) or single back-slash (\\) as path separators.\n" \
    f"\n" \
    f"temp_dir = C:\\tmp"


"""
==================
CONFIG FILE PARSER
==================
"""


class Config:
    """
    Configuration file parser.
    Note all return values in string format.
    """

    _config = {}

    def __init__(self, path: Union[None, str] = None, config_version: float = _CONFIG_VERSION, default_cfg: str = _DEFAULT_CFG):
        """
        Initialisations
        @param path: Path to config file.  Local directory by default
        @param config_version: must specify minimum config file version here
        @param default_cfg: Default CFG
        """

        self.log = logging.getLogger(self.__class__.__name__)
        assert isinstance(config_version, float)
        assert isinstance(default_cfg, str)
        if path is None:
            path = f'./{self.__class__.__name__}.cfg'
            logging.debug(f'Path to configuration file not specified.  Using: {path}')
        else:
            assert isinstance(path, str)
            if isfile(path):
                logging.debug(f'Configuration file detected as {path}')
            else:
                logging.debug(f"Configuration file path specified {path} does not exist, creating default")
                try:
                    with open(path, 'wt') as config_file:
                        config_file.write(default_cfg)
                    config_file.close()
                    logging.debug(f'{path} file created')
                except PermissionError as e:
                    logging.error(f"can not access file {path}. Might be opened by another application. "
                                  f"Error returned: {e}")
                    raise PermissionError(f"can not access file {path}. Might be opened by another application."
                                          f"Error returned: {e}")
                except OSError as e:
                    logging.error(f"can not access file {path}. Might be opened by another application. "
                                  f"Error returned: {e}")
                    raise OSError(f"can not access file {path}. Might be opened by another application."
                                  f"Error returned: {e}")
                except UserWarning as e:
                    logging.debug(f"{path} file empty - {e}")
                    raise UserWarning(f"can not access file {path}. Might be opened by another application. "
                                      f"Error returned: {e}")
        # read file
        try:
            with open(path, 'rt') as config_file:
                for line in config_file:
                    # skip comment or empty lines
                    if not (line.startswith('#') or line.startswith(linesep) or line.startswith('\n')):
                        var_name, var_value = line.split('=')
                        var_name = var_name.strip(' \t\n\r')
                        var_value = var_value.strip(' \t\n\r')
                        if ',' in var_value:
                            self._config[var_name] = [x.strip(' \t\n\r') for x in var_value.split(',')]
                        else:
                            self._config[var_name] = var_value
            config_file.close()
            logging.info(f'Configuration file {path} read.')
            logging.debug('Config file contents:')
            # log config file content
            for key in self._config.keys():
                logging.debug(f"config[{key}] = {self._config[key]}")
            logging.debug('End of Config file content.')
        except PermissionError as e:
            logging.error(f"can not access file {path}. Might be opened by another application. "
                          f"Error returned: {e}")
            raise PermissionError(f"can not access file {path}. Might be opened by another application."
                                  f"Error returned: {e}")
        except OSError as e:
            logging.error(f"can not access file {path}. Might be opened by another application. "
                          f"Error returned: {e}")
            raise OSError(f"can not access file {path}. Might be opened by another application."
                          f"Error returned: {e}")
        except UserWarning as e:
            logging.debug(f"{path} file empty - {e}")
            raise UserWarning(f"can not access file {path}. Might be opened by another application. "
                              f"Error returned: {e}")
        # verify config_version
        file_version = self.__getitem__("config_version")
        fault_msg = f"Config file {split(path)[1]} version ({file_version}) is lower than " \
                    f"expected {config_version}. Consider deleting and re-running code to " \
                    f"generate default config file " \
                    f"with latest version."
        try:
            file_version = float(file_version)
        except ValueError as e:
            logging.error(f"config_version value in file is not a valid float. error: {e}")
        if not isinstance(file_version, (float, int)):
            raise ValueError(fault_msg)
        if file_version < config_version:
            raise ValueError(fault_msg)

    def __del__(self):
        """ Destructor. """

        # destructor content here if required
        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def __getitem__(self, item: str) -> Union[None, str, list]:
        """
        return parameter from configuration file
        @param item: name of parameter
        :return: value of parameter from configuration file
        """
        assert isinstance(item, str)
        ret = None  # by default
        if item in self._config:
            try:
                ret = self._config[item]
            except KeyError as e:
                logging.error(f'parameter requested {item} not in config file, error: {e}')
                ret = None
        else:
            logging.info(f'parameter requested {item} not in config file')
        if ret is not None and isinstance(ret, str) and ret.lower() == 'none':  # turn text none into None
            ret = None
        return ret
