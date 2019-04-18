"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, get_object_or_404

from bilbycommon.utility.utils import get_readable_size
from ..utility.job import CWJob
from ..models import BilbyCWJob

logger = logging.getLogger(__name__)


@login_required
def download_asset(request, job_id, download, file_path):
    """
    Returns a file from the server for the specified job

    :param request: The django request object
    :param job_id: int: The job id
    :param download: int: Force download or not
    :param file_path: string: the path to the file to fetch

    :return: A HttpStreamingResponse object representing the file
    """
    # Get the job
    job = get_object_or_404(BilbyCWJob, id=job_id)

    # Check that this user has access to this job
    # it can download assets if there is a copy access
    bilby_job = job.bilby_job
    bilby_job.list_actions(request.user)

    if 'copy' not in bilby_job.job_actions:
        # Nothing to see here
        raise Http404

    # Get the requested file from the server
    try:
        return job.fetch_remote_file(file_path, force_download=download == 1)
    except:
        raise Http404


@login_required
def view_job(request, job_id):
    """
    Collects a particular job information and renders them in template.
    :param request: Django request object.
    :param job_id: id of the job.
    :return: Rendered template.
    """

    job = None

    # checking:
    # 1. BilbyCWJob ID and job exists
    if job_id:
        try:
            job = BilbyCWJob.objects.get(id=job_id)

            # Check that this user has access to this job
            # it can view if there is a copy access
            bilby_job = job.bilby_job
            bilby_job.list_actions(request.user)

            if 'copy' not in bilby_job.job_actions:
                job = None
            else:
                # create a bilby_job instance of the job
                bilby_job = CWJob(job_id=job.id)
                bilby_job.list_actions(request.user)

                # Empty parameter dict to pass to template
                job_data = {
                    # 'L1': None,
                    # 'V1': None,
                    # 'H1': None,
                    # 'corner': None,
                    # 'archive': None,
                    # for drafts there are no clusters assigned, so bilby_job.job.custer is None for them
                    'is_online': bilby_job.job.cluster is not None and bilby_job.job.cluster.is_connected() is not None
                }
                #
                # # Check if the cluster is online
                # if job_data['is_online']:
                #     try:
                #         # Get the output file list for this job
                #         result = bilby_job.job.fetch_remote_file_list(path="/", recursive=True)
                #         # Waste the message id
                #         result.pop_uint()
                #         # Iterate over each file
                #         num_entries = result.pop_uint()
                #         for _ in range(num_entries):
                #             path = result.pop_string()
                #             # Waste the is_file bool
                #             result.pop_bool()
                #             # Waste the file size
                #             size = get_readable_size(result.pop_ulong())
                #
                #             # Check if this is a wanted file
                #             if 'output/L1_frequency_domain_data.png' in path:
                #                 job_data['L1'] = {'path': path, 'size': size}
                #             if 'output/V1_frequency_domain_data.png' in path:
                #                 job_data['V1'] = {'path': path, 'size': size}
                #             if 'output/H1_frequency_domain_data.png' in path:
                #                 job_data['H1'] = {'path': path, 'size': size}
                #             if 'output/bilby_corner.png' in path:
                #                 job_data['corner'] = {'path': path, 'size': size}
                #             if 'bilby_job_{}.tar.gz'.format(bilby_job.job.id) in path:
                #                 job_data['archive'] = {'path': path, 'size': size}
                #     except:
                #         job_data['is_online'] = False

                return render(
                    request,
                    "bilbycw/job/view_job.html",
                    {
                        'bilby_job': bilby_job,
                        'job_data': job_data
                    }
                )
        except BilbyCWJob.DoesNotExist:
            pass

    if not job:
        # should return to a page notifying that no permission to view
        raise Http404
