#!/usr/bin/env python
#
#    Supertree Toolkit. Software for managing and manipulating sources
#    trees ready for supretree construction.
#    Copyright (C) 2011, Jon Hill, Katie Davis
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Jon Hill. jon.hill@imperial.ac.uk. 

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class BibImportError(Error):
    """Exception raised for errors in the input.

    Attributes:
        msg  -- explanation of the error
    """

    def __init__(self, msg):
        self.msg = msg

class MatrixError(Error):
    """Exception raised for errors in the input.

    Attributes:
        msg  -- explanation of the error
    """

    def __init__(self, msg):
        self.msg = msg

class NotUniqueError(Error):
    """Exception raised when source names in
       dataset are not unique. Many funcitons rely on this
       fact

       Attributes:
          msg -- explaination of error
    """

    def __init__(self, msg):
        self.msg = msg

class UnableToParseSubsFile(Error):
    """Exception raised when a subs file fails to parse
       correctly

       Attributes:
          msg -- explaination of error
    """

    def __init__(self, msg):
        self.msg = msg

class InvalidSTKData(Error):
    """Exception raised when a the PHYML is inconsistant

       Attributes:
          msg -- explaination of error
    """

    def __init__(self, msg):
        self.msg = msg

