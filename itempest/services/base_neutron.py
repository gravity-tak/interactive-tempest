from tempest.lib.services.network import base


class BaseNetworkClient(base.BaseNetworkClient):

    # https://bugs.launchpad.net/neutron/+bug/1606659
    # tag-add is a CREATE operation; then expected resp_code is 201
    # however it is using http PUT operation to accomplish it.
    def update_resource(self, uri, post_data, resp_code=None):
        if resp_code:
            req_uri = self.uri_prefix + uri
            req_post_data = base.json.dumps(post_data)
            resp, body = self.put(req_uri, req_post_data)
            body = base.json.loads(body)
            self.expected_success(resp_code, resp.status)
            return base.rest_client.ResponseBody(
                resp, body)
        else:
            return super(BaseNetworkClient, self).update_resource(
                uri, post_data)
