"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bilbycommon.utility.display_names import (
    REAL_DATA,
    FAKE_DATA,
)
from bilbycommon.utility.utils import get_to_be_active_tab
from bilbycw.utility.constants import (
    START,
    DATA_SOURCE,
    DATA_PARAMETER,
    DATA_PARAMETER_REAL,
    DATA_PARAMETER_SIMULATED,
    SEARCH_PARAMETER,
    LAUNCH,
    MODELS,
    FORMS_NEW,
    TAB_FORMS,
    TABS,
    TABS_INDEXES,
)
from ..utility.job import CWJob
from ..models import (
    BilbyCWJob,
    DataSource,
)


def get_enabled_tabs(bilby_job, active_tab):
    """
    Calculates and finds which tabs should be enabled in the UI
    :param bilby_job: Bilby job instance for which the tabs will be calculated
    :param active_tab: Currently active tab
    :return: list of enabled tabs
    """

    # for any bilby job at least First Two tabs should be enabled
    # because, Start tab must have been submitted before a BilbyCWJob is created
    # and as a result the user should be able to see Data Parameter Tab
    enabled_tabs = [START, DATA_PARAMETER, ]

    # if nothing has been saved yet, that means, no form has been submitted yet,
    # the user should see only the Start Tab.
    if not bilby_job:
        return enabled_tabs[:1]

    # if data parameters have been entered for it
    # enable Data Parameters and Search Parameter Tabs
    if bilby_job.data_parameters:
        if DATA_PARAMETER not in enabled_tabs:
            enabled_tabs.append(DATA_PARAMETER)
        if SEARCH_PARAMETER not in enabled_tabs:
            enabled_tabs.append(SEARCH_PARAMETER)

    # if search parameters have been entered for it
    # enable Search Parameters and Launch Tabs
    if bilby_job.search_parameters:
        if SEARCH_PARAMETER not in enabled_tabs:
            enabled_tabs.append(SEARCH_PARAMETER)
        if LAUNCH not in enabled_tabs:
            enabled_tabs.append(LAUNCH)

    # always make sure to include the active tab
    if active_tab not in enabled_tabs:
        enabled_tabs.append(active_tab)

    return enabled_tabs


def generate_forms(job=None, forms=None):
    """
    Generates all the forms for the job and the user inputs.
    :param job: the job information to be rendered in the forms
    :param forms: forms already generated during save tab
    :return: A dictionary of forms
    """

    # initialise all blank if no forms are generated, usually this will happen for a get request
    # the new job page, or job copied or loaded for editing.
    if not forms:
        forms = {
            START: None,
            DATA_SOURCE: None,
            DATA_PARAMETER_REAL: None,
            DATA_PARAMETER_SIMULATED: None,
            LAUNCH: None,
        }

    # if there is a job, update the model forms
    if job:
        for model in MODELS:
            try:
                # START Form is the BilbyCWJob instance, for other forms it is referenced
                instance = job if model in [START, ] else MODELS[model].objects.get(job=job)

                # do not override already generated forms.
                # otherwise, this would wipe out all errors from the form.
                if not forms.get(model, None):
                    # generate a form if there is none generated for this
                    forms.update({
                        model: FORMS_NEW[model](instance=instance, job=job, prefix=model)
                    })
            except MODELS[model].DoesNotExist:
                pass

    # Do a check for all forms as well,
    # i.e., for Dynamic forms here, others will be skipped.
    for name in FORMS_NEW.keys():

        # generate a form if there is none generated for this
        # Model forms would be automatically ignored here as they have been taken
        # care of in the previous section
        if not forms.get(name, None):
            forms.update({
                name: FORMS_NEW[name](job=job, prefix=name)
            })

    # if there is a job, update the forms based on job information
    # to pre-fill their input fields like the model forms
    # extra processing is needed because Dynamic Form does not
    # have easy update option by passing the instance.
    if job:
        # non-model forms update
        forms[DATA_PARAMETER_REAL].update_from_database(job=job)
        forms[DATA_PARAMETER_SIMULATED].update_from_database(job=job)
        forms[SEARCH_PARAMETER].update_from_database(job=job)
        forms[LAUNCH].update_from_database(job=job)

    return forms


def filter_as_per_input(forms_to_save, request, job):
    """
    Filters out irrelevant forms from the to save list based on user input
    :param forms_to_save: list of forms to save for a tab
    :param request: Django request object
    :param job: BilbyCWJob instance
    :return: new list of forms to save
    """

    if request.POST.get('form-tab', None) == DATA_PARAMETER and job:
        try:
            data_source = DataSource.objects.get(job=job)
            if data_source.data_source == REAL_DATA:
                forms_to_save = [DATA_PARAMETER_REAL, ]
            if data_source.data_source == FAKE_DATA:
                forms_to_save = [DATA_PARAMETER_SIMULATED, ]
        except DataSource.DoesNotExist:
            pass

    return forms_to_save


