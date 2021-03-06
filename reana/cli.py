# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2018 CERN.
#
# REANA is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# REANA is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# REANA; if not, write to the Free Software Foundation, Inc., 59 Temple Place,
# Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.

"""Helper scripts for REANA developers. Run `reana --help` for help."""

import os
import subprocess
import sys

import click

SRCDIR = os.environ.get('REANA_SRCDIR')

GITHUB_USER = os.environ.get('REANA_GITHUB_USER')

REPO_LIST_ALL = [
    'reana',
    'reana-client',
    'reana-cluster',
    'reana-commons',
    'reana-demo-alice-lego-train-test-run',
    'reana-demo-atlas-recast',
    'reana-demo-bsm-search',
    'reana-demo-cms-h4l',
    'reana-demo-helloworld',
    'reana-demo-lhcb-d2pimumu',
    'reana-demo-root6-roofit',
    'reana-demo-worldpopulation',
    'reana-env-aliphysics',
    'reana-env-jupyter',
    'reana-env-root6',
    'reana-job-controller',
    'reana-message-broker',
    'reana-server',
    'reana-ui',
    'reana-workflow-commons',
    'reana-workflow-controller',
    'reana-workflow-engine-cwl',
    'reana-workflow-engine-serial',
    'reana-workflow-engine-yadage',
    'reana-workflow-monitor',
    'reana.io',
]


REPO_LIST_CLUSTER = [
    'reana-commons',
    'reana-job-controller',
    'reana-message-broker',
    'reana-server',
    'reana-workflow-commons',
    'reana-workflow-controller',
    'reana-workflow-engine-cwl',
    'reana-workflow-engine-serial',
    'reana-workflow-engine-yadage',
    'reana-workflow-monitor',
]


@click.group()
def cli():  # noqa: D301
    """Run REANA development and integration commands.

    How to configure your environment:

    .. code-block:: console

        \b
        $ export REANA_SRCDIR=~/project/reana/src
        $ export REANA_GITHUB_USER=tiborsimko

    How to prepare your environment:

    .. code-block:: console

        \b
        $ # prepare directoru that will hold sources
        $ mkdir $REANA_SRCDIR && cd $REANA_SRCDIR
        $ # install reana developer helper script
        $ mkvirtualenv reana
        $ pip install git+git://github.com/reanahub/reana.git#egg=reana
        $ # run ssh-agent locally to simplify GitHub interaction
        $ eval "$(ssh-agent -s)"
        $ ssh-add ~/.ssh/id_rsa

    How to fork and clone all REANA repositories:

    .. code-block:: console

        \b
        $ reana git-fork -c ALL
        $ eval "$(reana git-fork -c ALL)"
        $ reana git-clone -c ALL

    How to compile and deploy latest ``master`` REANA cluster:

    .. code-block:: console

        \b
        $ minikube start --kubernetes-version="v1.9.4" --vm-driver=kvm2
        $ eval $(minikube docker-env)
        $ reana docker-build
        $ reana docker-images
        $ pip install reana-cluster
        $ reana-cluster -f reana-cluster-latest.yaml init
        $ # we now have REANA cluster running "master" versions of components

    How to test one component pull request:

    .. code-block:: console

        \b
        $ cd reana-job-controller
        $ reana git-checkout -b . 72 --fetch
        $ reana docker-build -c .
        $ kubectl delete pod -l app=job-controller
        $ kubectl get pods
        $ # we can now try to run an example

    How to test multiple component branches:

    .. code-block:: console

        \b
        $ reana git-checkout -b reana-job-controller 72
        $ reana git-checkout -b reana-workflow-controller 98
        $ reana git-status
        $ reana docker-build
        $ kubectl delete pod -l app=job-controller
        $ kubectl delete pod -l app=workflow-controller
        $ kubectl get pods
        $ # we can now try to run an example

    How to release and push cluster component images:

    .. code-block:: console

        \b
        $ reana git-clean
        $ reana docker-build --no-cache
        $ # we should now run one more test with non-cached ``latest``
        $ # once it works, we can tag and push
        $ reana docker-build -t 0.3.0.dev20180625
        $ reana docker-push -t 0.3.0.dev20180625
        $ # we should now make PR for ``reana-cluster.yaml`` to use given tag
    """
    pass


