# Number of jobs to be displayed in a page showing list view
# Ex: My Jobs, My Drafts, All Jobs, Public Jobs etc.
JOBS_PER_PAGE = 50


def set_dict_indices(my_array):
    """Creates a dictionary based on values in my_array, and links each of them to an index.

    Parameters
    ----------
    my_array:
        An array (e.g. [a,b,c])

    Returns
    -------
    my_dict:
        A dictionary (e.g. {a:0, b:1, c:2})
    """
    my_dict = {}
    i = 0
    for value in my_array:
        my_dict[value] = i
        i += 1

    return my_dict
