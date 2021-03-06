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

import base64

from oslo_log import log as logging
from oslo_serialization import jsonutils
import requests

from tempest import config

requests.packages.urllib3.disable_warnings()
LOG = logging.getLogger(__name__)


class VSMClient(object):
    """NSX-v client.

    The client provides the API operations on its components.
    The purpose of this rest client is to query backend components after
    issuing corresponding API calls from OpenStack. This is to make sure
    the API calls has been realized on the NSX-v backend.
    """
    API_VERSION = "2.0"

    def __init__(self, host, username, password, *args, **kwargs):
        self.force = True if 'force' in kwargs else False
        self.host = host
        self.username = username
        self.password = password
        self.version = None
        self.endpoint = None
        self.content_type = "application/json"
        self.accept_type = "application/json"
        self.verify = False
        self.secure = True
        self.interface = "json"
        self.url = None
        self.headers = None
        self.api_version = VSMClient.API_VERSION
        self.default_scope_id = None

        self.__set_headers()
        self._version = self.get_vsm_version()

    def __set_endpoint(self, endpoint):
        self.endpoint = endpoint

    def get_endpoint(self):
        return self.endpoint

    def __set_content_type(self, content_type):
        self.content_type = content_type

    def get_content_type(self):
        return self.content_type

    def __set_accept_type(self, accept_type):
        self.accept_type = accept_type

    def get_accept_type(self):
        return self.accept_type

    def __set_api_version(self, api_version):
        self.api_version = api_version

    def get_api_version(self):
        return self.api_version

    def __set_url(self, version=None, secure=None, host=None, endpoint=None):
        version = self.api_version if version is None else version
        secure = self.secure if secure is None else secure
        host = self.host if host is None else host
        endpoint = self.endpoint if endpoint is None else endpoint
        http_type = 'https' if secure else 'http'
        self.url = '%s://%s/api/%s%s' % (http_type, host, version, endpoint)

    def get_url(self):
        return self.url

    def __set_headers(self, content=None, accept=None):
        content_type = self.content_type if content is None else content
        accept_type = self.accept_type if accept is None else accept
        auth_cred = self.username + ":" + self.password
        auth = base64.b64encode(auth_cred)
        headers = {}
        headers['Authorization'] = "Basic %s" % auth
        headers['Content-Type'] = content_type
        headers['Accept'] = accept_type
        self.headers = headers

    def get(self, endpoint=None, params=None, version=None):
        """Basic query GET method for json API request."""
        self.__set_url(endpoint=endpoint, version=version)
        response = requests.get(self.url, headers=self.headers,
                                verify=self.verify, params=params)
        return response

    def delete(self, endpoint=None, params=None):
        """Basic delete API method on endpoint."""
        self.__set_url(endpoint=endpoint)
        response = requests.delete(self.url, headers=self.headers,
                                   verify=self.verify, params=params)
        return response

    def post(self, endpoint=None, body=None):
        """Basic post API method on endpoint."""
        self.__set_url(endpoint=endpoint)
        response = requests.post(self.url, headers=self.headers,
                                 verify=self.verify,
                                 data=jsonutils.dumps(body))
        return response

    def get_all_vdn_scopes(self):
        """Retrieve existing network scopes"""
        self.__set_api_version('2.0')
        self.__set_endpoint("/vdn/scopes")
        response = self.get()
        return response.json()['allScopes']

    # return the vdn_scope_id for the priamry Transport Zone
    def get_vdn_scope_id(self):
        """Retrieve existing network scope id."""
        scopes = self.get_all_vdn_scopes()
        if len(scopes) == 0:
            return scopes[0]['objectId']
        return None

    def get_vdn_scope_by_id(self, scope_id):
        """Retrieve existing network scopes id"""
        self.__set_api_version('2.0')
        self.__set_endpoint("/vdn/scopes/%s" % scope_id)
        return self.get().json()

    def get_vdn_scope_by_name(self, name):
        """Retrieve network scope id of existing scope name:

        nsxv_client.get_vdn_scope_id_by_name('TZ1')
        """
        scopes = self.get_all_vdn_scopes()
        for scope in scopes:
            if scope['name'] == name:
                return scope
        return None

    def get_all_logical_switches(self, vdn_scope_id='vdnscope-1'):
        lswitches = []
        self.__set_api_version('2.0')
        vdn_scope_id = vdn_scope_id or self.get_vdn_scope_id()
        endpoint = "/vdn/scopes/%s/virtualwires" % (vdn_scope_id)
        self.__set_endpoint(endpoint)
        response = self.get()
        paging_info = response.json()['dataPage']['pagingInfo']
        page_size = int(paging_info['pageSize'])
        total_count = int(paging_info['totalCount'])
        msg = ("There are total %s logical switches and page size is %s"
               % (total_count, page_size))
        LOG.debug(msg)
        pages = ceil(total_count, page_size)
        LOG.debug("Total pages: %s" % pages)
        for i in range(pages):
            start_index = page_size * i
            params = {'startindex': start_index}
            response = self.get(params=params)
            lswitches += response.json()['dataPage']['data']
        return lswitches

    def get_logical_switch(self, name, vdn_scope_id='vdnscope-1'):
        """Get the logical switch based on the name.

        The uuid of the OpenStack L2 network. Return ls if found,
        otherwise return None.
        """
        lswitches = self.get_all_logical_switches(vdn_scope_id=vdn_scope_id)
        lswitch = [ls for ls in lswitches if ls['name'] == name]
        if len(lswitch) == 0:
            LOG.debug('logical switch %s NOT found!' % name)
            lswitch = None
        else:
            ls = lswitch[0]
            LOG.debug('Found lswitch: %s' % ls)
        return ls

    def delete_lsw_by_name(self, name, vdn_scope_id='vdnscope-1'):
        """Delete logical switch based on name.

        The name of the logical switch on NSX-v is the uuid
        of the openstack l2 network.
        """
        ls = self.get_logical_switch(name, vdn_scope_id=vdn_scope_id)
        if ls is not None:
            endpoint = '/vdn/virtualwires/%s' % ls['objectId']
            response = self.delete(endpoint=endpoint)
            if response.status_code == 200:
                LOG.debug('Successfully deleted logical switch %s' % name)
            else:
                LOG.debug('ERROR @delete ls=%s failed with reponse code %s' %
                          (name, response.status_code))

    def delete_lsw_by_objectId(self, objectId):
        # objectId = 'virtualwire-%s'
        endpoint = '/vdn/virtualwires/%s' % objectId
        response = self.delete(endpoint=endpoint)
        if response.status_code == 200:
            LOG.debug('Successfully deleted logical switch %s' % objectId)
        else:
            LOG.debug('ERROR @delete %s failed with reponse code %s' %
                      (objectId, response.status_code))

    def get_all_edges(self):
        """Get all edges on NSX-v backend."""
        self.__set_api_version('4.0')
        self.__set_endpoint('/edges')
        edges = []
        response = self.get()
        paging_info = response.json()['edgePage']['pagingInfo']
        page_size = int(paging_info['pageSize'])
        total_count = int(paging_info['totalCount'])
        msg = "There are total %s edges and page size is %s" % (total_count,
                                                                page_size)
        LOG.debug(msg)
        pages = ceil(total_count, page_size)
        for i in range(pages):
            start_index = page_size * i
            params = {'startindex': start_index}
            response = self.get(params=params)
            edges += response.json()['edgePage']['data']
        return edges

    def get_edge(self, name):
        """Get edge based on the name, which is OpenStack router.

        Return edge if found, else return None.
        """
        edges = self.get_all_edges()
        edge = [e for e in edges if e['name'] == name]
        if len(edge) == 0:
            LOG.debug('Edge %s NOT found!' % name)
            edge = None
        else:
            edge = edge[0]
            LOG.debug('Found edge: %s' % edge)
        return edge

    def delete_edge(self, edge_id):
        self.__set_api_version('4.0')
        endpoint = '/edges/%s' % edge_id
        response = self.delete(endpoint=endpoint)
        if response.status_code != 204:
            print("ERROR on deleteing edge[%s]: reponse status code %s" % (
                edge_id, response.status_code))

    def get_firewall_l3_sections(self, include_default=False):
        ds_layer3 = 'Default Section Layer3'
        self.__set_api_version('4.0')
        self.__set_endpoint("/firewall/globalroot-0/config")
        response = self.get()
        j_son = response.json()
        if response.status_code == 200:
            l3_sessions = j_son['layer3Sections']['layer3Sections']
            if include_default:
                return l3_sessions
            firewall_sessions = [fs for fs in l3_sessions if
                                 fs['name'] != ds_layer3]
            return firewall_sessions
        return []

    def delete_firewall_l3_section(self, section_id):
        endpoint = "/firewall/globalroot-0/config/layer3sections/%s" % \
                   section_id
        self.__set_api_version('4.0')
        response = self.delete(endpoint=endpoint)
        if response.status_code != 204:
            print(
                "ERROR on deleteing firewall_session[%s]: reponse status "
                "code "
                "%s" % (
                    section_id, response.status_code))

    def get_security_groups(self):
        self.__set_api_version('2.0')
        endpoint = "/services/securitygroup/scope/globalroot-0"
        self.__set_endpoint(endpoint)
        response = self.get()
        security_groups = response.json()
        return security_groups

    def delete_security_group(self, sg_object_id, force=False):
        self.__set_api_version('2.0')
        endpoint = "/services/securitygroup/%s" % sg_object_id
        param = dict(force=force)
        response = self.delete(endpoint=endpoint, params=param)

        if response.status_code not in (200, 204):
            # 200 if force=True
            print(
                "ERROR on deleteing security_group[%s]: reponse status code "
                "%s"
                % (
                    sg_object_id, response.status_code))

    def get_security_policy(self, policy_id=None):
        self.__set_api_version('2.0')
        policy_id = policy_id if policy_id else "all"
        self.__set_endpoint("/services/policy/securitypolicy/%s" % policy_id)
        response = self.get()
        j_son = response.json()
        return j_son.get('policies', j_son)

    def get_security_actions(self, policy_id):
        endpoint_url = "/services/policy/securitypolicy/%s/securityactions"
        self.__set_api_version('2.0')
        policy_id = policy_id if policy_id else "all"
        self.__set_endpoint(endpoint_url % (policy_id))
        response = self.get()
        j_son = response.json()
        return j_son.get('actionsByCategory', j_son)

    def get_vsm_version(self):
        """Get the VSM client version including major, minor, patch, & build#.

        Build number, e.g. 6.2.0.2986609
        return: vsm version
        """
        self.__set_api_version('1.0')
        self.__set_endpoint('/appliance-management/global/info')
        response = self.get()
        json_ver = response.json()['versionInfo']
        return '.'.join([json_ver['majorVersion'], json_ver['minorVersion'],
                         json_ver['patchVersion'], json_ver['buildNumber']])

    # list ressult to console
    def list_vdn(self, columns=None):
        columns = columns or ['id', 'name']
        ofmt = " ".join(["{%s}" % x for x in columns])
        for vdn in self.get_all_vdn_scopes():
            print(ofmt.format(**vdn))

    def list_edge(self, columns=None):
        columns = columns or ['objectId', 'name', 'datacenterName']
        ofmt = " ".join(["{%s}" % x for x in columns])
        for edge in self.get_all_edges():
            print(ofmt.format(**edge))

    def list_lsw(self, columns=None, vdn_scope_id=None):
        vdn_list = self.get_all_vdn_scopes()
        if vdn_scope_id:
            vdn_id_list = [vdn_scope_id]
        else:
            vdn_id_list = [x['id'] for x in vdn_list]
        columns = columns or ['objectId', 'vdnId:5', 'name', 'vdnScopeId']
        ofmt = " ".join(["{%s}" % x for x in columns])
        for vdn_scope_id in vdn_id_list:
            for lsw in self.get_all_logical_switches(
                    vdn_scope_id=vdn_scope_id):
                print(ofmt.format(**lsw))

    def list_security_group(self, columns=None):
        columns = columns or ['objectId', 'name']
        ofmt = " ".join(["{%s}" % x for x in columns])
        for sg in self.get_security_groups():
            print(ofmt.format(**sg))

    def list_security_policy(self, columns=None):
        columns = columns or ['objectId', 'name']
        ofmt = " ".join(["{%s}" % x for x in columns])
        for sp in self.get_security_policy():
            print(ofmt.format(**sp))

    def list_firewall_l3(self, columns=None):
        columns = columns or ['id', 'type', 'name']
        ofmt = " ".join(["{%s}" % x for x in columns])
        for fw in self.get_firewall_l3_sections():
            print(ofmt.format(**fw))


def ceil(a, b):
    if b == 0:
        return 0
    div = a / b
    mod = 0 if a % b is 0 else 1
    return div + mod