def save_tab(request, active_tab):
    """
    Saves the forms in a tab.
    :param request: Django request object
    :param active_tab: Currently active tab
    :return: active tab, forms for all the tabs, whether or not the form is submitted
    """

    submitted = False

    # check whether job exists
    try:
        job = BilbyCWJob.objects.get(id=request.session['draft_job'].get('id', None))
    except (KeyError, AttributeError, BilbyCWJob.DoesNotExist):
        job = None

    # generating the forms for the UI
    forms = dict()

    # here, the forms are saved in the database as required.
    # not all of them are saved, only the forms that are in the tab are considered.
    # additionally, it is based on the user input
    # filtering the required forms to be save based on user input
    forms_to_save = filter_as_per_input(TAB_FORMS.get(active_tab), request, job)

    error_in_form = False

    for form_to_save in forms_to_save:

        forms[form_to_save] = FORMS_NEW[form_to_save](request.POST, request=request, job=job, prefix=form_to_save)

        if not forms[form_to_save].is_valid():
            error_in_form = True

    if not error_in_form:
        # should not submit job if previous is pressed on the submit page
        previous = request.POST.get('previous', False)

        # save the forms
        for form_to_save in forms_to_save:
            if not (previous and form_to_save == LAUNCH):
                # before saving, just check whether a corresponding job has been created and in that case
                # update the form
                forms[form_to_save] = FORMS_NEW[form_to_save](request.POST, request=request, job=job,
                                                              prefix=form_to_save)
                # then save the form
                # rechecking the forms validity again, this is just because cleaned data attribute is only
                # generated once is_valid is called
                if forms[form_to_save].is_valid():
                    forms[form_to_save].save()

            # checking if the job is created in the form, this will happen only for the start tab where
            # upon saving the start form a draft job will be created and
            # the draft job is needed to save the other forms
            # to achieve this, we need to reconstruct the forms with the job information
            if not job and request.session['draft_job']:
                try:
                    job = BilbyCWJob.objects.get(id=request.session['draft_job'].get('id', None))
                except (KeyError, AttributeError, BilbyCWJob.DoesNotExist):
                    job = None

        # update the job
        if job:
            job.refresh_from_db()
            # saving the job here again will call signal to update the last updated
            # it is left to the signal because of potential change of BilbyCWJob model to
            # extend the HpcJob model.
            job.save()

        # get the active tab
        active_tab, submitted = get_to_be_active_tab(TABS, TABS_INDEXES, active_tab, previous=previous)

    # don't process further for submitted jobs
    if not submitted:

        # now generate the other forms.
        forms = generate_forms(job, forms=forms)

    return active_tab, forms, submitted


def remove_redundant_forms(forms, bilby_job):
    if not bilby_job:
        # remove anything but start tab forms
        for name in FORMS_NEW.keys():

            if name in [START, DATA_SOURCE, ]:
                continue
            else:
                forms.update({
                    name: None,
                })

        return forms

    clean_forms = forms.copy()

    if bilby_job.data_source.data_source != REAL_DATA:
        clean_forms.update({
            DATA_PARAMETER_REAL: None,
        })
    if bilby_job.data_source.data_source != FAKE_DATA:
        clean_forms.update({
            DATA_PARAMETER_SIMULATED: None,
        })

    return clean_forms


@login_required
def new_job(request):
    """
    Process request and returns all the forms for a draft job
    :param request: Django request object
    :return: Rendered template or redirects to relevant view
    """

    # Processing if the request is post, that means things to be saved here
    if request.method == 'POST':

        # Get the active tab
        active_tab = request.POST.get('form-tab', START)

        # find out new active tab, forms to render, and whether submitted or not
        active_tab, forms, submitted = save_tab(request, active_tab)

        # if submitted, nothing more to do with drafts
        # redirect to the page where the job can be viewed with other jobs
        if submitted:
            return redirect('jobs')

    # Processing if the request is get,
    # Can happen for new draft, copy or edit
    else:

        # set the active tab as start
        active_tab = START

        # Coming with copy or edit request: load the correct job id as draft
        try:
            request.session['draft_job'] = request.session['to_load']
        except (AttributeError, KeyError):
            request.session['draft_job'] = None

        # clear the to_load session variable, so that next time it does not load
        # this job automatically
        request.session['to_load'] = None

        # Now, check whether a job exists or not
        try:
            job = BilbyCWJob.objects.get(id=request.session['draft_job'].get('id', None))
        except (KeyError, AttributeError, BilbyCWJob.DoesNotExist):
            job = None

        # generate forms
        forms = generate_forms(job=job)

    # Create a bilby job for this job
    try:
        bilby_job = CWJob(job_id=request.session['draft_job'].get('id', None))
    except (KeyError, AttributeError):
        bilby_job = None

    # Clean up redundant forms based on bilby job
    forms = remove_redundant_forms(forms=forms, bilby_job=bilby_job)

    # Get enabled Tabs based on the bilby job and active job
    enabled_tabs = get_enabled_tabs(bilby_job, active_tab)

    return render(
        request,
        "bilbycw/job/edit-job.html",
        {
            'active_tab': active_tab,
            'enabled_tabs': enabled_tabs,
            'disable_other_tabs': False,
            'new_job': False,

            'start_form': forms[START],
            'data_source_form': forms[DATA_SOURCE],
            'data_parameter_real_form': forms[DATA_PARAMETER_REAL],
            'data_parameter_simulated_form': forms[DATA_PARAMETER_SIMULATED],
            'search_parameter_form': forms[SEARCH_PARAMETER],
            'submit_form': forms[LAUNCH],

            # job so far...
            'drafted_job': bilby_job,
        }
    )
