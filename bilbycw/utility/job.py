"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""
import ast
import json

from bilbycommon.utility.display_names import (
    REAL_DATA,
    FAKE_DATA,
    A0_SEARCH,
    ORBIT_TP_SEARCH,
)
from bilbycommon.utility.utils import (
    list_job_actions,
    generate_draft_job_name,
    find_display_name,
    remove_suffix,
)

from ..models import (
    BilbyCWJob,
    DataSource,
    SearchParameter,
    DataParameter,
    EngineParameter,
    ViterbiParameter,
    OutputParameter,
)

from ..forms.searchparameter.searchparameter import FIELDSETS as SEARCH_PARAMETERS_FIELDSETS
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
            data_source=from_data_source.data_source,
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

        # creating the search parameters
        search_parameters = SearchParameter.objects.filter(job=from_job)

        for search_parameter in search_parameters:
            SearchParameter.objects.create(
                job=to_job,
                name=search_parameter.name,
                value=search_parameter.value,
            )


class ParameterSimple(object):
    """
    Class to represent a parameter with name and value pair
    """

    def __init__(self, name, value, related_fields=None):
        self.name = name
        self.value = value
        self.fields = related_fields
        self._compute_json_value()

    def _compute_json_value(self):
        """
        Computes json value for the parameter. If there is no related_fields that means it is a simple parameter, which
        means that the json value would be the actual value. Otherwise for compound parameter, the json value might
        differ from the display value. For example: orbitTp field in search parameter:
            is displayed as: Start/Fixed: 4545.5, End: 7878.6, # Bins: 11
            json requires: ["4545.5", "7878.6", "11"]
        """
        if not self.fields:
            # handling an exception case:
            # for the parameter 'capture' in 'output', it is to be a list instead of the a single value
            # however, at this moment, there is no input taking from the user, so json conversion has been
            # made here. Otherwise, could follow the IFO style in Simulated data parameter
            if self.name in ['capture', ]:
                self.json_value = ast.literal_eval(self.value)
            else:
                self.json_value = self.value
        else:
            if self.name in [A0_SEARCH, ORBIT_TP_SEARCH]:
                self.json_value = [x.value for x in self.fields] if len(self.fields) > 1 else self.fields[0].value

    def display_string(self):
        """
        Formats the string representation of the name value pair as follows for displaying purpose
            : display_name of name: display name of value
        :return: formatted string
        """
        return '{name}: {value}'.format(name=find_display_name(self.name), value=find_display_name(self.value))


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

    # list to hold the Data Parameters
    data_parameters = None

    # list to hold the Search Parameters
    search_parameters = None

    # list to hold the Engine Parameters
    engine_parameters = None

    # list to hold the Viterbi Parameters
    viterbi_parameters = None

    # list to hold the Output Parameters
    output_parameters = None

    # what actions a user can perform on this job
    job_actions = None

    def clone_as_draft(self, user):
        """
        Clones the bilby job for the user as a Draft BilbyCWJob
        :param user: the owner of the new Draft BilbyCWJob
        :return: Nothing
        """

        name = generate_draft_job_name(self.job, user)

        if not name:
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
        self.job_actions = list_job_actions(self.job, user)

    def _get_value(self, fields):
        """
        Generates a final value of related fields by combining them.
        :param fields: list of fields
        :return: String representing the combined value for the related fields.
        """
        related_fields = []
        for field in fields:
            try:
                search_parameter = SearchParameter.objects.get(job=self.job, name=field)

                # if there is a value, then we will include this, otherwise we don't need to include this
                if search_parameter.value:
                    related_fields.append(ParameterSimple(name=search_parameter.name, value=search_parameter.value))
            except SearchParameter.DoesNotExist:
                pass

        # no value found for these fields
        # this should not occur, however just checking
        if not related_fields:
            return None, None

        # returning the formatted string
        return ', '.join('{}'.format(x.display_string()) for x in related_fields), related_fields

    def _populate_search_parameters(self):
        """
        Populates the search parameters for a job.
        :return: list of search parameters.
        """

        # initialising the empty list
        search_parameters = []

        # checking out the FIELDSET items for processing.
        for name, fields in SEARCH_PARAMETERS_FIELDSETS.items():

            related_fields = None

            # if the name is in the required list, we will be processing them for
            # related field using the innner method
            if name in [A0_SEARCH, ORBIT_TP_SEARCH, ]:
                value, related_fields = self._get_value(fields)

            # otherwise we will be just adding the single field.
            else:
                try:
                    value = SearchParameter.objects.get(job=self.job, name=fields[0]).value
                except SearchParameter.DoesNotExist:
                    value = None

            # adding to the list iff there is a value.
            if value:
                search_parameters.append(ParameterSimple(name=name, value=value, related_fields=related_fields))

        return search_parameters

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

            if self.data_source.data_source == REAL_DATA:
                for name in REAL_DATA_FIELDS_PROPERTIES.keys():
                    try:
                        data_parameter = all_data_parameters.get(name=name)
                        self.data_parameters.append(
                            ParameterSimple(name=data_parameter.name, value=data_parameter.value)
                        )
                    except DataParameter.DoesNotExist:
                        continue
            elif self.data_source.data_source == FAKE_DATA:
                for name in SIMULATED_DATA_FIELDS_PROPERTIES.keys():
                    try:
                        data_parameter = all_data_parameters.get(name=name)
                        self.data_parameters.append(
                            ParameterSimple(name=data_parameter.name, value=data_parameter.value)
                        )
                    except DataParameter.DoesNotExist:
                        continue

        # populating search parameters tab information, we cannot use the direct model instances here because few of
        # them are dependent fields that need to be displayed together under a same name.
        self.search_parameters = self._populate_search_parameters()

        # populating the engine parameters
        try:
            engine_parameters = EngineParameter.objects.filter(job=self.job)
        except EngineParameter.DoesNotExist:
            pass
        else:
            self.engine_parameters = []
            for engine_parameter in engine_parameters:
                self.engine_parameters.append(
                    ParameterSimple(name=engine_parameter.name, value=engine_parameter.value)
                )

        # populating the viterbi parameters
        try:
            viterbi_parameters = ViterbiParameter.objects.filter(job=self.job)
        except ViterbiParameter.DoesNotExist:
            pass
        else:
            self.viterbi_parameters = []
            for viterbi_parameter in viterbi_parameters:
                self.viterbi_parameters.append(
                    ParameterSimple(name=viterbi_parameter.name, value=viterbi_parameter.value)
                )

        # populating the output parameters
        try:
            output_parameters = OutputParameter.objects.filter(job=self.job)
        except OutputParameter.DoesNotExist:
            pass
        else:
            self.output_parameters = []
            for output_parameter in output_parameters:
                self.output_parameters.append(
                    ParameterSimple(name=output_parameter.name, value=output_parameter.value)
                )

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
                'source': self.data_source.data_source,
            })
            for data_parameter in self.data_parameters:
                data_source_dict.update({
                    remove_suffix(data_parameter.name): data_parameter.json_value,
                })

        # processing search parameter dict
        search_parameter_dict = dict()

        for search_parameter in list(self.search_parameters):
            search_parameter_dict.update({
                remove_suffix(search_parameter.name): search_parameter.json_value,
            })

        # processing engine parameter dict
        engine_parameter_dict = dict()

        for engine_parameter in list(self.engine_parameters):
            engine_parameter_dict.update({
                remove_suffix(engine_parameter.name): engine_parameter.json_value,
            })

        # processing viterbi parameter dict
        viterbi_parameter_dict = dict()

        for viterbi_parameter in list(self.viterbi_parameters):
            viterbi_parameter_dict.update({
                remove_suffix(viterbi_parameter.name): viterbi_parameter.json_value,
            })

        # processing output parameter dict
        output_parameter_dict = dict()

        for output_parameter in list(self.output_parameters):
            output_parameter_dict.update({
                remove_suffix(output_parameter.name): output_parameter.json_value,
            })

        # accumulating all in one dict
        json_dict = dict(
            name=self.job.name,
            description=self.job.description,
            datasource=data_source_dict,
            engine=engine_parameter_dict,
            viterbi=viterbi_parameter_dict,
            search=search_parameter_dict,
            output=output_parameter_dict,
        )

        # returning json with correct indentation
        return json.dumps(json_dict, indent=4)
