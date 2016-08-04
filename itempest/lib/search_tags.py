G = {
    'net1': {'east', 'gold', 'production'},
    'net2': {'west', 'silver', 'development'},
    'net3': {'north', 'brown', 'development', 'abc'},
    'net4': {'south', 'brown', 'testing', 'a'},
    'net5': {'west', 'gold', 'production', 'ab'},
    'net6': {'east', 'silver', 'testing'},
    'net7': {'north', 'gold', 'production'},
    'net8': {'south', 'silver', 'testing'}
}


# A little complex, but it can operate on subset of K_sets (G variable)
# Think it like pipe through these methods using on_keys to filter
#
# tags
def x_and_y(x_and_y, K_sets, on_keys=None):
    s_xy = set(x_and_y)
    xy_s = [k for k, S in K_sets.items()
            if (on_keys is None or k in on_keys) and s_xy.issubset(S)]
    return xy_s


# not-tags
def not_x_and_y(x_and_y, K_sets, on_keys=None):
    s_xy = set(x_and_y)
    xy_s = [k for k, S in K_sets.items()
            if (on_keys is None or k in on_keys) and not s_xy.issubset(S)]
    return xy_s


# tags-any
def x_or_y(x_or_y, K_sets, on_keys=None):
    s_xy = set(x_or_y)
    xy_s = [k for k, S in K_sets.items()
            if (on_keys is None or k in on_keys) and len(S & s_xy) > 0]
    return xy_s


# not tags-any
def not_x_or_y(x_or_y, K_sets, on_keys=None):
    s_xy = set(x_or_y)
    xy_s = [k for k, S in K_sets.items()
            if (on_keys is None or k in on_keys) and len(S & s_xy) == 0]
    return xy_s


### Usages:
# SEARCH: tags=['gold','production']
#     x_and_y(['gold','production'],G)
# SEARCH: tags=['gold','production'] and tags-any=['west', 'east']
#     x_or_y(['west', 'east'], G, x_and_y(['gold','production'],G))
# SEARCH: tags=['gold','production'] and not-tags-any=['west', 'east']
#     not_x_or_y(['west', 'east'], G, x_and_y(['gold','production'],G))


### just for your reference
### you should use methods above
###
# tags
def find_x_and_y(x_and_y, K_sets):
    s_xy = set(x_and_y)
    xy_s = [k for k, S in K_sets.items() if s_xy.issubset(S)]
    return xy_s


# not-tags
def notfind_x_and_y(x_and_y, K_sets):
    s_xy = set(x_and_y)
    xy_s = [k for k, S in K_sets.items() if not s_xy.issubset(S)]
    return xy_s


# tags-any
def find_x_or_y(x_or_y, K_sets):
    s_xy = set(x_or_y)
    xy_s = [k for k, S in K_sets.items() if len(S & s_xy) > 0]
    return xy_s


# not tags-any
def notfind_x_or_y(x_or_y, K_sets):
    s_xy = set(x_or_y)
    xy_s = [k for k, S in K_sets.items() if len(S & s_xy) == 0]
    return xy_s


# tags and tags-any
def find_x_and_y_plus_a_or_b(x_and_y, a_or_b, K_sets):
    s_xy = set(x_and_y)
    s_ab = set(a_or_b)
    m_set = [k for k, S in K_sets.items()
             if s_xy.issubset(S) and len(S & s_ab) > 0]
    return m_set


# tags and not-tags-any
def find_x_and_y_minus_a_or_b(x_and_y, a_or_b, K_sets):
    s_xy = set(x_and_y)
    s_ab = set(a_or_b)
    m_set = [k for k, S in K_sets.items()
             if s_xy.issubset(S) and len(S & s_ab) == 0]
    return m_set
