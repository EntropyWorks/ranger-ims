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
Shift Report Element
"""

__all__ = [
    "ShiftReportElement",
]

from datetime import datetime as DateTime, timedelta as TimeDelta

from twisted.python.constants import Names, NamedConstant
from twisted.web.template import renderer

#from ims.data import to_json_text
from ims.dms import DirtShift
from ims.element.base import BaseElement
from ims.element.util import ignore_incident



class Activity(Names):
    created = NamedConstant()
    updated = NamedConstant()
    idle    = NamedConstant()
    closed  = NamedConstant()



class Shift(object):
    @classmethod
    def from_datetime(cls, position, datetime):
        """
        Create a shift from a datetime.

        @param position: a L{Values} container corresponding to the
            position the shift is for.

        @param datetime: a L{DateTime} during the shift.
        """
        return cls(
            position = position,
            date = datetime.date(),
            name = position.shiftForTime(datetime.time()),
        )


    def __init__(self, position, date, time=None, name=None):
        """
        One or both of C{time} and C{name} are required.  If both are
        provided, they must match (meaning C{time == name.value}).

        @param position: a L{Values} container corresponding to the
            position the shift is for.

        @param date: the L{Date} for the shift.

        @param time: the L{Time} for the shift.

        @param name: the L{ValueConstant} from the C{position}
            container corresponding to the time of the shift.
        """
        if time is None:
            if name is None:
                raise ValueError("Both time and name may not be None.")
            else:
                time = name.value

        if name is None:
            name = position.lookupByValue(time)
        elif name.value != time:
            raise ValueError("time and name do not match: {0} != {1}".format(time, name))

        self.position = position
        self.start = DateTime(year=date.year, month=date.month, day=date.day, hour=time.hour)
        self.name = name


    def __hash__(self):
        return hash((self.position, self.name))


    def __eq__(self, other):
        return (
            self.position == other.position and
            self.start == other.start
        )


    def __lt__(self, other): return self.start <  other.start if isinstance(other, Shift) else NotImplemented
    def __le__(self, other): return self.start <= other.start if isinstance(other, Shift) else NotImplemented
    def __gt__(self, other): return self.start >  other.start if isinstance(other, Shift) else NotImplemented
    def __ge__(self, other): return self.start >= other.start if isinstance(other, Shift) else NotImplemented


    def __str__(self):
        return "{self.start} {self.name.name}".format(self=self)


    @property
    def end(self):
        return (self.start.time() + TimeDelta(hours=self.position.length))


    def next_shift(self):
        return self.__class__(
            position = self.position,
            date = self.start.date(),
            time = self.end,
        )


class ShiftReportElement(BaseElement):
    def __init__(self, ims, name):
        BaseElement.__init__(self, ims, name, "Shift Change Report")


    def _index_incidents(self, number_of_shifts=3):
        if not hasattr(self, "_incidents_by_shift"):
            storage = self.ims.storage
            incidents_by_shift = {} #{"created":[], "closed":[]}

            for number, etag in storage.list_incidents():
                incident = storage.read_incident_with_number(number)

                if ignore_incident(incident):
                    continue

                if incident.created:
                    shift = Shift.from_datetime(DirtShift, incident.created)
                    incidents_by_activity = incidents_by_shift.setdefault(shift, {})
                    incidents_by_activity.setdefault(Activity.created, set()).add(incident)

                if incident.closed:
                    shift = Shift.from_datetime(DirtShift, incident.closed)
                    incidents_by_activity = incidents_by_shift.setdefault(shift, {})
                    incidents_by_activity.setdefault(Activity.closed, set()).add(incident)

            open_incidents = set()
            for shift in sorted(incidents_by_shift):
                incidents_by_activity = incidents_by_shift[shift]
                open_incidents |= incidents_by_activity[Activity.created]
                open_incidents -= incidents_by_activity.get(Activity.closed, set())

                incidents_by_activity[Activity.idle] = open_incidents

            self._incidents_by_shift = incidents_by_shift


    @renderer
    def debug(self, request, tag):
        self._index_incidents()

        output = []
        for shift in sorted(self._incidents_by_shift):
            output.append(u"{0}".format(shift))
            incidents_by_activity = self._incidents_by_shift[shift]

            for activity in Activity.iterconstants():
                output.append(u"  {0}".format(activity))

                for incident in sorted(incidents_by_activity.get(activity, [])):
                    number = incident.number
                    summary = incident.summaryFromReport()
                    output.append(u"    {0}: {1}".format(number, summary))

                output.append(u"")
            output.append(u"")

        return u"\n".join(output)
