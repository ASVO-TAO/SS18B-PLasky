from django.apps import AppConfig


class BilbycommonConfig(AppConfig):
    name = 'bilbycommon'

    def ready(self):
        import bilbycommon.signals
