'''
Created on Feb 19, 2016

@author: gur36840
'''

#from neutron.common import exceptions
#from webob import exc



class L2GwMigrationException(Exception):
    """
    Base Neutron Migration Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printed
    with the keyword arguments provided to the constructor.
    """
    message = "An unknown exception occurred"

    def __init__(self, *args, **kwargs):
        super(L2GwMigrationException, self).__init__()
        self._error_string = self.message
        if len(args) > 0:
            args = ["%s" % arg for arg in args]
            self._error_string = (self._error_string +
                                  "\nDetails: %s" % '\n'.join(args))
    def __str__(self):
        return self._error_string


class SwitchNotFound(L2GwMigrationException):
    message = 'Switch not found with given %s'


class InvalidIpAddress(L2GwMigrationException):
    message = 'Invalid ip address'


class UnhandeledException(L2GwMigrationException):
    message = 'Some unexpected error occured'


class DBError(L2GwMigrationException):
    message = "DB Error"


class InvalidControlFile(L2GwMigrationException):
    message = 'Modified control file is invalid'


class InputOutput(L2GwMigrationException):
    message = 'Unable to complete Input/Output operation on file '

class NoMappingFound(L2GwMigrationException):
    message = 'Unable to create binding for all ports'

class ValueError(L2GwMigrationException):
    message = "IP Error"
