#!/usr/bin/env python
#
# pip install shade

import argparse
import sys
import os
import shade
import json


FILE_PATH = os.path.abspath(__file__)


class OpenStack(object):
    def __init__(self, conf):
        self.conf = conf
        self._cloud = None

    @property
    def cloud(self):
        if not self._cloud:
            self._cloud = shade.OpenStackCloud(
                    auth_url=self.conf.auth_url,
                    username=self.conf.username,
                    password=self.conf.password,
                    project_name=self.conf.project_name,
                    user_domain_id='default',
                    identity_api_version='3',
                    project_domain_id='default')
        return self._cloud

    def get_keystone_users(self, *args):
        ks = self.cloud.keystone_client
        return len(ks.users.list())

    def get_keystone_projects(self, *args):
        ks = self.cloud.keystone_client
        return len(ks.projects.list())

    def get_keystone_roles(self, *args):
        ks = self.cloud.keystone_client
        return len(ks.roles.list())

    def get_keystone_domains(self, *args):
        ks = self.cloud.keystone_client
        return len(ks.domains.list())

    def get_keystone_services(self, *args):
        ks = self.cloud.keystone_client
        return len(ks.services.list())

    def get_keystone_endpoints(self, *args):
        ks = self.cloud.keystone_client
        return len(ks.endpoints.list())

    def _get_statistics(self):
        if not getattr(self, 'hypervisor_stats', None):
            nova = self.cloud.nova_client
            self.hypervisor_stats = nova.hypervisor_stats.statistics()
        return self.hypervisor_stats

    def get_nova_vcpus(self, *args):
        return self._get_statistics().vcpus

    def get_nova_vcpus_used(self, *args):
        return self._get_statistics().vcpus_used

    def get_nova_memory(self, *args):
        return self._get_statistics().memory_mb

    def get_nova_memory_used(self, *args):
        return self._get_statistics().memory_mb_used

    def get_nova_disk(self, *args):
        return self._get_statistics().local_gb

    def get_nova_disk_used(self, *args):
        return self._get_statistics().local_gb_used

    def get_nova_running_vms(self, *args):
        return self._get_statistics().running_vms

    def _get_nova_services(self):
        return self.cloud.nova_client.services.list()

    def get_nova_service_host(self, binary, *args):
        services = self._get_nova_services()
        hosts = [] 
        for service in services:
             if service.binary == binary:
                 hosts.append(service.host)        
        return hosts

    def get_service_nova_scheduler_up(self, *args):
        services = self._get_nova_services()
        return len([service for service in services
                    if service.state == 'up'
                    and service.binary == 'nova-scheduler'])

    def get_service_down_nova_scheduler(self, host, *args):
        services = self._get_nova_services()
#        return len([service for service in services
#                    if service.state == 'down'
#                    and service.binary == 'nova-scheduler'])
        ret = 0 
        for service in services:
            if service.state == 'down' and service.binary == 'nova-scheduler' and service.host == host:
                ret = 1
        return ret


    def get_service_nova_scheduler_disabled(self, *args):
        services = self._get_nova_services()
        return len([service for service in services
                    if service.status != 'enabled'
                    and service.binary == 'nova-scheudler'])

    def get_service_nova_compute_up(self, *args):
        services = self._get_nova_services()
        return len([service for service in services
                    if service.state == 'up'
                    and service.binary == 'nova-compute'])

    def get_service_down_nova_compute(self, host, *args):
        services = self._get_nova_services()
        #return len([service for service in services
        #            if service.state == 'down'
        #            and service.binary == 'nova-compute'])
        ret = 0 
        for service in services:
            if service.state == 'down' and service.binary == 'nova-compute' and service.host == host:
                ret = 1
        return ret

    def get_service_nova_compute_disabled(self, *args):
        services = self._get_nova_services()
        return len([service for service in services
                    if service.status != 'enabled'
                    and service.binary == 'nova-compute'])

    def get_service_nova_conductor_up(self, *args):
        services = self._get_nova_services()
        return len([service for service in services
                    if service.state == 'up'
                    and service.binary == 'nova-conductor'])

    def get_service_down_nova_conductor(self, host, *args):
        services = self._get_nova_services()
#        return len([service for service in services
#                    if service.state == 'down'
#                    and service.binary == 'nova-conductor'])
        ret = 0 
        for service in services:
            if service.state == 'down' and service.binary == 'nova-conductor' and service.host == host:
                ret = 1
        return ret


    def get_service_nova_conductor_disabled(self, *args):
        services = self._get_nova_services()
        return len([service for service in services
                    if service.status != 'enabled'
                    and service.binary == 'nova-conductor'])

    def get_service_nova_consoleauth_up(self, *args):
        services = self._get_nova_services()
        return len([service for service in services
                    if service.state == 'up'
                    and service.binary == 'nova-consoleauth'])

    def get_service_down_nova_consoleauth(self, host, *args):
        services = self._get_nova_services()
