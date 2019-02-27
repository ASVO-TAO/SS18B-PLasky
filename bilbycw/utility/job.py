"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

import json
import uuid

from bilbycommon.utility.display_names import (
    REAL_DATA,
    SIMULATED_DATA,
    SUBMITTED,
    QUEUED,
    IN_PROGRESS,
    DRAFT,
    COMPLETED,
    PENDING,
    ERROR,
    CANCELLED,
    WALL_TIME_EXCEEDED,
    OUT_OF_MEMORY,
    PUBLIC,
)

from ..models import (
    BilbyCWJob,
    DataSource,
    SearchParameter,
    DataParameter,
)

from ..forms.dataparameter.real import FIELDS_PROPERTIES as REAL_DATA_FIELDS_PROPERTIES
from ..forms.dataparameter.simulated import FIELDS_PROPERTIES as SIMULATED_DATA_FIELDS_PROPERTIES


def clone_job_data(from_job, to_job):
    """
    Copy job data across two jobs
    :param from_job: instance of BilbyCWJob that will be used as a source
    :param to_job: instance of BilbyCWJob that will be used as a target
    :return: Nothing
    """
    # cloning data and data parameters
    try:
        from_data_source = DataSource.objects.get(job=from_job)
        data_source_created = DataSource.objects.create(
            job=to_job,
            data_source=from_data_source.data_choice,
        )
    except DataSource.DoesNotExist:
        pass
    else:
        # creating the data parameters
        data_parameters = DataParameter.objects.filter(data_source=from_data_source)

        for data_parameter in data_parameters:
            DataParameter.objects.create(
                data_source=data_source_created,
                name=data_parameter.name,
                value=data_parameter.value,
            )


class CWJob(object):
    """
    Class representing a BilbyCWJob. The bilby job parameters are scattered in different models in the database.
    This class used to collects the correct job parameters in one place. It also defines the json representation
    of the job.
    """

    # variable to hold the BilbyCWJob model instance
    job = None

    # variable to hold the DataSource model instance
    data_source = None

    # list to hold the Data Parameters instances
    data_parameters = None

    # list to hold the Search Parameters instances
    search_parameters = None

    # what actions a user can perform on this job
    job_actions = None

    def clone_as_draft(self, user):
        """
        Clones the bilby job for the user as a Draft BilbyCWJob
        :param user: the owner of the new Draft BilbyCWJob
        :return: Nothing
        """

        if not self.job:
            return

        # try to generate a unique name for the job owner
        name = self.job.name
        while BilbyCWJob.objects.filter(user=user, name=name).exists():
            name = (self.job.name + '_' + uuid.uuid4().hex)[:255]

            # This will be true if the job has 255 Characters in it,
            # In this case, we cannot get a new name by adding something to it.
            # This can be altered later based on the requirement.
            if name == self.job.name:
                # cannot generate a new name, returning none
                return None

        # Once the name is set, creating the draft job with new name and owner and same description
        cloned = BilbyCWJob.objects.create(
            name=name,
            user=user,
            description=self.job.description,
        )

        # copying other parameters of the job
        clone_job_data(self.job, cloned)

        return cloned

    def list_actions(self, user):
        """
        List the actions a user can perform on this BilbyCWJob
        :param user: User for whom the actions will be generated
        :return: Nothing
        """

        self.job_actions = []

        # BilbyCWJob Owners and Admins get most actions
        if self.job.user == user or user.is_admin():

            # any job can be copied
            self.job_actions.append('copy')

            # job can only be deleted if in the following status:
            # 1. draft
            # 2. completed
            # 3. error (wall time and out of memory)
            # 4. cancelled
            # 5. public
            if self.job.status in [DRAFT, COMPLETED, ERROR, CANCELLED, WALL_TIME_EXCEEDED, OUT_OF_MEMORY, PUBLIC]:
                self.job_actions.append('delete')

            # edit a job if it is a draft
            if self.job.status in [DRAFT]:
                self.job_actions.append('edit')

            # cancel a job if it is not finished processing
            if self.job.status in [PENDING, SUBMITTED, QUEUED, IN_PROGRESS]:
                self.job_actions.append('cancel')

            # completed job can be public and vice versa
            if self.job.status in [COMPLETED]:
                self.job_actions.append('make_it_public')
            elif self.job.status in [PUBLIC]:
                self.job_actions.append('make_it_private')

        else:
            # non admin and non owner can copy a PUBLIC job
            if self.job.status in [PUBLIC]:
                self.job_actions.append('copy')

    def __init__(self, job_id, light=False):
        """
        Initialises the Bilby BilbyCWJob
        :param job_id: id of the job
        :param light: Whether used for only job variable to be initialised atm
        """
        # do not need to do further processing for light bilby jobs
        # it is used only for status check mainly from the model itself to list the
        # actions a user can do on the job
        if light:
            return

        # populating data source and data parameters tab information
        try:
            self.data_source = DataSource.objects.get(job=self.job)
        except DataSource.DoesNotExist:
            pass
        else:
            self.data_parameters = []
            # finding the correct data parameters for the data type
            all_data_parameters = DataParameter.objects.filter(data_source=self.data_source)

            if self.data_source == REAL_DATA:
                for name in REAL_DATA_FIELDS_PROPERTIES.keys():
                    self.data_parameters.append(all_data_parameters.get(name=name))
            elif self.data_source == SIMULATED_DATA:
                for name in SIMULATED_DATA_FIELDS_PROPERTIES.keys():
                    self.data_parameters.append(all_data_parameters.get(name=name))

        # populating search parameters tab information
        self.search_parameters = SearchParameter.objects.filter(job=self.job)

    def __new__(cls, *args, **kwargs):
        """
        Instantiate the BilbyCWJob
        :param args: arguments
        :param kwargs: keyword arguments
        :return: Instance of BilbyCWJob with job variable initialised from job_id if exists
                 otherwise returns None
        """
        result = super(CWJob, cls).__new__(cls)
        try:
            result.job = BilbyCWJob.objects.get(id=kwargs.get('job_id', None))
        except BilbyCWJob.DoesNotExist:
            return None
        return result

    def as_json(self):
        """
        Generates the json representation of the BilbyCWJob so that Bilby Core can digest it
        :return: Json Representation
        """

        # processing data dict
        data_source_dict = dict()
        if self.data_source:
            data_source_dict.update({
                'type': self.data_source,
            })
            for data_parameter in self.data_parameters:
                data_source_dict.update({
                    data_parameter.name: data_parameter.value,
                })

        # processing search parameter dict
        search_parameter_dict = dict()
        search_parameter_dict.update({
            'type': 'search_parameters',
        })
        for search_parameter in self.search_parameters:
            search_parameter_dict.update({
                search_parameter.name: search_parameter.value,
            })

        # accumulating all in one dict
        json_dict = dict(
            name=self.job.name,
            description=self.job.description,
            data_source=data_source_dict,
            search_parameters=search_parameter_dict,
        )

        # returning json with correct indentation
        return json.dumps(json_dict, indent=4)
