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
Element Utilities
"""

__all__ = [
    "incident_types_to_ignore",
    "ignore_incident",
    "ignore_entry",
    "incidents_from_query",
    "terms_from_query",
    "show_closed_from_query",
    "since_days_ago_from_query",
    "since_from_query",
    "num_shifts_from_query",
    "query_value",
]

from datetime import datetime as DateTime, timedelta as TimeDelta

from ims.data import IncidentType



incident_types_to_ignore = set((IncidentType.Junk.value,))



def ignore_incident(incident):
    if incident_types_to_ignore & set(incident.incident_types):
        return True
    return False


def ignore_entry(entry):
    if entry.system_entry:
        return True
    return False


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

    return DateTime.utcnow() - TimeDelta(days=days)


def num_shifts_from_query(request):
    return query_value(request, "num_shifts", "1")


def query_value(request, key, default, no_args_default=None):
    attr_name = "ims_qv_{0}".format(key)

    if not hasattr(request, attr_name):
        if request.args:
            try:
                setattr(request, attr_name, request.args.get(key, [default])[-1])
            except IndexError:
                setattr(request, attr_name, default)
        else:
            if no_args_default is not None:
                setattr(request, attr_name, no_args_default)
            else:
                setattr(request, attr_name, default)

    return getattr(request, attr_name)
