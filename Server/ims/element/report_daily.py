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
Daily Report Element
"""

__all__ = [
    "DailyReportElement",
]

from datetime import timedelta as TimeDelta

from twisted.python import log
from twisted.web.template import renderer

from ims.data import to_json_text
from ims.element.base import BaseElement
from ims.element.util import ignore_incident



class DailyReportElement(BaseElement):
    def __init__(self, ims, template_name):
        BaseElement.__init__(self, ims, template_name, "Daily Report")


    def _index_incidents(self, start_hour=12):
        if not hasattr(self, "_incidents_by_date") or not hasattr(self, "_incidents_by_type"):
            storage = self.ims.storage
            incidents_by_date = {}
            incidents_by_type = {}

            def dates_from_incident(incident):
                dates = set()

                def add_date(dt, dates=dates):
                    if dt is None:
                        return

                    if dt.hour < start_hour:
                        dates.add(dt.date() - TimeDelta(days=1))
                    else:
                        dates.add(dt.date())

                for entry in incident.report_entries:
                    add_date(entry.created)

                add_date(incident.created)
                add_date(incident.dispatched)
                add_date(incident.on_scene)
                add_date(incident.closed)

                return dates

            for number, etag in storage.list_incidents():
                incident = storage.read_incident_with_number(number)

                if ignore_incident(incident):
                    continue

                for date in dates_from_incident(incident):
                    incidents_by_date.setdefault(date, set()).add(incident)

                if incident.incident_types:
                    for incident_type in incident.incident_types:
                        incidents_by_type.setdefault(incident_type, set()).add(incident)
                else:
                    incidents_by_type.setdefault("(unclassified)", set()).add(incident)

            self._incidents_by_date = incidents_by_date
            self._incidents_by_type = incidents_by_type


    def incidents_by_date(self):
        self._index_incidents()
        return self._incidents_by_date


    def incidents_by_type(self):
        self._index_incidents()
        return self._incidents_by_type


    @renderer
    def tableColumns(self, request, tag):
        return to_json_text(
            ["Type"] +
            [
                date.strftime("%a %m/%d")
                for date in sorted(self.incidents_by_date())
            ] +
            ["Total"]
        )


    @renderer
    def tableData(self, request, tag):
        return self.data(labels=True, totals=True)


    @renderer
    def chartData(self, request, tag):
        return self.data()


    def data(self, labels=False, totals=False):
        rows = []

        incidents_by_type = self.incidents_by_type()
        incidents_by_date = self.incidents_by_date()

        for incident_type in sorted(incidents_by_type):
            if labels:
                row = [incident_type]
            else:
                row = []

            seen = set()

            for date in sorted(incidents_by_date):
                incidents = incidents_by_type[incident_type] & incidents_by_date[date]
                seen |= incidents
                row.append("{0}".format(len(incidents)))
                #row.append("{0} ({1})".format(len(incidents), ",".join((str(i.number) for i in incidents))))

            row.append(len(incidents_by_type[incident_type]))

            unseen = incidents_by_type[incident_type] - seen

            if unseen:
                log.msg("ERROR: No date for some {0} incidents (!?): {1}".format(incident_type, unseen))

            rows.append(row)

        if totals:
            row = ["Total"]
            seen = set()
            for date in sorted(incidents_by_date):
                incidents = incidents_by_date[date]
                seen |= incidents
                row.append(len(incidents))
            row.append(len(seen))
            rows.append(row)

        return to_json_text(rows)
