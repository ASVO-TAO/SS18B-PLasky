from django.apps import AppConfig


class BilbycwConfig(AppConfig):
    name = 'bilbycw'

    def ready(self):
        import bilbycw.signals
