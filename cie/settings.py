import os
from split_settings.tools import include, optional

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)

ENV = os.environ.get('DJANGO_ENV', 'development')

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

include(*settings)
