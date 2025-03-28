# https://www.elastic.co/de/blog/creating-custom-framework-integrations-with-the-elastic-apm-python-agent
import re
import sys

import elasticapm
import pkg_resources
from elasticapm.utils import get_url_dict
from elasticapm.utils.disttracing import TraceParent
from pyramid._compat import reraise
from pyramid.events import ApplicationCreated, subscriber


def includeme(config):
    config.add_tween('pyramid_elasticapm.TweenFactory')
    config.scan(
        'pyramid_elasticapm',
        ignore=[
            re.compile(r'\.testing$').search,
            re.compile(r'\.conftest$').search,
            re.compile(r'\.tests\.').search,
        ],
    )


@subscriber(ApplicationCreated)
def elasticapm_instrument(event):
    elasticapm.instrument()


# https://www.elastic.co/guide/en/apm/agent/python/current/configuration.html
ELASTICAPM_PREFIX = 'elasticapm.'


class TweenFactory:
    def __init__(self, handler, registry):
        self.handler = handler
        self.registry = registry
        settings = registry.settings

        config = {
            key.replace(ELASTICAPM_PREFIX, '').upper(): value
            for key, value in settings.items()
            if key.startswith(ELASTICAPM_PREFIX)
        }

        pkg_versions = dict()
        for pkg_name in (
            'pyramid',
            'pyramid_elasticapm',
            settings['elasticapm.service_distribution'],
        ):
            pkg_versions[pkg_name] = pkg_resources.get_distribution(
                pkg_name
            ).version

        self.client = elasticapm.Client(
            config,
            service_version=(
                pkg_versions[settings['elasticapm.service_distribution']]
            ),
            framework_name='Pyramid',
            framework_version=pkg_versions['pyramid'],
            global_labels={
                'pyramid_elasticapm': pkg_versions['pyramid_elasticapm']
            },
        )

    def __call__(self, request):
        self.client.begin_transaction(
            'request', TraceParent.from_headers(request.headers)
        )
        transaction_result = ''
        response = None
        try:
            response = self.handler(request)
            transaction_result = response.status[0] + 'xx'
            elasticapm.set_context(
                lambda: self.get_data_from_response(response), 'response'
            )
            return response
        except Exception:
            transaction_result = '5xx'
            self.client.capture_exception(
                context={
                    'request': self.get_data_from_request(request, response)
                },
                handled=False,
            )
            reraise(*sys.exc_info())
        finally:
            transaction_name = self.get_transaction_name(request)
            elasticapm.set_context(
                lambda: self.get_data_from_request(request, response),
                'request',
            )
            try:
                elasticapm.set_user_context(
                    user_id=request.authenticated_userid,
                )
            except Exception:
                # getting authenticated_userid may fail. .e.g decoding an auth
                # JWT.
                pass
            self.client.end_transaction(transaction_name, transaction_result)

    def get_data_from_request(self, request, response):
        data = {
            'headers': dict(**request.headers),
            'method': request.method,
            'socket': {
                'remote_address': request.remote_addr,
                'encrypted': request.scheme == 'https',
            },
            'cookies': dict(**request.cookies),
            'url': get_url_dict(request.url),
        }
        # remove Cookie header since the same data is in
        # request["cookies"] as well
        data['headers'].pop('Cookie', None)
        if response is not None and response.status_code >= 400:
            data['body'] = request.body
            data['response_body'] = response.body
        return data

    def get_data_from_response(self, response):
        data = {'status_code': response.status_int}
        if response.status_code >= 400:
            data['body'] = response.body
        if response.headers:
            data['headers'] = {
                key: ';'.join(response.headers.getall(key))
                for key in response.headers.iterkeys()
            }
        return data

    @classmethod
    def get_transaction_name(cls, request):
        transaction_name = request.path
        if request.matched_route:
            transaction_name = request.matched_route.pattern
        elif hasattr(request, 'view_name'):
            transaction_name = request.view_name
        if (
            transaction_name.startswith('/fanstatic')
            or transaction_name == '/favicon.ico'
        ):
            transaction_name = 'resources/*subpath'
        # prepend request method
        return (
            ' '.join((request.method, transaction_name))
            if transaction_name
            else ''
        )
