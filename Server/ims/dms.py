##
# See the file COPYRIGHT for copyright information.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##

"""
Duty Management System integration.
"""

__all__ = [
    # "DirtShift",
    "DMSError",
    "DatabaseError",
    "DutyManagementSystem",
]

from time import time
# from datetime import time as Time

# from twisted.python.constants import Values, ValueConstant
from twisted.python import log
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.enterprise import adbapi

from ims.data import Ranger



class DMSError(Exception):
    """
    Duty Management System error.
    """



class DatabaseError(DMSError):
    """
    Database error.
    """



# class DirtShift(Values):
#     length = 6

#     Grave     = ValueConstant(Time(hour=length * 0))
#     Morning   = ValueConstant(Time(hour=length * 1))
#     Afternoon = ValueConstant(Time(hour=length * 2))
#     Swing     = ValueConstant(Time(hour=length * 3))


#     @classmethod
#     def shiftForTime(cls, time):
#         if time.hour >= 24:
#             raise ValueError("Hour may not be >= 24: {0!r}".format(time))
#         elif time.hour >= cls.Swing.value.hour:
#             return cls.Swing
#         elif time.hour >= cls.Afternoon.value.hour:
#             return cls.Afternoon
#         elif time.hour >= cls.Morning.value.hour:
#             return cls.Morning
#         elif time.hour >= cls.Grave.value.hour:
#             return cls.Grave
#         else:
#             raise ValueError("Hour must be >= 0: {0!r}".format(time.hour))



class DutyManagementSystem(object):
    """
    Duty Management System

    This class coonects to an external system to get data.
    """
    rangers_cache_interval = 60 * 60 * 1  # 1 hour


    def __init__(self, host, database, username, password):
        """
        @param host: The name of the database host to connect to.
        @type host: L{unicode}

        @param database: The name of the database to access.
        @type database: L{unicode}

        @param username: The user name to use to access the database.
        @type username: L{unicode}

        @param password: The password to use to access the database.
        @type password: L{unicode}
        """
        self.host     = host
        self.database = database
        self.username = username
        self.password = password

        self._rangers_updated = 0


    @property
    def dbpool(self):
        if not hasattr(self, "_dbpool"):
            self._dbpool = adbapi.ConnectionPool(
                "mysql.connector",
                host=self.host,
                database=self.database,
                user=self.username,
                password=self.password,
            )
        return self._dbpool


    @inlineCallbacks
    def rangers(self):
        now = time()

        if now - self.rangers_updated > self.rangers_cache_interval:
            # Mark as updated now so we don't end up performing multiple
            # (redundant) DB queries at the same time.
            self.rangers_updated = now

            try:
                #
                # Ask the Ranger database for a list of Rangers.
                #
                log.msg(
                    "{0} Retrieving Rangers from Duty Management System..."
                    .format(self)
                )

                results = yield self.dbpool.runQuery("""
                    select callsign, first_name, mi, last_name, status
                    from person
                    where status not in (
                        'prospective', 'alpha',
                        'bonked', 'uberbonked',
                        'deceased'
                    )
                """)

                self._rangers = tuple(
                    Ranger(handle, fullName(first, middle, last), status)
                    for handle, first, middle, last, status
                    in results
                )
                self.rangers_updated = time()

            except Exception as e:
                self.rangers_updated = 0
                self._dbpool = None
                raise DatabaseError(e)

        returnValue(self._rangers)


def fullName(first, middle, last):
    values = dict(first=first, middle=middle, last=last)
    if middle:
        return "{first} {middle}. {last}".format(**values)
    else:
        return "{first} {last}".format(**values)