#        return len([service for service in services
#                    if service.state == 'down'
#                    and service.binary == 'nova-consoleauth'])
        ret = 0 
        for service in services:
            if service.state == 'down' and service.binary == 'nova-consoleauth' and service.host == host:
                ret = 1
        return ret


    def get_service_nova_consoleauth_disabled(self, *args):
        services = self._get_nova_services()
        return len([service for service in services
                    if service.status != 'enabled'
                    and service.binary == 'nova-consoleauth'])

    def _get_all_servers(self):
        nova_client = self.cloud.nova_client
        search_opts = {
            'all_tenants': 1
        }
        return nova_client.servers.list(search_opts=search_opts)

    def get_nova_instance_active(self, *args):
        servers = self._get_all_servers()
        return len([server for server in servers
                    if server.status == 'ACTIVE'])

    def get_nova_instance_error(self, *args):
        servers = self._get_all_servers()
        return len([server for server in servers
                    if server.status == 'ERROR'])

    def get_nova_instance_others(self, *args):
        servers = self._get_all_servers()
        return len([server for server in servers
                    if server.status != 'ACTIVE'
                    and server.status != 'ERROR'])

    def _get_all_images(self):
        return self.cloud.list_images()

    def get_glance_images(self, *args):
        images = self._get_all_images()
        return len(images)

    def get_glance_images_public(self, *args):
        images = self._get_all_images()
        return len([image for image in images if
                    image['visibility'] == 'public'])

    def get_glance_images_private(self, *args):
        images = self._get_all_images()
        return len([image for image in images if
                    image['visibility'] != 'public'])

    def get_neutron_networks(self, *args):
        return len(self.cloud.neutron_client.list_networks()['networks'])

    def get_neutron_ports(self, *args):
        return len(self.cloud.neutron_client.list_ports()['ports'])

    def get_neutron_subnets(self, *args):
        return len(self.cloud.neutron_client.list_subnets()['subnets'])

    def get_neutron_routers(self, *args):
        return len(self.cloud.neutron_client.list_routers()['routers'])

    def get_neutron_floatingips(self, *args):
        return len(self.cloud.neutron_client.list_floatingips()['floatingips'])

    def _get_neutron_agents(self, binary, alive=True, admin_state_up=True):
        agents = self.cloud.neutron_client.list_agents()['agents']
        return len([agent for agent in agents if
                    agent['binary'] == binary and
                    agent['alive'] == alive and
                    agent['admin_state_up'] == admin_state_up])

    def get_service_neutron_dhcp_up(self, *args):
        return self._get_neutron_agents('neutron-dhcp-agent')

    def get_service_down_neutron_dhcp(self, *args):
        return self._get_neutron_agents('neutron-dhcp-agent',
                                        alive=False)

    def get_service_neutron_dhcp_disabled(self, *args):
        return self._get_neutron_agents('neutron-dhcp-agent',
                                        admin_state_up=False)

    def get_service_neutron_l3_up(self, *args):
        return self._get_neutron_agents('neutron-l3-agent')

    def get_service_down_neutron_l3(self, *args):
        return self._get_neutron_agents('neutron-l3-agent',
                                        alive=False)

    def get_service_neutron_l3_disabled(self, *args):
        return self._get_neutron_agents('neutron-l3-agent',
                                        admin_state_up=False)

    def get_service_neutron_metadata_up(self, *args):
        return self._get_neutron_agents('neutron-metadata-agent')

    def get_service_down_neutron_metadata(self, *args):
        return self._get_neutron_agents('neutron-metadata-agent',
                                        alive=False)

    def get_service_neutron_metadata_disabled(self, *args):
        return self._get_neutron_agents('neutron-metadata-agent',
                                        admin_state_up=False)

    def get_service_neutron_openvswitch_up(self, *args):
        return self._get_neutron_agents('neutron-openvswitch-agent')

    def get_service_down_neutron_openvswitch(self, *args):
        return self._get_neutron_agents('neutron-openvswitch-agent',
                                        alive=False)

    def get_service_neutron_openvswitch_disabled(self, *args):
        return self._get_neutron_agents('neutron-openvswitch-agent',
                                        admin_state_up=False)

    def _get_volume(self, resource):
        search_opts = {
            'all_tenants': 1
        }
        resource_mgnt = getattr(self.cloud.cinder_client,
                                resource)
        return resource_mgnt.list(search_opts=search_opts)

    def get_cinder_pools_name(self, *args):
        pools = self.cloud.cinder_client.pools.list()
        pools_name = []
        for pool in pools:
            pools_name.append(pool.name)
        return pools_name

    def get_cinder_pool(self, pool_name, method, *args):
        pools = self.cloud.cinder_client.pools.list(detailed=True)
        free_capacity_gb = 0
        total_capacity_gb = 0
        for pool in pools:
            if pool.name == pool_name:
                free_capacity_gb = pool.free_capacity_gb
                total_capacity_gb = pool.total_capacity_gb
                if method == 'free':
                    return free_capacity_gb
                elif method == 'total':
                    return total_capacity_gb
                else:
                    return '0'

    def get_cinder_volumes(self, *args):
        return len(self._get_volume('volumes'))

    def get_cinder_snapshots(self, *args):
        return len(self._get_volume('volume_snapshots'))

    def get_cinder_backups(self, *args):
        return len(self._get_volume('backups'))

    def get_cinder_types(self, *args):
        return len(self._get_volume('volume_types'))

    def _get_cinder_service(self, binary, state=None, status=None):
        services = self.cloud.cinder_client.services.list()
        count = 0
        for service in services:
            if (service.binary != binary or
                    state and service.state != state or
                    status and service.status != status):
                continue
            count += 1
        return count

    def get_service_cinder_backup_up(self, *args):
        return self._get_cinder_service('cinder-backup', state='up')

    def get_service_down_cinder_backup(self, *args):
        return self._get_cinder_service('cinder-backup', state='down')

    def get_service_cinder_backup_disabled(self, *args):
        return self._get_cinder_service('cinder-backup', status='disabled')

    def get_service_cinder_volume_up(self, *args):
        return self._get_cinder_service('cinder-volume', state='up')

    def get_service_down_cinder_volume(self, *args):
        return self._get_cinder_service('cinder-volume', state='down')

    def get_service_cinder_volume_disabled(self, *args):
        return self._get_cinder_service('cinder-volume', status='disabled')

    def get_service_cinder_scheduler_up(self, *args):
        return self._get_cinder_service('cinder-scheduler', state='up')

    def get_service_down_cinder_scheduler(self, *args):
        return self._get_cinder_service('cinder-scheduler', state='down')

    def get_service_cinder_scheduler_disabled(self, *args):
        return self._get_cinder_service('cinder-scheduler', status='disabled')


