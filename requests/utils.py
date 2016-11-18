import json
import random
from base64 import b64encode
from django.conf import settings
from six.moves.urllib import parse
from six.moves.urllib import request


def make_request(host, path):
    credentials = bytes('{}:{}'.format(*settings.CAGR_CREDENTIALS), 'utf8')
    auth_token = 'Basic {}'.format(b64encode(credentials).decode())

    headers = {'authorization': auth_token}
    req = request.Request(parse.urljoin(host, path), headers=headers)
    with request.urlopen(req) as page:
        return json.loads(page.read().decode())


def random_use_code():
    return ''.join(random.choice(settings.USE_CODE_ALPHABET) for _ in
                   range(settings.USE_CODE_LENGTH))
