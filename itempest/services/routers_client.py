#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tempest.lib.services.network import routers_client as client


# latest routers_client remove extra_routes
class RoutersClient(client.RoutersClient):

    def update_extra_routes(self, router_id, **kwargs):
        """Update Extra routes.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#updateExtraRoutes
        """
        uri = '/routers/%s' % router_id
        put_body = {'router': kwargs}
        return self.update_resource(uri, put_body)

    def delete_extra_routes(self, router_id):
        uri = '/routers/%s' % router_id
        put_body = {
            'router': {
                'routes': None
            }
        }
        return self.update_resource(uri, put_body)

    def update_router_with_snat_gw_info(self, router_id, **kwargs):
        """Update a router passing also the enable_snat attribute.

        This method must be execute with admin credentials, otherwise the API
        call will return a 404 error.
        """
        return self._update_router(router_id,
                                   set_enable_snat=True, **kwargs)
