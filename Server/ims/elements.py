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
XHTML Elements
"""

__all__ = [
    "HomePageElement",
    "DispatchQueueElement",
    "incidents_from_query",
]

from datetime import datetime, timedelta

from twisted.web.template import Element, renderer
from twisted.web.template import XMLFile

from ims.data import to_json_text



class BaseElement(Element):
    def __init__(self, ims, name, title):
        self.ims = ims
        self._title = title

        self.loader = XMLFile(ims.config.Resources.child(name+".xhtml"))


    @renderer
    def title(self, request, tag):
        return tag(self._title)



class HomePageElement(BaseElement):
    def __init__(self, ims):
        BaseElement.__init__(self, ims, "home", "Ranger Incident Management System")



class DispatchQueueElement(BaseElement):
    def __init__(self, ims):
        BaseElement.__init__(self, ims, "queue", "Dispatch Queue")


    @renderer
    def columns(self, request, tag):
        return to_json_text([
            "Number",
            "Priority",
            "Created", "Dispatched", "On Scene", "Closed",
            "Rangers",
            "Location",
            "Type",
            "Description"
        ])


    @renderer
    def data(self, request, tag):
        def format_date(d):
            if d is None:
                return ""
            else:
                return d.strftime("%a.%H:%M")

        data = []

        for number, etag in incidents_from_query(self.ims, request):
            incident = self.ims.storage.read_incident_with_number(number)

            if incident.summary:
                summary = incident.summary
            elif incident.report_entries:
                for entry in incident.report_entries:
                    if not entry.system_entry:
                        summary = entry.text
                        break
            else:
                summary = ""

            data.append([
                incident.number,
                incident.priority,
                format_date(incident.created),
                format_date(incident.dispatched),
                format_date(incident.on_scene),
                format_date(incident.closed),
                ", ".join(ranger.handle for ranger in incident.rangers),
                str(incident.location),
                ", ".join(incident.incident_types),
                summary,
            ])

        return to_json_text(data)


    @renderer
    def hide_closed_column(self, request, tag):
        if show_closed_from_query(request):
            return tag
        else:
            return "$('td:nth-child(6),th:nth-child(6)').hide();"


    @renderer
    def search_value(self, request, tag):
        terms = terms_from_query(request)
        if terms:
            return tag(value=" ".join(terms))
        else:
            return tag


    @renderer
    def show_closed_value(self, request, tag):
        if show_closed_from_query(request):
            return tag(value="true")
        else:
            return tag(value="false")


    @renderer
    def show_closed_checked(self, request, tag):
        if show_closed_from_query(request):
            return tag(checked="")
        else:
            return tag


    @renderer
    def since_days_ago_selected(self, request, tag):
        if tag.attributes["value"] == since_days_ago_from_query(request):
            return tag(selected="")
        else:
            return tag;



class DailyReportElement(BaseElement):
    def __init__(self, ims):
        BaseElement.__init__(self, ims, "report_daily", "Daily Report")


    def incidents_by_date(self):
        if not hasattr(self, "_incidents_by_date"):
            storage = self.ims.storage
            incidents_by_date = {}

            for number, etag in storage.list_incidents():
                incident = storage.read_incident_with_number(number)

                for entry in incident.report_entries:
                    created = entry.created
                    if created.hour < 12:
                        date = created.date() - timedelta(days=1)
                    else:
                        date = created.date()

                    incidents_by_date.setdefault(date, set()).add(incident)

            self._incidents_by_date = incidents_by_date

        return self._incidents_by_date


    @renderer
    def columns(self, request, tag):
        return to_json_text(["Type"] + [
            date.strftime("%a %b %d")
            for date in self.incidents_by_date()
        ])


    @renderer
    def data(self, request, tag):
        data = []

        return to_json_text(data)



def incidents_from_query(ims, request):
    if not hasattr(request, "ims_incidents"):
        if request.args:
            request.ims_incidents = ims.storage.search_incidents(
                terms = terms_from_query(request),
                show_closed = show_closed_from_query(request),
                since = since_from_query(request),
            )
        else:
            request.ims_incidents = ims.storage.list_incidents()

    return request.ims_incidents


def terms_from_query(request):
    if not hasattr(request, "ims_terms"):
        if request.args:
            terms = set()

            for query in request.args.get("search", []):
                for term in query.split(" "):
                    terms.add(term)

            for term in request.args.get("term", []):
                terms.add(term)

            request.ims_terms = terms

        else:
            request.ims_terms = set()

    return request.ims_terms


def show_closed_from_query(request):
    return query_value(request, "show_closed", "false", "true") == "true"


def since_days_ago_from_query(request):
    return query_value(request, "since_days_ago", "0")


def since_from_query(request):
    try:
        days = int(since_days_ago_from_query(request))
    except ValueError:
        days = 0

    if not days:
        return None

    return datetime.utcnow() - timedelta(days=days)


def query_value(request, key, default, no_args_default=None):
    attr_name = "ims_qv_{0}".format(key)

    if not hasattr(request, attr_name):
        if request.args:
            try:
                setattr(request, attr_name, request.args.get(key, [default])[-1])
                print "found", key
            except IndexError:
                setattr(request, attr_name, default)
                print "index error"
        else:
            if no_args_default is not None:
                setattr(request, attr_name, no_args_default)
                print "no args default"
            else:
                setattr(request, attr_name, default)
                print "no args"

    print attr_name, repr(getattr(request, attr_name))
    return getattr(request, attr_name)
