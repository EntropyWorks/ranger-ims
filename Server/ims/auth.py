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
Authentication
"""

__all__ = [
]

from zope.interface import implements

from twisted.cred.portal import IRealm, Portal

from twisted.web.resource import IResource
from twisted.web.guard import HTTPAuthSessionWrapper, DigestCredentialFactory



def guard(resourceClass, realmName, checkers):
    class IMSRealm(object):
        implements(IRealm)

        def requestAvatar(self, avatarId, mind, *interfaces):
            if IResource not in interfaces:
                raise NotImplementedError()

            resource = resourceClass()
            resource.avatarId = avatarId

            return (IResource, resource, lambda: None)

    portal = Portal(IMSRealm(), checkers)

    return resourceClass
    return lambda: HTTPAuthSessionWrapper(
        portal,
        (
            DigestCredentialFactory("md5", realmName),
        )
    )
