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
]

from twisted.web.template import Element, renderer
from twisted.web.template import XMLFile



class BaseElement(Element):
    def __init__(self, ims, name, title):
        self.ims = ims
        self._title = title

        self.loader = XMLFile(ims.config.Resources.child(name+".xhtml"))


    @renderer
    def title(self, request, tag):
        return self._title



class HomePageElement(BaseElement):
    def __init__(self, ims):
        BaseElement.__init__(self, ims, "home", "Ranger Incident Management System")



class DispatchQueueElement(BaseElement):
    def __init__(self, ims):
        BaseElement.__init__(self, ims, "queue", "Dispatch Queue")
