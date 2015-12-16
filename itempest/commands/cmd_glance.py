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


def _g_image_client(mgr_or_client):
    try:
        return getattr(mgr_or_client, 'image_client')
    except Exception:
        return _g_image_v2_client(mgr_or_client)


def _g_image_v2_client(mgr_or_client):
    return getattr(mgr_or_client, 'image_client_v2', mgr_or_client)


# image-create ubuntu-12.04-so-x86_64 bare vmdk --is-public=True
#       --location=http://10.34.57.171/images/ubuntu-12.04-so-x86_64.vmdk'
def image_create(mgr_or_client, name, container_format, disk_format,
                 **kwargs):
    """Create a new image."""
    image_client = _g_image_v2_client(mgr_or_client)
    if 'is_public' in kwargs:
        is_public = kwargs.pop('is_public')
        kwargs['visibility'] = 'public' if is_public else 'private'
    return image_client.create_image(name, container_format, disk_format,
                                     **kwargs)


def image_delete(mgr_or_client, image_id):
    """Delete specified image(s)."""
    image_client = _g_image_v2_client(mgr_or_client)
    image = image_client.delete_image(image_id)
    return image


def image_download(mgr_or_client):
    """Download a specific image."""
    pass


def image_list(mgr_or_client, *args, **kwargs):
    """List images you can access."""
    image_client = _g_image_v2_client(mgr_or_client)
    result = image_client.list_images(*args, **kwargs)
    if 'images' in result:
        return result['images']
    return result


def image_show(mgr_or_client, image_id, *args, **kwargs):
    """Describe a specific image."""
    image_client = _g_image_v2_client(mgr_or_client)
    # TODO(akang): what is the client and command?
    image = image_client.show_image(image_id, *args, **kwargs)
    return image


def image_update(mgr_or_client, image_id, **kwargs):
    """Update a specific image."""
    image_client = _g_image_v2_client(mgr_or_client)
    # TODO(akang): what is the client and command?
    image = image_client.update_image(image_id, **kwargs)
    return image


# member
def member_create(mgr_or_client):
    """Share a specific image with a tenant."""
    pass


def member_delete(mgr_or_client):
    """Remove a shared image from a tenant."""
    pass


def member_list(mgr_or_client):
    """Describe sharing permissions by image or tenant."""
    pass