def shorten_component_name(component):
    """Return canonical short version of the component name.

    Example: reana-job-controller -> r-j-controller

    :param component: standard component name
    :type component: str

    :return: short component name
    :rtype: str
    """
    short_name = ''
    parts = component.split('-')
    for part in parts[:-1]:
        short_name += part[0] + '-'
    short_name += parts[-1]
    return short_name


def find_standard_component_name(short_component_name):
    """Return standard component name corresponding to the short name.

    Example: r-j-controller -> reana-job-controller

    :param short_component_name: short component name
    :type component: str

    :return: standard component name
    :rtype: str

    :raise: exception in case more than one is found
    """
    output = []
    for component in REPO_LIST_ALL:
        component_short_name = shorten_component_name(component)
        if component_short_name == short_component_name:
            output.append(component)
    if len(output) == 1:
        return output[0]
    raise Exception('Component name {0} cannot be uniquely mapped.'.format(
        'short_component_name'))


def get_srcdir(component=''):
    """Return source code directory of the given REANA component.

    :param component: standard component name
    :type component: str

    :return: source code directory for given component
    :rtype: str
    """
    if not SRCDIR:
        click.echo('Please set environment variable REANA_SRCDIR'
                   ' to the directory that will contain'
                   ' REANA source code repositories.')
        click.echo('Example:'
                   ' $ export REANA_SRCDIR=~/private/project/reana/src')
        sys.exit(1)
    if component:
        return SRCDIR + os.sep + component
    else:
        return SRCDIR


def get_current_branch(srcdir):
    """Return current Git branch name checked out in the given directory.

    :param component: standard component name
    :type component: str

    :return: checkout out branch in the component source code directory
    :rtype: str
    """
    os.chdir(srcdir)
    return subprocess.getoutput('git branch 2>/dev/null | '
                                'grep "^*" | colrm 1 2')


def select_components(components):
    """Return expanded and unified component name list based on input values.

    :param components: A list of component name that may consist of:
                          * (1) standard component names such as
                                'reana-job-controller';
                          * (2) short component name such as 'r-j-controller';
                          * (3) special value '.' indicating component of the
                                current working directory;
                          * (4) special value 'CLUSTER' that will expand to
                                cover all REANA cluster components;
                          * (5) special value 'ALL' that will expand to include
                                all REANA repositories.
    :type components: list

    :return: Unique standard component names.
    :rtype: list

    """
    short_component_names = [shorten_component_name(name)
                             for name in REPO_LIST_ALL]
    output = set([])
    for component in components:
        if component == 'ALL':
            for repo in REPO_LIST_ALL:
                output.add(repo)
        elif component == 'CLUSTER':
            for repo in REPO_LIST_CLUSTER:
                output.add(repo)
        elif component == '.':
            cwd = os.path.basename(os.getcwd())
            output.add(cwd)
        elif component in REPO_LIST_ALL:
            output.add(component)
        elif component in short_component_names:
            component_standard_name = find_standard_component_name(component)
            output.add(component_standard_name)
        else:
            display_message('Ignoring unknown component {0}.'.format(
                component))
    return list(output)


def is_component_dockerised(component):
    """Return whether the component contains Dockerfile.

    Useful to skip some docker-related commands for those components that are
    not concerned, such as building Docker images for `reana-cluster` that does
    not provide any.

    :param component: standard component name
    :type component: str

    :return: True/False whether the component is dockerisable
    :rtype: bool
    """
    if os.path.exists(get_srcdir(component) + os.sep + 'Dockerfile'):
        return True
    return False


def run_command(cmd, component=''):
    """Run given command in the given component source directory.

    Exit in case of troubles.

    :param cmd: shell command to run
    :param component: standard component name
    :type cmd: str
    :type component: str
    """
    click.secho('[{0}] {1}'.format(component, cmd), bold=True)
    if component:
        os.chdir(get_srcdir(component))
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as err:
        sys.exit(err.cmd)


def display_message(msg, component=''):
    """Display message in a similar style as run_command().

    :param msg: message to display
    :param component: standard component name
    :type msg: str
    :type component: str
    """
    click.secho('[{0}] {1}'.format(component, msg), bold=True)


