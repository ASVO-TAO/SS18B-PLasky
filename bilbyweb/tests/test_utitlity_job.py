"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from django.test import (
    TestCase,
)

from bilbycommon.utility.job import BilbyJob
from .utility import TestData, get_members
from ..models import BilbyPEJob


class TestBilbyJob(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.data = TestData()
        cls.members = get_members()

    def test_job_creation(self):
        job = BilbyPEJob.objects.create(
            user=self.members[0],
            name='a job',
            description='a job description',
        )

        b_job = BilbyJob(job_id=job.id)
        self.assertNotEquals(b_job, None)
        self.assertEquals(b_job.job, job)

    def test_job_creation_invalid(self):
        BilbyPEJob.objects.create(
            user=self.members[0],
            name='a job',
            description='a job description',
        )

        b_job = BilbyJob(job_id=-1)
        self.assertEquals(b_job, None)
