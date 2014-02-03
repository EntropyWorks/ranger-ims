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
Tests for L{ims.data}.
"""

from cStringIO import StringIO
from datetime import datetime

from twisted.trial import unittest

from ims.data import (
    JSON,
    InvalidDataError,
    Incident,
    ReportEntry,
    Ranger,
    Location,
    from_json_text,
)



class ConstantTests(unittest.TestCase):
    """
    Tests for constants in L{ims.data}.
    """

    def test_JSON_states(self):
        """
        L{JSON.states} returns incident state names.
        """
        self.assertEquals(
            set(JSON.states()),
            set((
                JSON.created,
                JSON.dispatched,
                JSON.on_scene,
                JSON.closed,
            )),
        )


    def test_JSON_cmpStates(self):
        states = tuple(JSON.states())

        self.assertEquals(states, sorted(states))



class IncidentTests(unittest.TestCase):
    """
    Tests for L{ims.data.Incident}
    """

    def test_from_json_text(self):
        """
        Test for L{ims.data.Incident.from_json_text} with incident
        data.
        """
        self.equals_1(Incident.from_json_text(incident1_text, 1))


    def test_from_json_io(self):
        """
        Test for L{ims.data.Incident.from_json_io} with incident data.
        """
        self.equals_1(Incident.from_json_io(StringIO(incident1_text), 1))


    def test_from_json(self):
        """
        Test for L{ims.data.Incident.from_json} with incident data.
        """
        self.equals_1(Incident.from_json(from_json_text(incident1_text), 1))


    def test_from_json_text_no_number(self):
        """
        L{ims.data.Incident.from_json_text} requires a non-C{None}
        number.
        """
        self.assertRaises(TypeError, Incident.from_json_text, incident1_text)


    def test_from_json_io_no_number(self):
        """
        L{ims.data.Incident.from_json_io} requires a non-C{None}
        number.
        """
        self.assertRaises(
            TypeError,
            Incident.from_json_io, StringIO(incident1_text)
        )


    def test_from_json_no_number(self):
        """
        L{ims.data.Incident.from_json} requires a non-C{None} number.
        """
        self.assertRaises(
            TypeError,
            Incident.from_json, from_json_text(incident1_text)
        )


    def test_str(self):
        """
        L{ims.data.Incident.__str__}
        """
        incident = Incident.from_json_text(incident1_text, 1)
        self.assertEquals(
            str(incident),
            "{i.number}: {i.summary}".format(i=incident)
        )


    def test_repr(self):
        """
        L{ims.data.Incident.__repr__}
        """
        incident = Incident.from_json_text(incident1_text, 1)
        self.assertEquals(
            repr(incident),
            "{i.__class__.__name__}("
            "number={i.number!r},"
            "rangers={i.rangers!r},"
            "location={i.location!r},"
            "incident_types={i.incident_types!r},"
            "summary={i.summary!r},"
            "report_entries={i.report_entries!r},"
            "created={i.created!r},"
            "dispatched={i.dispatched!r},"
            "on_scene={i.on_scene!r},"
            "closed={i.closed!r},"
            "priority={i.priority!r})"
            .format(i=incident)
        )


    def test_eq_different(self):
        """
        L{ims.data.Incident.__eq__} between two different incidents.
        """
        incident1 = Incident.from_json_text(incident1_text, 1)
        incident2 = Incident.from_json_text(incident2_text, 2)

        self.assertNotEquals(incident1, incident2)


    def test_eq_equal(self):
        """
        L{ims.data.Incident.__eq__} between equal incidents.
        """
        incident1a = Incident.from_json_text(incident1_text, 1)
        incident1b = Incident.from_json_text(incident1_text, 1)

        self.assertEquals(incident1a, incident1a)
        self.assertEquals(incident1a, incident1b)


    def test_eq_other(self):
        """
        L{ims.data.Incident.__eq__} between incident and other type.
        """
        incident = Incident.from_json_text(incident1_text, 1)

        self.assertNotEquals(incident, object())


    def test_validate(self):
        """
        L{ims.data.Incident.validate} of valid incident.
        """
        incident = Incident.from_json_text(incident1_text, 1)

        incident.validate()


    def test_validate_none_rangers(self):
        """
        L{ims.data.Incident.validate} of incident with C{None} Rangers.
        """
        incident = Incident.from_json_text(incident1_text, 1)
        incident.rangers = None

        self.assertRaises(InvalidDataError, incident.validate)


    def test_validate_not_unicode_types(self):
        """
        L{ims.data.Incident.validate} of incident with non-unicode
        incident types.
        """
        incident = Incident.from_json_text(incident1_text, 1)
        incident.incident_types.append(b"bytes")

        self.assertRaises(InvalidDataError, incident.validate)


    def test_validate_not_unicode_summary(self):
        """
        L{ims.data.Incident.validate} of incident with non-unicode
        summary.
        """
        incident = Incident.from_json_text(incident1_text, 1)
        incident.summary = b"bytes"

        self.assertRaises(InvalidDataError, incident.validate)


    def test_validate_not_datetime_created(self):
        """
        L{ims.data.Incident.validate} of incident with non-datetime
        created time.
        """
        incident = Incident.from_json_text(incident1_text, 1)
        incident.created = 0

        self.assertRaises(InvalidDataError, incident.validate)


    def test_validate_not_datetime_dispatched(self):
        """
        L{ims.data.Incident.validate} of incident with non-datetime
        dispatched time.
        """
        incident = Incident.from_json_text(incident1_text, 1)
        incident.dispatched = 0

        self.assertRaises(InvalidDataError, incident.validate)


    def test_validate_not_datetime_on_scene(self):
        """
        L{ims.data.Incident.validate} of incident with non-datetime
        on scene time.
        """
        incident = Incident.from_json_text(incident1_text, 1)
        incident.on_scene = 0

        self.assertRaises(InvalidDataError, incident.validate)


    def test_validate_not_datetime_closed(self):
        """
        L{ims.data.Incident.validate} of incident with non-datetime
        closed time.
        """
        incident = Incident.from_json_text(incident1_text, 1)
        incident.closed = 0

        self.assertRaises(InvalidDataError, incident.validate)


    def test_validate_not_int_priority(self):
        """
        L{ims.data.Incident.validate} of incident with non-int
        priority.
        """
        incident = Incident.from_json_text(incident1_text, 1)
        incident.priority = "1"

        self.assertRaises(InvalidDataError, incident.validate)


    def test_validate_not_int_priority_bounds(self):
        """
        L{ims.data.Incident.validate} of incident with out-of-bounds
        priority.
        """
        incident = Incident.from_json_text(incident1_text, 1)

        incident.priority = "0"
        self.assertRaises(InvalidDataError, incident.validate)

        incident.priority = "6"
        self.assertRaises(InvalidDataError, incident.validate)


    def test_to_json_text(self):
        """
        L{ims.data.Incident.to_json_text} produces same incident as json.
        """
        incident1a = Incident.from_json_text(incident1_text, 1)
        incident1a_text = incident1a.to_json_text()
        incident1b = Incident.from_json_text(incident1a_text, 1)

        self.assertEquals(incident1a, incident1b)


    def equals_1(self, incident):
        self.assertEquals(incident.number, 1)
        self.assertEquals(incident.rangers, [Ranger(u"Tulsa", None, None)])
        self.assertEquals(
            incident.location,
            Location(
                u"Near the Man",
                u"A couple of posts towards the temple from the Man",
            )
        )
        self.assertEquals(incident.incident_types, [u"Vehicle"])
        self.assertEquals(incident.summary, u"Knocked out spire")
        self.assertEquals(
            incident.report_entries,
            [
                ReportEntry(
                    created=datetime(2013, 3, 21, 19, 18, 42),
                    author=u"Tool",
                    text=(
                        u"Art car knocked out a spire at couple of "
                        u"posts toward temple from the Man."
                    ),
                ),
                ReportEntry(
                    created=datetime(2013, 3, 21, 20, 14, 11),
                    author=u"Tool",
                    text=(
                        u"Intercept: lamp post is bent, rebar is broken.  "
                        u"Khaki has notified DPW.  ETA unknown."
                    ),
                ),
                ReportEntry(
                    created=datetime(2013, 3, 21, 21, 41, 40),
                    author=u"<unknown>",
                    text=u"Tulsa is hanging out until eyes on art arrives.",
                ),
                ReportEntry(
                    created=datetime(2013, 3, 21, 22, 0, 10),
                    author=u"Splinter",
                    text=(
                        u"Tulsa: got some help, dealt with it, may need "
                        u"some lighting, but code 4."
                    ),
                ),
            ]
        )
        self.assertEquals(
            incident.created,
            datetime(2013, 3, 21, 19, 16, 0)
        )
        self.assertEquals(
            incident.dispatched,
            datetime(2013, 3, 21, 20, 55, 11)
        )
        self.assertEquals(
            incident.on_scene,
            datetime(2013, 3, 21, 20, 55, 11)
        )
        self.assertEquals(
            incident.closed,
            datetime(2013, 3, 21, 22, 0, 17)
        )
        self.assertEquals(
            incident.priority,
            2
        )



class ReportEntryTests(unittest.TestCase):
    """
    Tests for L{ims.data.ReportEntry}
    """

    def test_str(self):
        """
        L{ims.data.ReportEntry.__str__}
        """
        entry = ReportEntry(
            author=u"Tool",
            text=u"Something happened!",
            created=datetime(1972, 06, 29, 12, 0, 0),
        )
        self.assertEquals(
            str(entry),
            "Tool@1972-06-29 12:00:00: Something happened!"
        )


    def test_repr(self):
        """
        L{ims.data.ReportEntry.__repr__}
        """
        entry = ReportEntry(
            author=u"Tool",
            text=u"Something happened!",
            created=datetime(1972, 06, 29, 12, 0, 0),
        )
        self.assertEquals(
            repr(entry),
            "{e.__class__.__name__}("
            "author={e.author!r},"
            "text={e.text!r},"
            "created={e.created!r})"
            .format(e=entry)
        )


    def test_eq_different(self):
        """
        L{ims.data.ReportEntry.__eq__} between two different entries.
        """
        entry1 = ReportEntry(
            author=u"Tool",
            text=u"Something happened!",
            created=datetime(1972, 06, 29, 12, 0, 0),
        )
        entry2 = ReportEntry(
            author=u"Tool",
            text=u"Something else happened!",
            created=datetime(1972, 06, 29, 12, 0, 0),
        )

        self.assertNotEquals(entry1, entry2)


    def test_eq_equal(self):
        """
        L{ims.data.ReportEntry.__eq__} between equal entries.
        """
        entry1a = ReportEntry(
            author=u"Tool",
            text=u"Something happened!",
            created=datetime(1972, 06, 29, 12, 0, 0),
        )
        entry1b = ReportEntry(
            author=u"Tool",
            text=u"Something happened!",
            created=datetime(1972, 06, 29, 12, 0, 0),
        )

        self.assertEquals(entry1a, entry1a)
        self.assertEquals(entry1a, entry1b)


    def test_eq_other(self):
        """
        L{ims.data.ReportEntry.__eq__} between entry and other type.
        """
        entry = ReportEntry(
            author=u"Tool",
            text=u"Something happened!",
            created=datetime(1972, 06, 29, 12, 0, 0),
        )

        self.assertNotEquals(entry, object())


    def test_validate(self):
        """
        L{ims.data.ReportEntry.validate} of valid entry.
        """
        entry = ReportEntry(
            author=u"Tool",
            text=u"Something happened!",
            created=datetime(1972, 06, 29, 12, 0, 0),
        )

        entry.validate()


    def test_validate_non_unicode_author(self):
        """
        L{ims.data.ReportEntry.validate} of entry with non-unicode
        author.
        """
        entry = ReportEntry(
            author=b"Tool",
            text=u"Something happened!",
            created=datetime(1972, 06, 29, 12, 0, 0),
        )

        self.assertRaises(InvalidDataError, entry.validate)


    def test_validate_non_unicode_text(self):
        """
        L{ims.data.ReportEntry.validate} of entry with non-unicode
        text.
        """
        entry = ReportEntry(
            author=u"Tool",
            text=b"Something happened!",
            created=datetime(1972, 06, 29, 12, 0, 0),
        )

        self.assertRaises(InvalidDataError, entry.validate)


    def test_validate_non_datetime_created(self):
        """
        L{ims.data.ReportEntry.validate} of entry with non-datetime
        created time.
        """
        entry = ReportEntry(
            author=u"Tool",
            text=u"Something happened!",
            created=0,
        )

        self.assertRaises(InvalidDataError, entry.validate)



class RangerTests(unittest.TestCase):
    """
    Tests for L{ims.data.Ranger}
    """

    tool = Ranger(
        handle=u"Tool",
        name=u"Wilfredo Sanchez Vega",
        status="vintage",
    )

    tulsa = Ranger(
        handle=u"Tulsa",
        name=u"Curtis Kline",
        status="vintage",
    )


    def test_str(self):
        """
        L{ims.data.Ranger.__str__}
        """
        self.assertEquals(str(self.tool), "Tool (Wilfredo Sanchez Vega)")


    def test_repr(self):
        """
        L{ims.data.Ranger.__repr__}
        """
        self.assertEquals(
            repr(self.tool),
            "Ranger(handle=u'Tool',name=u'Wilfredo Sanchez Vega',"
            "status='vintage')"
        )


    def test_eq_different(self):
        """
        L{ims.data.Ranger.__eq__} between two different entries.
        """
        self.assertNotEquals(self.tool, self.tulsa)


    def test_eq_equal(self):
        """
        L{ims.data.Ranger.__eq__} between equal entries.
        """
        ranger1a = Ranger(
            handle=u"Tulsa",
            name=u"Curtis Kline",
            status="vintage",
        )
        ranger1b = Ranger(
            handle=u"Tulsa",
            name=u"Curtis Kline",
            status="vintage",
        )

        self.assertEquals(ranger1a, ranger1a)
        self.assertEquals(ranger1a, ranger1b)


    def test_eq_other(self):
        """
        L{ims.data.Ranger.__eq__} between ranger and other type.
        """
        self.assertNotEquals(self.tool, object())


    def test_validate(self):
        """
        L{ims.data.Ranger.validate} of valid ranger.
        """
        self.tool.validate()


    def test_validate_non_unicode_handle(self):
        """
        L{ims.data.Ranger.validate} of Ranger with non-unicode
        handle.
        """
        ranger = Ranger(
            handle=b"Tulsa",
            name=u"Curtis Kline",
            status="vintage",
        )

        self.assertRaises(InvalidDataError, ranger.validate)


    def test_validate_non_unicode_name(self):
        """
        L{ims.data.Ranger.validate} of Ranger with non-unicode name.
        """
        ranger = Ranger(
            handle=u"Tulsa",
            name=b"Curtis Kline",
            status="vintage",
        )

        self.assertRaises(InvalidDataError, ranger.validate)



class LocationTests(unittest.TestCase):
    """
    Tests for L{ims.data.Location}
    """

    hq = Location(
        name=u"Ranger HQ",
        address=u"5:45 & Esplanade",
    )

    man = Location(
        name=u"The Man",
        address=u"The Man",
    )


    def test_str(self):
        """
        L{ims.data.Location.__str__}
        """
        self.assertEquals(str(self.hq), "Ranger HQ (5:45 & Esplanade)")


    def test_repr(self):
        """
        L{ims.data.Location.__repr__}
        """
        self.assertEquals(
            repr(self.hq),
            "Location(name=u'Ranger HQ',address=u'5:45 & Esplanade')"
        )


    def test_eq_different(self):
        """
        L{ims.data.Location.__eq__} between two different entries.
        """
        self.assertNotEquals(self.hq, self.man)


    def test_eq_equal(self):
        """
        L{ims.data.Location.__eq__} between equal entries.
        """
        location1a = Location(
            name=u"Ranger HQ",
            address=u"5:45 & Esplanade",
        )
        location1b = Location(
            name=u"Ranger HQ",
            address=u"5:45 & Esplanade",
        )

        self.assertEquals(location1a, location1a)
        self.assertEquals(location1a, location1b)


    def test_eq_other(self):
        """
        L{ims.data.Location.__eq__} between location and other type.
        """
        self.assertNotEquals(self.hq, object())


    def test_validate(self):
        """
        L{ims.data.Location.validate} of valid location.
        """
        self.hq.validate()


    def test_validate_non_unicode_name(self):
        """
        L{ims.data.Location.validate} of location with non-unicode name.
        """
        location = Location(
            name=b"Ranger HQ",
            address=u"5:45 & Esplanade",
        )

        self.assertRaises(InvalidDataError, location.validate)


    def test_validate_non_unicode_address(self):
        """
        L{ims.data.Location.validate} of location with non-unicode
        address.
        """
        location = Location(
            name=u"Ranger HQ",
            address=b"5:45 & Esplanade",
        )

        self.assertRaises(InvalidDataError, location.validate)







incident1_text = """
{
    "closed": "2013-03-21T22:00:17Z",
    "created": "2013-03-21T19:16:00Z",
    "dispatched": "2013-03-21T20:55:11Z",
    "incident_types": [
        "Vehicle"
    ],
    "location_address": "A couple of posts towards the temple from the Man",
    "location_name": "Near the Man",
    "number": 1,
    "on_scene": "2013-03-21T20:55:11Z",
    "priority": 2,
    "ranger_handles": [
        "Tulsa"
    ],
    "report_entries": [
        {
            "author": "Tool",
            "created": "2013-03-21T19:18:42Z",
            "text":
                "Art car knocked out a spire at couple of posts toward temple from the Man."
        },
        {
            "author": "Tool",
            "created": "2013-03-21T20:14:11Z",
            "text":
                "Intercept: lamp post is bent, rebar is broken.  Khaki has notified DPW.  ETA unknown."
        },
        {
            "created": "2013-03-21T21:41:40Z",
            "text": "Tulsa is hanging out until eyes on art arrives."
        },
        {
            "author": "Splinter",
            "created": "2013-03-21T22:00:10Z",
            "text":
                "Tulsa: got some help, dealt with it, may need some lighting, but code 4."
        }
    ],
    "summary": "Knocked out spire"
}
"""

incident2_text = """
{
    "location_address": "The Man",
    "incident_types": [
        "Admin"
    ],
    "closed": "2013-03-21T20:04:11Z",
    "location_name": "The Man",
    "on_scene": "2013-03-21T20:04:11Z",
    "priority": 5,
    "summary": "Releived Rangers at the Man",
    "number": 2,
    "ranger_handles": [
        "Lefty"
    ],
    "created": "2013-03-21T20:02:08Z",
    "dispatched": "2013-03-21T20:04:11Z",
    "report_entries": [
    ]
}
"""
