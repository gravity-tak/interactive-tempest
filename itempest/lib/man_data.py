# Copyright 2015 OpenStack Foundation
# Copyright 2015 VMware Inc.
#
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

import re
import json


# key will be popped out, so we will not use key==name which is
# keyword of most of OS packages.
def get_name_search_pattern(**kwargs):
    np_list = [('name_regexp', 'regexp'),
               ('name_startswith', 'startswith'),
               ('name_endswith', 'endswith'),
               ('name_exact', 'exact'),
               ('name_contain', 'contain')]
    spattern = {}
    for np in np_list:
        if np[0] in kwargs:
            spattern[np[1]] = kwargs.pop(np[0])
    return spattern


def is_in_spattern(name, spattern):
    if len(spattern) == 0:
        # no search pattern defined. By default it match
        return True
    if 'regexp' in spattern and re.search(spattern['regexp'], name):
        return True
    if 'exact' in spattern and spattern['exact'] == name:
        return True
    if 'startswith' in spattern and name.startswith(spattern['startswith']):
        return True
    if 'endswith' in spattern and name.startswith(spattern['endswith']):
        return True
    if 'contain' in spattern and name.find(spattern['contain']) >= 0:
        return True
    return False


def load_security_group(json_file):
    _dict = json.loads(open(json_file, 'r').read())
    sg_rules = {}
    security_groups = {}
    for rule in _dict['security-rules']:
        name = rule.pop('name')
        sg_rules[name] = rule
    for sg in _dict['security-groups']:
        name = sg['name']
        security_groups[name] = []
        for rule_name in sg['rules']:
            security_groups[name].append(sg_rules[rule_name])
    return security_groups
