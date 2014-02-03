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
Data model
"""

__all__ = [
    "JSON",
    "IncidentType",
    "InvalidDataError",
    "Incident",
    "ReportEntry",
    "Ranger",
    "Location",
    # "Shift",
    "to_json_text",
    "from_json_io",
    "from_json_text",
]

from datetime import datetime as DateTime  # , timedelta as TimeDelta
from json import dumps, load as from_json_io, loads as from_json_text

from twisted.python.constants import Values, ValueConstant

rfc3339_date_time_format = "%Y-%m-%dT%H:%M:%SZ"



class JSON(Values):
    number           = ValueConstant("number")
    priority         = ValueConstant("priority")
    summary          = ValueConstant("summary")
    location_name    = ValueConstant("location_name")
    location_address = ValueConstant("location_address")
    ranger_handles   = ValueConstant("ranger_handles")
    incident_types   = ValueConstant("incident_types")
    report_entries   = ValueConstant("report_entries")
    author           = ValueConstant("author")
    text             = ValueConstant("text")
    system_entry     = ValueConstant("system_entry")
    created          = ValueConstant("created")
    dispatched       = ValueConstant("dispatched")
    on_scene         = ValueConstant("on_scene")
    closed           = ValueConstant("closed")
    name             = ValueConstant("name")
    url              = ValueConstant("url")


    @classmethod
    def states(cls):
        """
        List the constants that are states names.

        @return: All incident state names.
        @rtype: iterable of L{ValueConstant}
        """
        if not hasattr(cls, "_states"):
            cls._states = (
                cls.created,
                cls.dispatched,
                cls.on_scene,
                cls.closed,
            )
        return cls._states


    @classmethod
    def cmpStates(cls, a, b):
        """
        Compare two states for ordering purposes.

        @param a: A JSON state name.
        @type a: L{ValueConstant}

        @param b: A JSON state name.
        @type b: L{ValueConstant}

        @return: An number that is negative if C{a < b}, zero if C{a == b}, and
            positive if C{a > b}.
        @rtype: L{int}
        """
        assert isinstance(a, ValueConstant), "a"
        assert isinstance(b, ValueConstant), "b"

        if not hasattr(cls, "_stateIndexes"):
            states = cls.states()
            cls._stateIndexes = dict(zip(states, xrange(0, len(states))))
        return cmp(cls._stateIndexes[a], cls._stateIndexes[b])


    @classmethod
    def describe(cls, value):
        """
        Describe a constant as a human-readable string.

        @param value: A JSON constant.
        @type constant: L{ValueConstant}

        @return: A string description of C{value}.
        @rtype: L{unicode}
        """
        return {
            cls.created: u"new",
        }.get(value, value.name.replace("_", " ").decode("utf-8"))



class IncidentType(Values):
    """
    Non-exhautive set of constants for incident types; only incident types
    known to the software need to be here.
    """
    Admin = ValueConstant(u"Admin")
    Junk  = ValueConstant(u"Junk")



class InvalidDataError(ValueError):
    """
    Invalid data
    """



class Incident(object):
    """
    Incident
    """

    @classmethod
    def from_json_text(cls, text, number=None, validate=True):
        """
        Create an incident from JSON text.

        @param text: JSON text describing an incident.
        @type text: L{unicode}

        @param number: The number of the incident.
            If C{number} is not C{None} and C{text} includes an incident number
            that is different than C{number}, raise an L{InvalidDataError}.
        @type number: L{int}

        @param validate: If true, raise L{InvalidDataError} is the data does
            not validate as a fully-well-formed incident.
        @type validate: L{bool}
        """
        root = from_json_text(text)
        return cls.from_json(root, number, validate)


    @classmethod
    def from_json_io(cls, io, number=None, validate=True):
        """
        Create an incident from a file.

        @param io: An open file containing JSON text.
        @type io: A file-like object with a C{read} method that returns UTF-8
            L{bytes}.

        @param number: The number of the incident.
            If C{number} is not C{None} and C{text} includes an incident number
            that is different than C{number}, raise an L{InvalidDataError}.
        @type number: L{int}

        @param validate: If true, raise L{InvalidDataError} is the data does
            not validate as a fully-well-formed incident.
        @type validate: L{bool}
        """
        root = from_json_io(io)
        return cls.from_json(root, number, validate)


    @classmethod
    def from_json(cls, root, number=None, validate=True):
        """
        Create an incident from a JSON object graph.

        @param root: A JSON object graph.
        @type root: L{dict}

        @param number: The number of the incident.
            If C{number} is not C{None} and C{text} includes an incident number
            that is different than C{number}, raise an L{InvalidDataError}.
        @type number: L{int}

        @param validate: If true, raise L{InvalidDataError} is the data does
            not validate as a fully-well-formed incident.
        @type validate: L{bool}
        """
        if number is None:
            raise TypeError("Incident number may not be null")
        else:
            number = int(number)

        json_number = root.get(JSON.number.value, None)

        if json_number is not None:
            if json_number != number:
                raise InvalidDataError(
                    "Incident number may not be modified: {0} != {1}"
                    .format(json_number, number)
                )

            root[JSON.number.value] = number

        if type(root) is not dict:
            raise InvalidDataError("JSON incident must be a dict")

        def parse_date(rfc3339):
            if not rfc3339:
                return None
            else:
                return DateTime.strptime(rfc3339, rfc3339_date_time_format)

        location = Location(
            name=root.get(JSON.location_name.value, None),
            address=root.get(JSON.location_address.value, None),
        )

        ranger_handles = root.get(JSON.ranger_handles.value, None)
        if ranger_handles is None:
            rangers = None
        else:
            rangers = [
                Ranger(handle, None, None)
                for handle in ranger_handles
            ]

        report_entries = [
            ReportEntry(
                author=entry.get(JSON.author.value, u"<unknown>"),
                text=entry.get(JSON.text.value, None),
                created=parse_date(entry.get(JSON.created.value, None)),
                system_entry=entry.get(JSON.system_entry.value, False),
            )
            for entry in root.get(JSON.report_entries.value, ())
        ]

        incident = cls(
            number=number,
            priority=root.get(JSON.priority.value, None),
            summary=root.get(JSON.summary.value, None),
            location=location,
            rangers=rangers,
            incident_types=root.get(JSON.incident_types.value, None),
            report_entries=report_entries,
            created=parse_date(root.get(JSON.created.value, None)),
            dispatched=parse_date(root.get(JSON.dispatched.value, None)),
            on_scene=parse_date(root.get(JSON.on_scene.value, None)),
            closed=parse_date(root.get(JSON.closed.value, None)),
        )

        if validate:
            incident.validate()

        return incident


    def __init__(
        self,
        number,
        rangers=(),
        location=None,
        incident_types=(),
        summary=None, report_entries=None,
        created=None, dispatched=None, on_scene=None, closed=None,
        priority=None,
    ):
        """
        @param number: The incident's identifying number.
        @type number: L{int}

        @param rangers: The Rangers associated with the incident.
        @type rangers: iterable of L{Ranger}

        @param location: The location associated with the incident.
        @type location: L{Location}

        @param incident_types: The incident types associated with the incident.
        @type incident_types: iterable of L{unicode}

        @param summary: The incident's summary.
        @type summary: L{unicode}

        @param report_entries: The report entries associated with the incident.
        @type report_entries: iterable of L{ReportEntry}

        @param created: The created time for the incident.
        @type created: L{DateTime}

        @param dispatched: The dispatch time for the incident.
        @type dispatched: L{DateTime}

        @param on_scene: The on scene time for the incident.
        @type on_scene: L{DateTime}

        @param closed: The closed time for the incident.
        @type closed: L{DateTime}

        @param priority: The priority for the incident.
        @type priority: L{int}
        """

        if type(number) is not int:
            raise InvalidDataError(
                "Incident number must be an int, not "
                "({n.__class__.__name__}){n}"
                .format(n=number)
            )

        if number < 0:
            raise InvalidDataError(
                "Incident number but be natural, not {n}".format(n=number)
            )

        if rangers is not None:
            rangers = list(rangers)

        if incident_types is not None:
            incident_types = list(incident_types)

        if report_entries is not None:
            report_entries = list(report_entries)

        if priority is None:
            priority = 5

        self.number         = number
        self.rangers        = rangers
        self.location       = location
        self.incident_types = incident_types
        self.summary        = summary
        self.report_entries = report_entries
        self.created        = created
        self.dispatched     = dispatched
        self.on_scene       = on_scene
        self.closed         = closed
        self.priority       = priority


    def __str__(self):
        return (
            u"{self.number}: {summary}"
            .format(self=self, summary=self.summaryFromReport())
            .encode("utf-8")
        )


    def __repr__(self):
        return (
            "{self.__class__.__name__}("
            "number={self.number!r},"
            "rangers={self.rangers!r},"
            "location={self.location!r},"
            "incident_types={self.incident_types!r},"
            "summary={self.summary!r},"
            "report_entries={self.report_entries!r},"
            "created={self.created!r},"
            "dispatched={self.dispatched!r},"
            "on_scene={self.on_scene!r},"
            "closed={self.closed!r},"
            "priority={self.priority!r})"
            .format(self=self)
        )


    def __hash__(self):
        return hash((
            self.number,
            tuple(self.rangers),
            self.location,
            tuple(self.incident_types),
            self.summary,
            tuple(self.report_entries),
            self.created,
            self.dispatched,
            self.on_scene,
            self.closed,
            self.priority,
        ))


    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.number == other.number and
                self.rangers == other.rangers and
                self.location == other.location and
                self.incident_types == other.incident_types and
                self.summary == other.summary and
                self.report_entries == other.report_entries and
                self.created == other.created and
                self.dispatched == other.dispatched and
                self.on_scene == other.on_scene and
                self.closed == other.closed and
                self.priority == other.priority
            )
        else:
            return NotImplemented


    def __lt__(self, other):
        if not isinstance(other, Incident):
            return NotImplemented
        return self.number < other.number


    def __le__(self, other):
        if not isinstance(other, Incident):
            return NotImplemented
        return self.number <= other.number


    def __gt__(self, other):
        if not isinstance(other, Incident):
            return NotImplemented
        return self.number > other.number


    def __ge__(self, other):
        if not isinstance(other, Incident):
            return NotImplemented
        return self.number >= other.number


    def summaryFromReport(self):
        """
        Generate a summary.  This uses the C{summary} attribute if it is not
        C{None} or empty; otherwise, it uses the first line of the first
        report entry,

        @return: The incident summary.
        @rtype: L{unicode}
        """
        if self.summary:
            return self.summary

        for entry in self.report_entries:
            return entry.text.split("\n")[0]

        return ""


    def validate(self):
        """
        Validate this incident.

        @raise: L{InvalidDataError} if the incident does not validate.
        """
        if self.rangers is None:
            raise InvalidDataError("Rangers may not be None.")

        for ranger in self.rangers:
            ranger.validate()

        if self.location is not None:
            self.location.validate()

        if self.incident_types is not None:
            for incident_type in self.incident_types:
                if type(incident_type) is not unicode:
                    raise InvalidDataError(
                        "Incident type must be unicode, not {0!r}"
                        .format(incident_type)
                    )

        if (
            self.summary is not None and
            type(self.summary) is not unicode
        ):
            raise InvalidDataError(
                "Incident summary must be unicode, not {0!r}"
                .format(self.summary)
            )

        if self.report_entries is not None:
            for report_entry in self.report_entries:
                report_entry.validate()

        if (
            self.created is not None and
            type(self.created) is not DateTime
        ):
            raise InvalidDataError(
                "Incident created date must be a DateTime, not {0!r}"
                .format(self.created)
            )

        if (
            self.dispatched is not None and
            type(self.dispatched) is not DateTime
        ):
            raise InvalidDataError(
                "Incident dispatched date must be a DateTime, not {0!r}"
                .format(self.dispatched)
            )

        if (
            self.on_scene is not None and
            type(self.on_scene) is not DateTime
        ):
            raise InvalidDataError(
                "Incident on_scene date must be a DateTime, not {0!r}"
                .format(self.on_scene)
            )

        if (
            self.closed is not None and
            type(self.closed) is not DateTime
        ):
            raise InvalidDataError(
                "Incident closed date must be a DateTime, not {0!r}"
                .format(self.closed)
            )

        if type(self.priority) is not int:
            raise InvalidDataError(
                "Incident priority must be an int, not {0!r}"
                .format(self.priority)
            )

        if not 1 <= self.priority <= 5:
            raise InvalidDataError(
                "Incident priority must be an int from 1 to 5, not {0!r}"
                .format(self.priority)
            )

        return self


    def to_json_text(self):
        """
        Generate JSON text from this incident.

        @return: JSON text describing this incident.
        @rtype: L{unicode}
        """

        root = {}

        def render_date(date_time):
            if not date_time:
                return None
            else:
                return date_time.strftime(rfc3339_date_time_format)

        if self.incident_types is None:
            incident_types = ()
        else:
            incident_types = self.incident_types

        root[JSON.number.value] = self.number
        root[JSON.priority.value] = self.priority
        root[JSON.summary.value] = self.summary
        root[JSON.location_name.value] = self.location.name
        root[JSON.location_address.value] = self.location.address
        root[JSON.incident_types.value] = incident_types

        root[JSON.created.value] = render_date(self.created)
        root[JSON.dispatched.value] = render_date(self.dispatched)
        root[JSON.on_scene.value] = render_date(self.on_scene)
        root[JSON.closed.value] = render_date(self.closed)

        root[JSON.ranger_handles.value] = [
            ranger.handle for ranger in self.rangers
        ]

        root[JSON.report_entries.value] = [
            {
                JSON.author.value: entry.author,
                JSON.text.value: entry.text,
                JSON.created.value: render_date(entry.created),
                JSON.system_entry.value: entry.system_entry,
            }
            for entry in self.report_entries
        ]

        try:
            return to_json_text(root)
        except TypeError:
            raise AssertionError(
                "{0!r}.to_json_text() generated unserializable data: {1!r}"
                .format(self.__class__.__name__, root)
            )



class ReportEntry(object):
    """
    Report entry
    """

    def __init__(self, author, text, created=None, system_entry=False):
        """
        @param author: The person who created/entered the entry.
        @type author: L{unicode}

        @param text: The report entry text.
        @type text: L{unicode}

        @param created: The created time of the report entry.
        @type created: L{DateTime}

        @param system_entry: Whether the report entry was created by the
            IMS software (as opposed to by a user).
        @type system_entry: L{bool}
        """
        if created is None:
            created = DateTime.utcnow()

        self.author       = author
        self.text         = text
        self.created      = created
        self.system_entry = bool(system_entry)


    def __str__(self):
        if self.system_entry:
            prefix = u"*"
        else:
            prefix = u""

        return (
            u"{prefix}{self.author}@{self.created}: {self.text}"
            .format(self=self, prefix=prefix)
            .encode("utf-8")
        )


    def __repr__(self):
        if self.system_entry:
            star = "*"
        else:
            star = ""

        return (
            "{self.__class__.__name__}("
            "author={self.author!r}{star},"
            "text={self.text!r},"
            "created={self.created!r})"
            .format(self=self, star=star)
        )


    def __hash__(self):
        return hash((
            self.author,
            self.text,
            self.created,
            self.system_entry,
        ))


    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.author == other.author and
                self.text == other.text and
                self.created == other.created and
                self.system_entry == other.system_entry
            )
        else:
            return NotImplemented


    def validate(self):
        """
        Validate this report entry.

        @raise: L{InvalidDataError} if the report entry does not validate.
        """
        if self.author is not None and type(self.author) is not unicode:
            raise InvalidDataError(
                "Report entry author must be unicode, not {0!r}"
                .format(self.author)
            )

        if type(self.text) is not unicode:
            raise InvalidDataError(
                "Report entry text must be unicode, not {0!r}"
                .format(self.text)
            )

        if type(self.created) is not DateTime:
            raise InvalidDataError(
                "Report entry created date must be a DateTime, not {0!r}"
                .format(self.created)
            )



class Ranger(object):
    """
    Ranger
    """

    def __init__(self, handle, name, status):
        """
        @param handle: The Ranger's handle.
        @type handle: L{unicode}

        @param name: The Ranger's name.
        @type name: L{unicode}

        @param status: The Ranger's status.
        @type status: L{unicode}
        """

        if not handle:
            raise InvalidDataError("Ranger handle required.")

        self.handle = handle
        self.name   = name
        self.status = status


    def __str__(self):
        return (
            u"{self.handle} ({self.name})"
            .format(self=self).encode("utf-8")
        )


    def __repr__(self):
        return (
            "{self.__class__.__name__}("
            "handle={self.handle!r},"
            "name={self.name!r},"
            "status={self.status!r})"
            .format(self=self)
        )


    def __hash__(self):
        return hash((
            self.handle,
            self.name,
            self.status,
        ))


    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.handle == other.handle and
                self.name == other.name and
                self.status == other.status
            )
        else:
            return NotImplemented


    def validate(self):
        """
        Validate this Ranger.

        @raise: L{InvalidDataError} if the Ranger does not validate.
        """
        if type(self.handle) is not unicode:
            raise InvalidDataError(
                "Ranger handle must be unicode, not {0!r}".format(self.handle)
            )

        if type(self.name) is not unicode:
            raise InvalidDataError(
                "Ranger name must be unicode, not {0!r}".format(self.handle)
            )

        if type(self.status) is not unicode:
            raise InvalidDataError(
                "Ranger status must be unicode, not {0!r}".format(self.status)
            )



class Location(object):
    """
    Location
    """

    def __init__(self, name=None, address=None):
        """
        @param name: The location's name.
        @type name: L{unicode}

        @param address: The location's address.
        @type address: L{unicode}
        """
        self.name    = name
        self.address = address


    def __str__(self):
        if self.name:
            if self.address:
                return (
                    u"{self.name} ({self.address})"
                    .format(self=self).encode("utf-8")
                )
            else:
                return u"{self.name}".format(self=self).encode("utf-8")
        else:
            if self.address:
                return u"({self.address})".format(self=self).encode("utf-8")
            else:
                return ""


    def __repr__(self):
        return (
            "{self.__class__.__name__}("
            "name={self.name!r},"
            "address={self.address!r})"
            .format(self=self)
        )


    def __hash__(self):
        return hash((
            self.name,
            self.address,
        ))


    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.name == other.name and
                self.address == other.address
            )
        else:
            return NotImplemented


    def validate(self):
        """
        Validate this location.

        @raise: L{InvalidDataError} if the location does not validate.
        """
        if self.name and type(self.name) is not unicode:
            raise InvalidDataError(
                "Location name must be unicode, not {0!r}"
                .format(self.name)
            )

        if self.address and type(self.address) is not unicode:
            raise InvalidDataError(
                "Location address must be unicode, not {0!r}"
                .format(self.address)
            )



# class Shift(object):
#     @classmethod
#     def from_datetime(cls, position, datetime):
#         """
#         Create a shift from a datetime.