@cli.command()
def version():
    """Return REANA version."""
    from reana.version import __version__
    click.echo(__version__)


@cli.command()
def help():
    """Display usage help tips and tricks."""
    click.echo(cli.__doc__)


@click.option('--component', '-c', multiple=True, default=['CLUSTER'],
              help='Which components? [shortname|name|.|CLUSTER|ALL]')
@click.option('--browser', '-b', default='firefox',
              help='Which browser to use? [firefox]')
@cli.command(name='git-fork')
def git_fork(component, browser):  # noqa: D301
    """Display commands to fork REANA source code repositories on GitHub.

    \b
    :param components: The option ``component`` can be repeated. The value may
                       consist of:
                         * (1) standard component name such as
                               'reana-job-controller';
                         * (2) short component name such as 'r-j-controller';
                         * (3) special value '.' indicating component of the
                               current working directory;
                         * (4) special value 'CLUSTER' that will expand to
                               cover all REANA cluster components [default];
                         * (5) special value 'ALL' that will expand to include
                               all REANA repositories.
    :param browser: The web browser to use. [default=firefox]
    :type component: str
    :type browser: str
    """
    components = select_components(component)
    if components:
        click.echo('# Fork REANA repositories on GitHub using your browser.')
        click.echo('# Run the following eval and then complete the fork'
                   ' process in your browser.')
        click.echo('#')
        click.echo('# eval "$(reana git-fork -b {0} {1})"'.format(
            browser,
            "".join([" -c {0}".format(c) for c in component])))
    for component in components:
        cmd = '{0} https://github.com/reanahub/{1}/fork;'.format(browser,
                                                                 component)
        click.echo(cmd)
    click.echo('echo "Please continue the fork process in the opened'
               ' browser windows."')


@click.option('--user', '-u', default=GITHUB_USER,
              help='GitHub user name [{0}]'.format(GITHUB_USER))
@click.option('--component', '-c', multiple=True, default=['CLUSTER'],
              help='Which components? [shortname|name|.|CLUSTER|ALL]')
@cli.command(name='git-clone')
def git_clone(user, component):  # noqa: D301
    """Clone REANA source repositories from GitHub.

    \b
    :param components: The option ``component`` can be repeated. The value may
                       consist of:
                         * (1) standard component name such as
                               'reana-job-controller';
                         * (2) short component name such as 'r-j-controller';
                         * (3) special value '.' indicating component of the
                               current working directory;
                         * (4) special value 'CLUSTER' that will expand to
                               cover all REANA cluster components [default];
                         * (5) special value 'ALL' that will expand to include
                               all REANA repositories.
    :param user: The GitHub user name. [default=$REANA_GITHUB_USER]
    :type component: str
    :type user: str
    """
    if not GITHUB_USER:
        click.echo('Please set environment variable REANA_GITHUB_USER to your'
                   ' GitHub user name.')
        click.echo('Example: $ export REANA_GITHUB_USER=tiborsimko')
        sys.exit(1)
    components = select_components(component)
    for component in components:
        os.chdir(get_srcdir())
        cmd = 'git clone git@github.com:{0}/{1}'.format(user, component)
        run_command(cmd)
        for cmd in [
            'git remote add upstream'
                ' "git@github.com:reanahub/{0}"'.format(component),
            'git config --add remote.upstream.fetch'
                ' "+refs/pull/*/head:refs/remotes/upstream/pr/*"',
        ]:
            run_command(cmd, component)


@click.option('--component', '-c', multiple=True, default=['CLUSTER'],
              help='Which components? [shortname|name|.|CLUSTER|ALL]')
@cli.command(name='git-status')
def git_status(component):  # noqa: D301
    """Report status of REANA source repositories.

    \b
    :param components: The option ``component`` can be repeated. The value may
                       consist of:
                         * (1) standard component name such as
                               'reana-job-controller';
                         * (2) short component name such as 'r-j-controller';
                         * (3) special value '.' indicating component of the
                               current working directory;
                         * (4) special value 'CLUSTER' that will expand to
                               cover all REANA cluster components [default];
                         * (5) special value 'ALL' that will expand to include
                               all REANA repositories.
    :type component: str
    """
    components = select_components(component)
    for component in components:
        branch = get_current_branch(get_srcdir(component))
        click.secho('- {0}'.format(component), nl=False, bold=True)
        if branch == 'master':
            click.secho(' @ {0}'.format(branch))
        else:
            click.secho(' @ {0}'.format(branch), fg='red')


