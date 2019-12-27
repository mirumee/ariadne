#
# The code herein implements (ports) the apollo-federation specs.
# Special thanks go to the apollo team for their great work!
# https://www.apollographql.com/docs/apollo-server/federation/federation-spec/
#

from .interfaces import FederatedInterfaceType
from .objects import FederatedObjectType
from .schema import make_federated_schema
