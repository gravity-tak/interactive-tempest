def tag_add(mgr_or_client, **kwargs):
    """Update a specific image."""
    tags_client = _g_tags_client(mgr_or_client)
    if 'resource' in kwargs:
        kwargs['resource_id'] = _g_resource_id(mgr_or_client,
                                               kwargs['resource'])
    return tags_client.add_tag(**kwargs)


def tag_remove(mgr_or_client, **kwargs):
    """Update a specific image."""
    tags_client = _g_tags_client(mgr_or_client)
    if 'resource' in kwargs:
        kwargs['resource_id'] = _g_resource_id(mgr_or_client,
                                               kwargs['resource'])
    return tags_client.remove_tag(**kwargs)


def tag_replace(mgr_or_client, **kwargs):
    """Update a specific image."""
    tags_client = _g_tags_client(mgr_or_client)
    if 'resource' in kwargs:
        kwargs['resource_id'] = _g_resource_id(mgr_or_client,
                                               kwargs['resource'])
    return tags_client.replace_tag(**kwargs)


# utilities
def _g_tags_client(mgr_or_client):
    return getattr(mgr_or_client, 'tags_client', mgr_or_client)


def _g_resource_id(mgr_or_client, resource, resource_type='network'):
    # currently core service, only resource_type=network is supported
    networks_client = mgr_or_client.networks_client
    body = networks_client.list_networks(name=resource)
    net_list = body['networks']
    if len(net_list) != 1:
        return resource
    return net_list[0]['id']
