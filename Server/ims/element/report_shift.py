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

from twisted.python.constants import Names, NamedConstant
from twisted.web.template import renderer, tags

from ims.dms import DirtShift
from ims.data import Shift
from ims.element.base import BaseElement
from ims.element.util import ignore_incident



class Activity(Names):
    created = NamedConstant()
    updated = NamedConstant()
    idle    = NamedConstant()
    closed  = NamedConstant()



class ShiftReportElement(BaseElement):
    def __init__(self, ims, template_name="report_shift"):
        BaseElement.__init__(self, ims, template_name, "Shift Change Report")


    @property
    def incidents_by_shift(self):
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

                for entry in incident.report_entries:
                    shift = Shift.from_datetime(DirtShift, entry.created)
                    incidents_by_activity = incidents_by_shift.setdefault(shift, {})
                    incidents_by_activity.setdefault(Activity.updated, set()).add(incident)

            open_incidents = set()
            for shift in sorted(incidents_by_shift):
                incidents_by_activity = incidents_by_shift[shift]

                created_incidents = incidents_by_activity.get(Activity.created, set())

                open_incidents |= created_incidents
                open_incidents -= incidents_by_activity.get(Activity.closed, set())

                incidents_by_activity[Activity.idle] = open_incidents - created_incidents

            self._incidents_by_shift = incidents_by_shift

        return self._incidents_by_shift


    @renderer
    def debug_activities(self, request, tag):
        output = []
        for shift in sorted(self.incidents_by_shift):
            output.append(u"{0}".format(shift))
            output.append(u"")
            incidents_by_activity = self.incidents_by_shift[shift]

            for activity in Activity.iterconstants():
                output.append(u"  {0}".format(activity))

                for incident in sorted(incidents_by_activity.get(activity, [])):
                    number = incident.number
                    summary = incident.summaryFromReport()
                    output.append(u"    {0}: {1}".format(number, summary))

                output.append(u"")

            output.append(u"")

        return tags.pre(u"\n".join(output))


    @renderer
    def report(self, request, tag):
        shift_elements = []
        for shift in sorted(self.incidents_by_shift):
            element = ShiftElement(self.ims, shift)
            shift_elements.append(element)

        return tag(shift_elements)



class ShiftElement(BaseElement):
    def __init__(self, ims, shift, template_name="shift"):
        BaseElement.__init__(self, ims, template_name, str(shift))
        self.shift_data = shift


    @renderer
    def shift_id(self, request, tag):
        return tag(id="shift_{0}".format(id(self.shift_data)))


    @renderer
    def activity(self, request, tag):
        # Created and still open: (activity = created) - (activity = closed)

        # Carried and updated: (activity = updated) - (activity = created)

        # Carried and idle: (activity = idle)

        # Carried and closed: (activity = closed) - (activity = created)

        # Created and closed: (activity = created) & (activity = closed)
        return "activity goes here"
