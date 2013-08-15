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
Incident Element
"""

__all__ = [
    "IncidentElement",
]

from twisted.web.template import renderer

from ims.element.base import BaseElement



class IncidentElement(BaseElement):
    def __init__(self, ims, number):
        BaseElement.__init__(self, ims, "incident", "Incident #{0}".format(number))
        self.incident = self.ims.storage.read_incident_with_number(number)

        for attr_name in (
            "number",
            "priority",
            "created",
            "dispatched",
            "on_scene",
            "closed",
            "summary",
        ):
            @renderer
            def render_attr(request, tag, attr_name=attr_name):
                return tag(u"{0}".format(getattr(self.incident, attr_name)))

            setattr(self, attr_name, render_attr)

    @renderer
    def state_selected(self, request, tag):
        return tag # FIXME


    @renderer
    def priority_selected(self, request, tag):
        return tag # FIXME


    @renderer
    def summary_value(self, request, tag):
        return tag(value=u"{0}".format(self.incident.summary))


    @renderer
    def location_name_value(self, request, tag):
        return tag(value=u"{0}".format(self.incident.location.name))


    @renderer
    def location_address_value(self, request, tag):
        return tag(value=u"{0}".format(self.incident.location.address))