@click.option('--component', '-c', multiple=True, default=['CLUSTER'],
              help='Which components? [shortname|name|.|CLUSTER|ALL]')
@cli.command(name='git-clean')
def git_clean(component):  # noqa: D301
    """Clean REANA source repository code tree.

    Removes pyc, eggs, _build and other leftover friends.
    Less aggressive then "git clean -x".

    \b
    :param components: The option ``component`` can be repeated. The value may
                       consist of:
                         * (1) standard component name such as
                               'reana-job-controller';
                         * (2) short component name such as 'r-j-controller';
                         * (3) special value '.' indicating component of the
                               current working directory;
                         * (4) special value 'CLUSTER' that will expand to
                               cover all REANA cluster components [default];
                         * (5) special value 'ALL' that will expand to include
                               all REANA repositories.
    :type component: str
    """
    components = select_components(component)
    for component in components:
        for cmd in [
            'find . -name "*.pyc" -delete',
            'find . -type d -name "*.egg-info" -exec rm -rf {} \\;',
            'find . -type d -name ".eggs" -exec rm -rf {} \\;',
            'find . -type d -name __pycache__ -delete',
            'find docs -type d -name "_build" -exec rm -rf {} \\;'
        ]:
            run_command(cmd, component)


@click.option('--branch', '-b', nargs=2, multiple=True,
              help='Which PR? [number component]')
@click.option('--fetch', is_flag=True, default=False)
@cli.command(name='git-checkout')
def git_checkout(branch, fetch):  # noqa: D301
    """Check out local branch corresponding to a component pull request.

    The ``-b`` option can be repetitive to check out several pull requests in
    several repositories at the same time.

    \b
    :param branch: The option ``branch`` can be repeated. The value consist of
                   two strings specifying the component name and the pull
                   request number. For example, ``-b reana-job-controler 72``
                   will create a local branch called ``pr-72`` in the
                   reana-job-component source code directory.
    :param fetch: Should we fetch latest upstream first? [default=False]
    :type component: str
    :type fetch: bool
    """
    for cpr in branch:
        component, pull_request = cpr
        component = select_components([component, ])[0]
        if component in REPO_LIST_ALL:
            if fetch:
                cmd = 'git fetch upstream'
                run_command(cmd, component)
            cmd = 'git checkout -b pr-{0} upstream/pr/{0}'.format(pull_request)
            run_command(cmd, component)
        else:
            msg = 'Ignoring unknown component.'
            display_message(msg, component)


@click.option('--component', '-c', multiple=True, default=['CLUSTER'],
              help='Which components? [shortname|name|.|CLUSTER|ALL]')
@cli.command(name='git-fetch')
def git_fetch(component):  # noqa: D301
    """Fetch REANA upstream source code repositories without upgrade.

    \b
    :param components: The option ``component`` can be repeated. The value may
                       consist of:
                         * (1) standard component name such as
                               'reana-job-controller';
                         * (2) short component name such as 'r-j-controller';
                         * (3) special value '.' indicating component of the
                               current working directory;
                         * (4) special value 'CLUSTER' that will expand to
                               cover all REANA cluster components [default];
                         * (5) special value 'ALL' that will expand to include
                               all REANA repositories.
    :type component: str
    """
    for component in select_components(component):
        cmd = 'git fetch upstream'
        run_command(cmd, component)


@click.option('--component', '-c', multiple=True, default=['CLUSTER'],
              help='Which components? [shortname|name|.|CLUSTER|ALL]')
