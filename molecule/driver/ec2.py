#  Copyright (c) 2015-2018 Cisco Systems, Inc.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

from molecule import logger
from molecule.driver import base

from molecule import util

LOG = logger.get_logger(__name__)


class EC2(base.Base):
    """
    The class responsible for managing `EC2`_ instances.  `EC2`_
    is ``not`` the default driver used in Molecule.

    Molecule leverages Ansible's `ec2_module`_, by mapping variables from
    ``molecule.yml`` into ``create.yml`` and ``destroy.yml``.

    .. _`ec2_module`: https://docs.ansible.com/ansible/latest/ec2_module.html

    .. code-block:: yaml

        driver:
          name: ec2
        platforms:
          - name: instance

    Some configuration examples:

    .. code-block:: yaml

        driver:
          name: ec2
        platforms:
          - name: instance
            image: ami-0311dc90a352b25f4
            instance_type: t2.micro
            vpc_subnet_id: subnet-1cb17175

    If you don't know the AMI code or want to avoid hardcoding it:

    .. code-block:: yaml

        driver:
          name: ec2
        platforms:
          - name: instance
            image_owner: 099720109477
            image_name: ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-20190320
            instance_type: t2.micro
            vpc_subnet_id: subnet-1cb17175

    Use wildcards for getting the latest image. For example, the latest Ubuntu bionic image:

    .. code-block:: yaml

        driver:
          name: ec2
        platforms:
          - name: instance
            image_owner: 099720109477
            image_name: ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-*
            instance_type: t2.micro
            vpc_subnet_id: subnet-1cb17175

    .. code-block:: bash

        $ pip install 'molecule[ec2]'

    Change the options passed to the ssh client.

    .. code-block:: yaml

        driver:
          name: ec2
          ssh_connection_options:
            - '-o ControlPath=~/.ansible/cp/%r@%h-%p'

    .. important::

        Molecule does not merge lists, when overriding the developer must
        provide all options.

    Provide a list of files Molecule will preserve, relative to the scenario
    ephemeral directory, after any ``destroy`` subcommand execution.

    .. code-block:: yaml

        driver:
          name: ec2
          safe_files:
            - foo

    .. _`EC2`: https://aws.amazon.com/ec2/
    """  # noqa

    def __init__(self, config):
        super(EC2, self).__init__(config)
        self._name = 'ec2'

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def login_cmd_template(self):
        connection_options = ' '.join(self.ssh_connection_options)

        return (
            'ssh {{address}} '
            '-l {{user}} '
            '-p {{port}} '
            '-i {{identity_file}} '
            '{}'
        ).format(connection_options)

    @property
    def default_safe_files(self):
        return [self.instance_config]

    @property
    def default_ssh_connection_options(self):
        return self._get_ssh_connection_options()

    def login_options(self, instance_name):
        d = {'instance': instance_name}

        return util.merge_dicts(d, self._get_instance_config(instance_name))

    def ansible_connection_options(self, instance_name):
        try:
            d = self._get_instance_config(instance_name)

            return {
                'ansible_user': d['user'],
                'ansible_host': d['address'],
                'ansible_port': d['port'],
                'ansible_private_key_file': d['identity_file'],
                'connection': 'ssh',
                'ansible_ssh_common_args': ' '.join(self.ssh_connection_options),
            }
        except StopIteration:
            return {}
        except IOError:
            # Instance has yet to be provisioned , therefore the
            # instance_config is not on disk.
            return {}

    def _get_instance_config(self, instance_name):
        instance_config_dict = util.safe_load_file(self._config.driver.instance_config)

        return next(
            item for item in instance_config_dict if item['instance'] == instance_name
        )

    def sanity_checks(self):
        # FIXME(decentral1se): Implement sanity checks
        pass


def load(self):
    return EC2(self)
