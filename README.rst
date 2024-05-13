==================
pyramid-elasticapm
==================

elastic-apm integration for the Pyramid framework

This package is inspired by https://www.elastic.co/de/blog/creating-custom-framework-integrations-with-the-elastic-apm-python-agent

**This fork is using pyramid 1.10 and python 3.8**
https://docs.pylonsproject.org/projects/pyramid/en/1.10-branch/

Since it is not published as a package, you have to install it from source,
e.g. by adding the following to requirements.in/requirements.txt::

    pyramid_elasticapm @ git+https://github.com/betermarks/pyramid_elasticapm.git

Installation
============

Install with pip::

    $ pip install git+https://github.com/betermarks/pyramid_elasticapm.git


Then include it in your pyramid application via config::

    [app:main]
    ...
    pyramid.includes = pyramid_elasticapm

or programmatically in your application::

    config.include('pyramid_elasticapm')


Settings
========


Settings for the elasticapm client can be specified via the `elasticapm`
namespace, e.g.:

* `elasticapm.server_url`: Specify the apm server url.
* `elasticapm.secret_token`: Your secret authentication token for the server.
* `elasticapm.service_name`: The service name
* `elasticapm.environment`: The environment (e.g. testing, production, …)
* `elasticapm.service_distribution`: The name of the package your are
  deploying. `pyramid_elasticapm` will retrieve the version number of this
  package and put it into the metadata of every transaction.
* `elasticapm.transactions_ignore_patterns`: Whitespace separated list of
  ignore patterns.
* `elasticapm.transaction_sample_rate`: Transaction sample rate
* `elasticapm.collect_local_variables`: Possible values: `errors` (default), `transactions`, `all`, `off`
  Keep in mind that those things can contain data that is covered by GDPR policies

All possible configuration options are supported, see
https://www.elastic.co/guide/en/apm/agent/python/current/configuration.html

Contributing
============

1. install direnv: https://direnv.net/docs/installation.html
2. hook direnv: https://direnv.net/docs/hook.html
3. create a new file called `.envrc` with the following content::

    # https://github.com/direnv/direnv/wiki/Python#venv-stdlib-module
    export VIRTUAL_ENV=venv
    layout python python3.8
4. use `direnv allow` so direnv creates and activates the virtual env when entering the directory
5. use `pip install -e . -r requirements.lock` to install the dependencies
6. run the tests `pytest`
7. use `pre-commit install` before your first commit, see https://github.com/bettermarks/.github#git-hooks
8. use `pip freeze --local > requirements.lock` to update the lock file, after the input changed
