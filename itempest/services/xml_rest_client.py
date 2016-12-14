import base64
import requests
from xml.etree import ElementTree
import xmltodict

requests.packages.urllib3.disable_warnings()


class XmlRestClient(object):
    def __init__(self, base_url,
                 username=None, password=None,
                 **kwargs):
        self.base_url = base_url if base_url[-1] != '/' else base_url[:-1]
        self.username, self.password = username, password
        self._verify = kwargs.get('verify', False)
        self.content_type = kwargs.get('content_type', "application/xml")
        self.headers = self.base_headers()
        self.sess = None

    def base_headers(self):
        if self.username and self.password:
            _creds = self.username + ":" + self.password
            basic_auth = base64.b64encode(_creds)
            authorization = "Basic %s" % basic_auth
        else:
            authorization = None
        headers = {
            'Content-Type': self.content_type,
            'Authorization': authorization,
        }
        for k, v in headers.items():
            if not v:
                headers.pop(k)
        return headers

    def get_login_session(self):
        if not self.sess:
            self.login()
        return self.sess

    def login(self):
        self.sess = requests.Session()
        resp = self.sess.get(self.base_url,
                             headers=self.base_headers(),
                             verify=self._verify)
        return resp

    def get(self, uri, params=None, headers=None):
        session = self.get_login_session()
        req_url = self.get_req_url(uri)
        headers = self._g_headers(headers)
        self.resp_get = session.get(req_url, headers=headers,
                                    verify=self._verify)
        return self.resp_get

    def post(self, uri, body, headers=None, params=None):
        session = self.get_login_session()
        req_url = self.get_req_url(uri)
        headers = self._g_headers(headers)
        self.resp_post = session.post(req_url, body,
                                      headers=headers,
                                      params=params,
                                      verify=self._verify)
        return self.resp_post

    def put(self, uri, body=None, headers=None):
        session = self.get_login_session()
        req_url = self.get_req_url(uri)
        pass

    def delete(self, uri, params=None, headers=None):
        session = self.get_login_session()
        req_url = self.get_req_url(uri)
        pass

    def _g_headers(self, headers=None):
        if headers is None:
            headers = self.headers.copy()
        else:
            headers.update(self.headers)
        return headers

    def get_req_url(self, uri):
        if uri[0] != "/":
            uri = "/" + uri
        req_url = self.base_url + uri
        return req_url


class VSMClient(XmlRestClient):
    def __init__(self, host, username, password, **kwargs):
        super(VSMClient, self).__init__(
            ("https://%s/" % host), username=username, password=password,
            **kwargs)

    def get_all_security_policy(self):
        policies = self.get("/api/2.0/services/policy/securitypolicy/all")
        return policies

    def get_security_policy(self, sp_id):
        policy = self.get(
            "/api/2.0/services/policy/securitypolicy/%s" % sp_id)
        return policy

    def get_security_actions(self, sp_id):
        uri = "/api/2.0/services/policy/securitypolicy/%s/securityactions" \
              % sp_id
        actions = self.get(uri)
        return actions

    def import_security_policy(self, xml_body, suffix=None):
        if suffix:
            params = dict(suffix=suffix)
        else:
            params = None
        uri = "/api/2.0/services/policy/securitypolicy/hierarchy"
        policy = self.post(uri, xml_body, params=params)
        return policy

    def import_policy_from_file(self, file, suffix=None):
        """
        file_aa = "/Users/akang/Developer/admin
        policy/nsx-policy/admin-policy-AA-0.blueprint"
        AA = xnsx.import_policy_from_file(file_aa, 'AA')
        If sucess, AA.status_code == 201
        policy_id = AA.headers.get('location').split("/")[-1]
        """
        fd = open(file)
        xml_body = fd.read()
        return self.import_security_policy(xml_body, suffix)

# folders2dict
def folder2dict(content):
    folders = xmltodict.parse(content)
    entities = folders['Entities']
    totals = int(entities['@TotalResults'])
    field_list = []
    for entity in entities['Entity']:
        _type = entity['@Type']
        _field_list = entity['Fields']['Field']
        _field = {}
        for _f in _field_list:
            _key = _f['@Name']
            _val = _f['Value']
            _field[_key] = _val
        field_list.append(_field)
    return field_list