#         @param position: a L{Values} container corresponding to the
#             position the shift is for.

#         @param datetime: a L{DateTime} during the shift.


#         """
#         return cls(
#             position=position,
#             date=datetime.date(),
#             name=position.shiftForTime(datetime.time()),
#         )


#     def __init__(self, position, date, time=None, name=None):
#         """
#         One or both of C{time} and C{name} are required.  If both are
#         provided, they must match (meaning C{time == name.value}).

#         @param position: a L{Values} container corresponding to the
#             position the shift is for.

#         @param date: the L{Date} for the shift.

#         @param time: the L{Time} for the shift.

#         @param name: the L{ValueConstant} from the C{position}
#             container corresponding to the time of the shift.
#         """
#         if time is None:
#             if name is None:
#                 raise ValueError("Both time and name may not be None.")
#             else:
#                 time = name.value

#         if name is None:
#             name = position.lookupByValue(time)
#         elif name.value != time:
#             raise ValueError(
#                 "time and name do not match: {0} != {1}"
#                 .format(time, name)
#             )

#         self.position = position
#         self.start = DateTime(
#             year=date.year,
#             month=date.month,
#             day=date.day,
#             hour=time.hour,
#         )
#         self.name = name


#     def __hash__(self):
#         return hash((self.position, self.name))


