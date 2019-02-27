"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

# Units of file size
B = 'B'
KB = 'KB'
MB = 'MB'
GB = 'GB'
TB = 'TB'
PB = 'PB'


def get_readable_size(size, unit=B):
    """
    Converts a size into human readable format: ex: 1024 MB -> 1.0 GB
    :param size: float number
    :param unit: unit of measurement
    :return: human readable format
    """
    units = [B, KB, MB, GB, TB, PB]

    # invalid inputs should return 0.0 B
    # 0 B, 0 KB, 0 ... should also return 0.0 B
    if size <= 0 or unit not in units:
        return '0.0 B'

    # checking whether we need go for another step
    # that is unit is not already in PB and size = 1024
    if unit in units[:-1] and size >= 1024:

        # get new size
        size = size / 1024

        # get next unit
        unit = units[units.index(unit) + 1]

        # call the function again for further checking
        return get_readable_size(size, unit)

    else:

        # return the string format to 2 decimal point
        return ' '.join([str(round(size / 1, 2)), unit])


def get_to_be_active_tab(tabs, tabs_indexes, active_tab, previous=False):
    """
    Finds out the next active tab based on user input
    :param tabs: Tabs that shows up in the UI
    :param tabs_indexes: indexed tabs to show them in order
    :param active_tab: Current active tab
    :param previous: Whether or not previous is pressed
    :return: To be Active tab, Whether it is the last tab or not
    """

    # keep track of out of index tab, beneficial to detect the last tab
    no_more_tabs = False

    # find the current active tab index
    active_tab_index = tabs_indexes.get(active_tab)

    # next active tab index based on the button pressed
    if previous:
        active_tab_index -= 1
    else:
        active_tab_index += 1

    # checks out the last tab or not
    try:
        active_tab = tabs[active_tab_index]
    except IndexError:
        no_more_tabs = True

    return active_tab, no_more_tabs