@cli.command(name='git-upgrade')
def git_upgrade(component):  # noqa: D301
    """Upgrade REANA local source code repositories.

    \b
    :param components: The option ``component`` can be repeated. The value may
                       consist of:
                         * (1) standard component name such as
                               'reana-job-controller';
                         * (2) short component name such as 'r-j-controller';
                         * (3) special value '.' indicating component of the
                               current working directory;
                         * (4) special value 'CLUSTER' that will expand to
                               cover all REANA cluster components [default];
                         * (5) special value 'ALL' that will expand to include
                               all REANA repositories.
    :type component: str
    """
    for component in select_components(component):
        for cmd in ['git fetch upstream',
                    'git checkout master',
                    'git merge --ff-only upstream/master',
                    'git push origin master',
                    'git checkout -']:
            run_command(cmd, component)


@click.option('--component', '-c', multiple=True, default=['CLUSTER'],
              help='Which components? [shortname|name|.|CLUSTER|ALL]')
@cli.command(name='git-diff')
def git_diff(component):  # noqa: D301
    """Diff checked-out REANA local source code repositories.

    \b
    :param components: The option ``component`` can be repeated. The value may
                       consist of:
                         * (1) standard component name such as
                               'reana-job-controller';
                         * (2) short component name such as 'r-j-controller';
                         * (3) special value '.' indicating component of the
                               current working directory;
                         * (4) special value 'CLUSTER' that will expand to
                               cover all REANA cluster components [default];
                         * (5) special value 'ALL' that will expand to include
                               all REANA repositories.
    :type component: str
    """
    for component in select_components(component):
        for cmd in ['git diff master', ]:
            run_command(cmd, component)


@click.option('--component', '-c', multiple=True, default=['CLUSTER'],
              help='Which components? [name|CLUSTER]')
@cli.command(name='git-push')
def git_push(full, component):  # noqa: D301
    """Push REANA local repositories to GitHub origin.

    \b
    :param components: The option ``component`` can be repeated. The value may
                       consist of:
                         * (1) standard component name such as
                               'reana-job-controller';
                         * (2) short component name such as 'r-j-controller';
                         * (3) special value '.' indicating component of the
                               current working directory;
                         * (4) special value 'CLUSTER' that will expand to
                               cover all REANA cluster components [default];
                         * (5) special value 'ALL' that will expand to include
                               all REANA repositories.
    :type component: str
    """
    components = select_components(component)
    for component in components:
        for cmd in ['git push origin master']:
            run_command(cmd, component)


@click.option('--user', '-u', default='reanahub',
              help='DockerHub user name [reanahub]')
@click.option('--tag', '-t', default='latest',
              help='Image tag [latest]')
@click.option('--component', '-c', multiple=True, default=['CLUSTER'],
              help='Which components? [name|CLUSTER]')
@click.option('--no-cache', is_flag=True)
@cli.command(name='docker-build')
def docker_build(user, tag, component, no_cache):  # noqa: D301
    """Build REANA component images.

    \b
    :param components: The option ``component`` can be repeated. The value may
                       consist of:
                         * (1) standard component name such as
                               'reana-job-controller';
                         * (2) short component name such as 'r-j-controller';
                         * (3) special value '.' indicating component of the
                               current working directory;
                         * (4) special value 'CLUSTER' that will expand to
                               cover all REANA cluster components [default];
                         * (5) special value 'ALL' that will expand to include
                               all REANA repositories.
    :param user: DockerHub organisation or user name. [default=reanahub]
    :param tag: Docker tag to use. [default=latest]
    :param no_cache: Flag instructing to avoid using cache. [default=False]
    :type component: str
    :type user: str
    :type tag: str
    :type no_cache: bool
    """
    components = select_components(component)
    for component in components:
        if is_component_dockerised(component):
            if no_cache:
                cmd = 'docker build --no-cache -t {0}/{1}:{2} .'.format(
                    user, component, tag)
            else:
                cmd = 'docker build -t {0}/{1}:{2} .'.format(
                    user, component, tag)
            run_command(cmd, component)
        else:
            msg = 'Ignoring this component that does not contain' \
                  ' a Dockerfile.'
            display_message(msg, component)


@click.option('--user', '-u', default='reanahub',
              help='DockerHub user name [reanahub]')
@cli.command(name='docker-images')
def docker_images(user):  # noqa: D301
    """List REANA component images.

    :param user: DockerHub user name. [default=reanahub]
    :type user: str
    """
    cmd = 'docker images | grep {0}'.format(user)
    run_command(cmd)