#     def __eq__(self, other):
#         return (
#             self.position == other.position and
#             self.start == other.start
#         )


#     def __lt__(self, other):
#         if not isinstance(other, Shift):
#             return NotImplemented
#         return self.start < other.start


#     def __le__(self, other):
#         if not isinstance(other, Shift):
#             return NotImplemented
#         return self.start <= other.start


#     def __gt__(self, other):
#         if not isinstance(other, Shift):
#             return NotImplemented
#         return self.start > other.start


#     def __ge__(self, other):
#         if not isinstance(other, Shift):
#             return NotImplemented
#         return self.start >= other.start


#     def __str__(self):
#         return (
#             u"{self.start:%y-%m-%d %a} {self.name.name}"
#             .format(self=self).encode("utf-8")
#         )


#     @property
#     def end(self):
#         return (self.start.time() + TimeDelta(hours=self.position.length))


#     def next_shift(self):
#         return self.__class__(
#             position=self.position,
#             date=self.start.date(),
#             time=self.end,
#         )


def to_json_text(obj):
    """
    Convert an object into JSON text.

    @param obj: An object that is serializable to JSON.
    @type obj: L{object}

    @return: JSON text.
    @rtype: L{unicode}
    """
    return dumps(obj, separators=(',', ':')).decode("UTF-8")