lld_mapping = {
    'keystone.users': 'Users',
    'keystone.projects': 'Projects',
    'keystone.roles': 'Roles',
    'keystone.domains': 'Domains',
    'keystone.services': 'Services',
    'keystone.endpoints': 'Endpoints',
    'nova.vcpus': 'Vcpus',
    'nova.memory': 'Memory',
    'nova.disk': 'Disks',
    'nova.vcpus_used': 'Vcpu Used',
    'nova.memory_used': 'Memory Used',
    'nova.disk_used': 'Disks Used',
    'nova.running_vms': 'Running VMs',
    'nova.instance.active': 'Active Instances',
    'nova.instance.error': 'Error Instances',
    'nova.instance.others': 'Other Status Instances',
    'glance.images': 'Images',
    'glance.images.public': 'Public Images',
    'glance.images.private': 'Private Images',
    'neutron.networks': 'Networks',
    'neutron.subnets': 'Subnets',
    'neutron.routers': 'Routers',
    'neutron.ports': 'Ports',
    'neutron.floatingips': 'Floating IPs',
    'cinder.volumes': 'Volumes',
    'cinder.snapshots': 'Snapshots',
    'cinder.backups': 'Backups',
    'cinder.types': 'Types',
    'service.nova.scheduler.up': 'nova-scheduler up',
    'service.down.nova.scheduler': 'nova-scheduler down',
    'service.nova.scheduler.disabled': 'nova-scheduler disabled',
    'service.nova.compute.up': 'nova-compute up',
    'service.down.nova.compute': 'nova-compute down',
    'service.nova.compute.disabled': 'nova-compute disabled',
    'service.nova.conductor.up': 'nova-conductor up',
    'service.down.nova.conductor': 'nova-conductor down',
    'service.nova.conductor.disabled': 'nova-conductor disabled',
    'service.nova.consoleauth.up': 'nova-consoleauth up',
    'service.down.nova.consoleauth': 'nova-consoleauth down',
    'service.nova.consoleauth.disabled': 'nova-consoleauth disabled',
    'service.neutron.dhcp.up': 'neutron-dhcp-agent up',
    'service.down.neutron.dhcp': 'neutron-dhcp-agent down',
    'service.neutron.dhcp.disabled': 'neutron-dhcp-agent disalbed',
    'service.neutron.l3.up': 'neutron-l3-agent up',
    'service.down.neutron.l3': 'neutron-l3-agent down',
    'service.neutron.l3.disabled': 'neutron-l3-agent disalbed',
    'service.neutron.metadata.up': 'neutron-metadata-agent up',
    'service.down.neutron.metadata': 'neutron-metadata-agent down',
    'service.neutron.metadata.disabled': 'neutron-metadata-agent disalbed',
    'service.neutron.openvswitch.up': 'neutron-openvswitch-agent up',
    'service.down.neutron.openvswitch': 'neutron-openvswitch-agent down',
    'service.neutron.openvswitch.disabled':
        'neutron-openvswitch-agent disalbed',
    'service.cinder.backup.up': 'cinder-backup up',
    'service.down.cinder.backup': 'cinder-backup down',
    'service.cinder.backup.disabled': 'cinder-backup disabled',
    'service.cinder.volume.up': 'cinder-volume up',
    'service.down.cinder.volume': 'cinder-volume down',
    'service.cinder.volume.disabled': 'cinder-volume disabled',
    'service.cinder.scheduler.up': 'cinder-scheduler up',
    'service.down.cinder.scheduler': 'cinder-scheduler down',
    'service.cinder.scheduler.disabled': 'cinder-scheduler disabled',
    }


