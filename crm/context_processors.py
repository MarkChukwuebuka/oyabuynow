import os


def app_settings(request):

    app_defaults = {
        'app_name' : os.getenv("APP_NAME"),
        'domain_name' : os.getenv("DOMAIN_NAME")
    }

    return {'app_config': app_defaults}