@click.option('--user', '-u', default='reanahub',
              help='DockerHub user name [reanahub]')
@click.option('--tag', '-t', default='latest',
              help='Image tag [latest]')
@click.option('--component', '-c', multiple=True, default=['CLUSTER'],
              help='Which components? [name|CLUSTER]')
@cli.command(name='docker-rmi')
def docker_rmi(user, tag, component):  # noqa: D301
    """Remove REANA component images.

    \b
    :param components: The option ``component`` can be repeated. The value may
                       consist of:
                         * (1) standard component name such as
                               'reana-job-controller';
                         * (2) short component name such as 'r-j-controller';
                         * (3) special value '.' indicating component of the
                               current working directory;
                         * (4) special value 'CLUSTER' that will expand to
                               cover all REANA cluster components [default];
                         * (5) special value 'ALL' that will expand to include
                               all REANA repositories.
    :param user: DockerHub organisation or user name. [default=reanahub]
    :param tag: Docker tag to use. [default=latest]
    :type component: str
    :type user: str
    :type tag: str
    """
    components = select_components(component)
    for component in components:
        if is_component_dockerised(component):
            cmd = 'docker rmi {0}/{1}:{2}'.format(user, component, tag)
            run_command(cmd, component)
        else:
            msg = 'Ignoring this component that does not contain' \
                  ' a Dockerfile.'
            display_message(msg, component)


@click.option('--user', '-u', default='reanahub',
              help='DockerHub user name [reanahub]')
@click.option('--tag', '-t', default='latest',
              help='Image tag [latest]')
@click.option('--component', '-c', multiple=True, default=['CLUSTER'],
              help='Which components? [name|CLUSTER]')
@cli.command(name='docker-push')
def docker_push(user, tag, component):  # noqa: D301
    """Push REANA component images to DockerHub.

    \b
    :param components: The option ``component`` can be repeated. The value may
                       consist of:
                         * (1) standard component name such as
                               'reana-job-controller';
                         * (2) short component name such as 'r-j-controller';
                         * (3) special value '.' indicating component of the
                               current working directory;
                         * (4) special value 'CLUSTER' that will expand to
                               cover all REANA cluster components [default];
                         * (5) special value 'ALL' that will expand to include
                               all REANA repositories.
    :param user: DockerHub organisation or user name. [default=reanahub]
    :param tag: Docker tag to use. [default=latest]
    :type component: str
    :type user: str
    :type tag: str
    """
    components = select_components(component)
    for component in components:
        if is_component_dockerised(component):
            cmd = 'docker push {0}/{1}:{2}'.format(user, component, tag)
            run_command(cmd, component)
        else:
            msg = 'Ignoring this component that does not contain' \
                  ' a Dockerfile.'
            display_message(msg, component)


@click.option('--user', '-u', default='reanahub',
              help='DockerHub user name [reanahub]')
@click.option('--tag', '-t', default='latest',
              help='Image tag [latest]')
@click.option('--component', '-c', multiple=True, default=['CLUSTER'],
              help='Which components? [name|CLUSTER]')
@cli.command(name='docker-pull')
def docker_pull(user, tag, component):  # noqa: D301
    """Pull REANA component images from DockerHub.

    \b
    :param components: The option ``component`` can be repeated. The value may
                       consist of:
                         * (1) standard component name such as
                               'reana-job-controller';
                         * (2) short component name such as 'r-j-controller';
                         * (3) special value '.' indicating component of the
                               current working directory;
                         * (4) special value 'CLUSTER' that will expand to
                               cover all REANA cluster components [default];
                         * (5) special value 'ALL' that will expand to include
                               all REANA repositories.
    :param user: DockerHub organisation or user name. [default=reanahub]
    :param tag: Docker tag to use. [default=latest]
    :type component: str
    :type user: str
    :type tag: str
    """
    components = select_components(component)
    for component in components:
        if is_component_dockerised(component):
            cmd = 'docker pull {0}/{1}:{2}'.format(user, component, tag)
            run_command(cmd, component)
        else:
            msg = 'Ignoring this component that does not contain' \
                  ' a Dockerfile.'
            display_message(msg, component)
