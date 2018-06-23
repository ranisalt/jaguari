from os import environ, pardir, path
from split_settings.tools import include, optional

BASE_DIR = path.join(path.dirname(path.abspath(__file__)), pardir)

ENV = environ.get('DJANGO_ENV', 'development')

settings = [
    'components/application.py',
    'components/i18n.py',
    'components/static.py',

    # plugins
    'components/cas.py',

    # Select the right env:
    f'env/{ENV}.py',
    # Optionally override some settings:
    optional('env/local.py'),
]

print(settings)

include(*settings)