def lld(conf):
    data = []
    openstack = OpenStack(conf)
    if conf.target == 'cinder.pool':
#        openstack = OpenStack(conf)
        cinder_pools_name = openstack.get_cinder_pools_name()
        for cinder_pool_name in cinder_pools_name:
            key = cinder_pool_name.replace('@','+').replace('#','/')
            value = 'Cinder Pool ' + cinder_pool_name
            item = {"{#NAME}": key,
                    "{#HUMAN}": value}
            data.append(item)
    else:
        for key, value in lld_mapping.items():
            if conf.target and not key.startswith(conf.target):
                continue
            service = value.split()[0]
            if service.startswith('nova') and value.split()[1] == 'down':
                ret = openstack.get_nova_service_host(service)
                for host in ret:   
                    item = {"{#NAME}": key,
                            "{#HOST}": host,                
                            "{#HUMAN}": value}
                    data.append(item)
            else:
                item = {"{#NAME}": key,
                        "{#HUMAN}": value}
                data.append(item)

    return {"data": data}


def test(conf):
    ret = {}
    ret['lld'] = lld(conf)
    openstack = OpenStack(conf)
    for key, value in lld_mapping.items():
        if conf.target and not key.startswith(conf.target):
            continue
        method = 'get_' + key.replace('.', '_')
        ret[key] = getattr(openstack, method)()
    return ret


def main():
    parse = argparse.ArgumentParser()
    parse.add_argument('--auth-url')
    parse.add_argument('--username')
    parse.add_argument('--password')
    parse.add_argument('--host')
    parse.add_argument('--project-name')
    parse.add_argument('-t', '--target')
    parse.add_argument('action',
                       choices=['list',
                                'get',
                                'test',
                                'usage'])
    conf = parse.parse_args(sys.argv[1:])
    openstack = OpenStack(conf)
    if conf.action == 'list':
        ret = json.dumps(lld(conf))
    elif conf.action == 'test':
        ret = json.dumps(test(conf))
    elif conf.action == 'get':
        if not conf.target.startswith('cinder.pool'):
            target = conf.target.replace('.', '_')
            method = 'get_' + target
            ret = getattr(openstack, method)(conf.host)
        else:
            pool_name = conf.target.split('.', 3)[3].replace('+','@').replace('/','#')
            method = conf.target.split('.')[2]
            ret = getattr(openstack, 'get_cinder_pool')(pool_name, method)
    elif conf.action == 'usage':
        if not all([conf.auth_url, conf.username, conf.password]):
            raise ValueError('auth-url, username and password is required')

        usages = []
        ctxt = {
            'auth_url': conf.auth_url,
            'username': conf.username,
            'password': conf.password,
            'file_path': FILE_PATH
        }
        usages.append('UserParameter=openstack.list[*],%(file_path)s --auth-url %(auth_url)s --username %(username)s --password %(password)s list --target $1' % ctxt)
        usages.append('UserParameter=openstack.get[*],%(file_path)s --auth-url %(auth_url)s --username %(username)s --password %(password)s get --target $1 --host $2' % ctxt)
        ret = '\n'.join(usages)
    print(ret)


if __name__ == "__main__":
    main()
