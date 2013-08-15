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
Protocol bits
"""

__all__ = [
    "IncidentManagementSystem",
]

from datetime import datetime as DateTime

from twisted.python.zippath import ZipArchive
from twisted.internet.defer import Deferred
from twisted.web import http
from twisted.web.static import File

from klein import Klein

from ims.data import JSON, to_json_text, from_json_io
from ims.data import Incident, ReportEntry, IncidentType
from ims.sauce import url_for, set_response_header
from ims.sauce import http_sauce
from ims.sauce import HeaderName, ContentType
from ims.element.file import FileElement
from ims.element.home import HomePageElement
from ims.element.queue import DispatchQueueElement
from ims.element.incident import IncidentElement
from ims.element.report_daily import DailyReportElement
from ims.element.report_shift import ShiftReportElement
from ims.element.util import incidents_from_query
from ims.util import http_download



class IncidentManagementSystem(object):
    """
    Incident Management System
    """
    app = Klein()

    protocol_version = "0.0"

    def __init__(self, config):
        self.config = config
        self.avatarId = None
        self.storage = config.storage
        self.dms = config.dms


    #
    # JSON endpoints
    #

    @app.route("/ping", methods=("GET",))
    @app.route("/ping/", methods=("GET",))
    @http_sauce
    def ping(self, request):
        ack="ack"
        set_response_header(request, HeaderName.etag, ack)
        set_response_header(request, HeaderName.contentType, ContentType.JSON)
        return to_json_text(ack)


    @app.route("/rangers", methods=("GET",))
    @app.route("/rangers/", methods=("GET",))
    @http_sauce
    def list_rangers(self, request):
        set_response_header(request, HeaderName.etag, str(self.dms.rangers_updated))
        set_response_header(request, HeaderName.contentType, ContentType.JSON)

        d = self.dms.rangers()
        d.addCallback(lambda rangers:
            to_json_text(tuple(
                {
                    "handle": ranger.handle,
                    "name"  : ranger.name,
                    "status": ranger.status,
                }
                for ranger in rangers
            ))
        )

        return d              

    @app.route("/incident_types", methods=("GET",))
    @app.route("/incident_types/", methods=("GET",))
    @http_sauce
    def list_incident_types(self, request):
        #set_response_header(request, HeaderName.etag, "*") # FIXME
        set_response_header(request, HeaderName.contentType, ContentType.JSON)
        return self.config.IncidentTypesJSON


    @app.route("/incidents", methods=("GET",))
    @app.route("/incidents/", methods=("GET",))
    @http_sauce
    def list_incidents(self, request):
        #set_response_header(request, HeaderName.etag, "*") # FIXME
        set_response_header(request, HeaderName.contentType, ContentType.JSON)
        return to_json_text(tuple(incidents_from_query(self, request)))


    @app.route("/incidents/<number>", methods=("GET",))
    @http_sauce
    def get_incident(self, request, number):
        # FIXME: For debugging
        #import time
        #time.sleep(0.3)

        set_response_header(request, HeaderName.etag, self.storage.etag_for_incident_with_number(number))
        set_response_header(request, HeaderName.contentType, ContentType.JSON)

        if False:
            #
            # This is faster, but doesn't benefit from any cleanup or
            # validation code, so it's only OK if we know all data in the
            # store is clean by this server version's standards.
            #
            return self.storage.read_incident_with_number_raw(number)
        else:
            #
            # This parses the data from the store, validates it, then
            # re-serializes it.
            #
            incident = self.storage.read_incident_with_number(number)
            return incident.to_json_text()


    @app.route("/incidents/<number>", methods=("POST",))
    @http_sauce
    def edit_incident(self, request, number):
        number = int(number)
        incident = self.storage.read_incident_with_number(number)

        #
        # Handle the changes requested by the client
        #
        edits_json = from_json_io(request.content)
        edits = Incident.from_json(edits_json, number=number, validate=False)

        user_entries = []

        system_messages = []
        state_changes = []

        def log_edit_value(key, old, new):
            if key is JSON.number:
                return

            if old == new:
                #print "Client submitted unchaged value for {0}: {1}".format(JSON.describe(key), new)
                return

            if key in JSON.states():
                state_changes.append((key, new))
                return

            system_messages.append(u"Changed {0} to: {1}".format(JSON.describe(key), new if new else u"<no value>"))

        def diff_set(key, old, new):
            old = frozenset(old if old else ())
            new = frozenset(new if new else ())
            unchanged = old & new
            removed = old ^ unchanged
            added = new ^ unchanged
            return added, removed

        def log_edit_set(key, added, removed):
            if added:
                system_messages.append(u"Added to {0}: {1}".format(JSON.describe(key), ", ".join(added)))
            if removed:
                system_messages.append(u"Removed from {0}: {1}".format(JSON.describe(key), ", ".join(removed)))

        def close_incident(incident=incident, edits=edits):
            now = DateTime.now()
            for key in (JSON.created, JSON.dispatched, JSON.on_scene, JSON.closed):
                attr_name = key.name

                if (
                    getattr(incident, attr_name) is None and
                    getattr(edits   , attr_name) is None
                ):
                    log_edit_value(key, getattr(incident, attr_name), now)
                    setattr(incident, attr_name, now)

        for key in edits_json.keys():
            key = JSON.lookupByValue(key)

            if key is JSON.report_entries:
                if edits.report_entries is not None:
                    for entry in edits.report_entries:
                        # Edit report entries to add author
                        entry.author = self.avatarId.decode("utf-8")
                        user_entries.append(entry)
            elif key is JSON.location_name:
                if edits.location.name is not None:
                    log_edit_value(key, incident.location.name, edits.location.name)
                    incident.location.name = edits.location.name
            elif key is JSON.location_address:
                if edits.location.address is not None:
                    log_edit_value(key, incident.location.address, edits.location.address)
                    incident.location.address = edits.location.address
            elif key is JSON.ranger_handles:
                if edits.rangers is not None:
                    added, removed = diff_set(key, incident.rangers, edits.rangers)
                    log_edit_set(key, [r.handle for r in added], [r.handle for r in removed])
                    incident.rangers = edits.rangers
            elif key is JSON.incident_types:
                if edits.incident_types is not None:
                    log_edit_set(key, *diff_set(key, incident.incident_types, edits.incident_types))

                    if IncidentType.Junk.value in (frozenset(edits.incident_types) - frozenset(incident.incident_types)):
                        # Junk was added as an incident type; let's close.
                        close_incident()

                    incident.incident_types = edits.incident_types
            else:
                attr_name = key.name
                attr_value = getattr(edits, attr_name)

                if key in (JSON.created, JSON.dispatched, JSON.on_scene, JSON.closed):
                    if edits.created is None:
                        # If created is None, then we aren't editing state.
                        # (It would be weird if others were not None here.)
                        continue
                elif attr_value is None:
                    # None values should not cause edits.
                    continue

                log_edit_value(key, getattr(incident, attr_name), attr_value)

                setattr(incident, attr_name, attr_value)

        #
        # Figure out what to report about state changes
        #
        highest_change = None
        lowest_change = None
        for state_changed, state_time in state_changes:
            if state_time is None:
                if lowest_change is None or JSON.cmpStates(lowest_change, state_changed) > 0:
                    lowest_change = state_changed
            else:
                if highest_change is None or JSON.cmpStates(highest_change[0], state_changed) < 0:
                    highest_change = (state_changed, state_time)

        if highest_change is not None:
            system_messages.append(u"State changed to: {0}".format(JSON.describe(highest_change[0])))
        elif lowest_change is not None:
            # We need one state less than lowest_change
            last = None
            for state in JSON.states():
                if state == lowest_change:
                    break
                last = state
            system_messages.append(u"State changed to: {0}".format(JSON.describe(last)))

        #
        # Add system report entries, then user entries
        #
        if system_messages:
            incident.report_entries.append(
                ReportEntry(
                    author = self.avatarId.decode("utf-8"),
                    text = u"\n".join(system_messages),
                    system_entry = True,
                )
            )
        incident.report_entries.extend(user_entries)

        #
        # Write to disk
        #
        self.storage.write_incident(incident)

        #
        # Respond
        #
        set_response_header(request, HeaderName.contentType, ContentType.JSON)
        request.setResponseCode(http.OK)

        return "";


    @app.route("/incidents/", methods=("POST",))
    @http_sauce
    def new_incident(self, request):
        incident = Incident.from_json_io(request.content, number=self.storage.next_incident_number())

        # Edit report entrys to add author
        for entry in incident.report_entries:
            entry.author = self.avatarId.decode("utf-8")

        self.storage.write_incident(incident)

        request.setResponseCode(http.CREATED)

        request.setHeader(
            HeaderName.incidentNumber.value,
            incident.number
        )
        request.setHeader(
            HeaderName.location.value,
            url_for(request, "get_incident", {"number": incident.number})
        )

        return "";


    #
    # Web UI
    #

    @app.route("/queue", methods=("GET",))
    @app.route("/queue/", methods=("GET",))
    @http_sauce
    def dispatchQueue(self, request):
        if not request.args:
            request.args["show_closed"] = ["false"]

        set_response_header(request, HeaderName.contentType, ContentType.HTML)
        return DispatchQueueElement(self)


    @app.route("/queue/incidents/<number>", methods=("GET",))
    @http_sauce
    def queue_incident(self, request, number):
        set_response_header(request, HeaderName.contentType, ContentType.HTML)
        return IncidentElement(self, number)


    #
    # Resources
    #

    @app.route("/resources", methods=("GET",))
    @app.route("/resources/", methods=("GET",), branch=True)
    @http_sauce
    def favicon(self, request):
        return File(self.config.Resources.path)


    #
    # Documentation
    #

    @app.route("/", methods=("GET",))
    @http_sauce
    def root(self, request):
        set_response_header(request, HeaderName.contentType, ContentType.HTML)
        return HomePageElement(self)


    @app.route("/docs", methods=("GET",))
    @app.route("/docs/", methods=("GET",))
    @http_sauce
    def doc_index(self, request):
        return self.doc_with_name(request, "index.xhtml")


    @app.route("/docs/<name>", methods=("GET",))
    @http_sauce
    def doc_with_name(self, request, name):
        filePath = self.config.Resources.child("docs").child(name)

        if filePath.exists():
            if name.endswith(".xhtml"):
                set_response_header(request, HeaderName.contentType, ContentType.HTML)
                return FileElement(filePath)

        request.setResponseCode(http.NOT_FOUND)
        set_response_header(request, HeaderName.contentType, ContentType.plain)
        return "Not found."


    #
    # Reports
    #

    @app.route("/reports/daily", methods=("GET",))
    @http_sauce
    def daily_report(self, request):
        set_response_header(request, HeaderName.contentType, ContentType.HTML)
        return DailyReportElement(self)


    @app.route("/charts/daily", methods=("GET",))
    @http_sauce
    def daily_chart(self, request):
        set_response_header(request, HeaderName.contentType, ContentType.HTML)
        return DailyReportElement(self, template_name="chart_daily")


    @app.route("/reports/shift", methods=("GET",))
    @http_sauce
    def shift_report(self, request):
        set_response_header(request, HeaderName.contentType, ContentType.HTML)
        return ShiftReportElement(self)


    #
    # Links
    #

    @app.route("/links", methods=("GET",))
    @app.route("/links/", methods=("GET",))
    @http_sauce
    def links(self, request):
        #set_response_header(request, HeaderName.etag, ????)
        set_response_header(request, HeaderName.contentType, ContentType.JSON)
        return to_json_text([
            { JSON.name.value: name, JSON.url.value: value }
            for name, value in (
                ( "Home page"                     , "/"              ),
                ( "Dispatch Queue"                , "/queue"         ),
                ( "Daily Incident Summary (Table)", "/reports/daily" ),
                ( "Daily Incident Summary (Chart)", "/charts/daily"  ),
            )
        ])


    #
    # Baseline
    #

    @app.route("/baseline/<container>/<name>", methods=("GET",))
    @http_sauce
    def baseline(self, request, container, name):
        # See http://baselinecss.com/
        return self.cachedZipResource(
            request,
            "_baseline",
            "http://baselinecss.com/download/baseline.zip",
            ("baseline.0.5.3", "css", container, name)
        )


    #
    # JQuery resources
    #

    @app.route("/jquery.js", methods=("GET",))
    @http_sauce
    def jquery(self, request):
        version = "jquery-1.10.2.min.js"
        url = "http://code.jquery.com/"+version
        return self.cachedResource(version, url)


    @app.route("/jquery-1.10.2.min.map", methods=("GET",))
    @http_sauce
    def jquery_map(self, request):
        name = "jquery-1.10.2.min.map"
        url = "http://code.jquery.com/"+name
        return self.cachedResource(name, url)


    @app.route("/tidy.js", methods=("GET",))
    @http_sauce
    def tidy(self, request):
        name = "tidy.js"
        url = "https://raw.github.com/nuxy/Tidy-Table/v1.4/jquery.tidy.table.min.js"
        return self.cachedResource(name, url)


    @app.route("/tidy.css", methods=("GET",))
    @http_sauce
    def tidy_css(self, request):
        name = "tidy.css"
        url = "https://raw.github.com/nuxy/Tidy-Table/v1.4/jquery.tidy.table.min.css"
        return self.cachedResource(name, url)


    @app.route("/images/arrow_asc.gif", methods=("GET",))
    @http_sauce
    def tidy_asc(self, request):
        name = "tidy-asc.gif"
        url = "https://raw.github.com/nuxy/Tidy-Table/v1.4/images/arrow_asc.gif"
        return self.cachedResource(name, url)


    @app.route("/images/arrow_desc.gif", methods=("GET",))
    @http_sauce
    def tidy_desc(self, request):
        name = "tidy-desc.gif"
        url = "https://raw.github.com/nuxy/Tidy-Table/v1.4/images/arrow_desc.gif"
        return self.cachedResource(name, url)


    #
    # Flot
    #

    @app.route("/flot/<name>", methods=("GET",))
    @http_sauce
    def flot(self, request, name):
        # See http://www.flotcharts.org/
        which = "flot-0.8.1"
        return self.cachedZipResource(
            request,
            "_{0}".format(which),
            "http://www.flotcharts.org/downloads/{0}.zip".format(which),
            ("flot", name)
        )


    #
    # Utilities
    #

    def cachedResource(self, name, url):
        name = "_{0}".format(name)
        filePath = self.config.Resources.child(name)

        if filePath.exists():
            return File(filePath.path)

        d = http_download(filePath, url)
        d.addCallback(lambda _: File(filePath.path))
        return d


    def cachedZipResource(self, request, name, url, segments):
        archivePath = self.config.Resources.child("{0}.zip".format(name))

        if archivePath.exists():
            d = Deferred()
            d.callback(None)
        else:
            d = http_download(archivePath, url)

        def readFromArchive(_):
            filePath = ZipArchive(archivePath.path)
            for segment in segments:
                filePath = filePath.child(segment)
            return filePath.getContent()

        def notFoundHandler(f):
            f.trap(KeyError)
            request.setResponseCode(http.NOT_FOUND)
            set_response_header(request, HeaderName.contentType, ContentType.plain)
            return "Not found."

        d.addCallback(readFromArchive)
        d.addErrback(notFoundHandler)
        return d
