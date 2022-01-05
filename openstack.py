# coding=utf-8

from keystoneauth1 import session
from keystoneauth1.identity import v3 as auth_v3
from novaclient import client as noclient
import cinderclient
from cinderclient.v3 import client as cinclient
import glanceclient
import glanceclient.v2.client as glclient
import neutronclient
from neutronclient.v2_0 import client as neclient
import copy
import sys


auth = auth_v3.Password(auth_url='http://xxx.xxx.xxx.xxx:35357/v3',
                        username='admin',
                        password='xxxxx',
                        project_name='admin',
                        user_domain_name='Default',
                        project_domain_name='Default',
                        )
sess = session.Session(auth=auth)


def get_nova_client(api_version='2.1'):
    return noclient.Client(
        api_version,
        endpoint_type='internal',
        session=sess)


def get_cinder_client():
    return cinclient.Client(
        interface='internal',
        session=sess)


def get_glance_client():
#    import pdb; pdb.set_trace()
    return glclient.Client(
        interface='internal',
        session=sess)


def get_neutron_client():
    return neclient.Client(
        interface='internal',
        session=sess)

class Server():
    
    def __init__(self):
        self.nova = get_nova_client()
        self.glance = get_glance_client()
        self.cinder = get_cinder_client()
        self.neutron = get_neutron_client()
        self.servers=[]
        self.server={}
    ##获取实例信息
    def server_mata(self):
        instances = self.nova.servers.list(detailed=True, search_opts={'all_tenants': '1', 'tenant_id': sys.argv[1]})
#        instances = self.nova.servers.list(detailed=True)

         ##实例数据

        for ser in instances:
##          获取实例的镜像
#           print ser
#           print ser.id
            self.server['name']=ser.name
            if ser.image:
                image_id = ser.image['id']
                self.server['image'] = self.glance.images.get(image_id).name
            try:
                flavor = self.nova.flavors.get(ser.flavor['id'])
                self.server['flavor']=flavor.name
                self.server['cpus']=flavor.vcpus
                self.server['ram']=flavor.ram / 1024
            except Exception as e:
                print(repr(e))

            self.server['key_name']=ser.key_name
            ## 实例状态
            self.server['status']=ser.status
            ## 实例创建时间
            self.server['created']=ser.created
            self.server['accessIPv4']=getattr(ser, 'accessIPv4')
            ## 实例所在主机
            self.server['host']=getattr(ser, 'OS-EXT-SRV-ATTR:host')
    
            ## 实例可用域
            self.server['availability_zone']=getattr(ser, 'OS-EXT-AZ:availability_zone', '')


            ## 获取实例ip地址
            interface_list = self.nova.servers.interface_list(ser.id)
            addr=[]
            floating_ips=[]
            interfaces=[]
            security_groups=[]
            allowed_address_pairss=[]
            for interface in interface_list:
                interface_id = getattr(interface, "id", '')
                interfaces.append(interface_id)

                port = self.neutron.show_port(interface_id)
                ## 获取port的可用地址对
                allowed_address_pairs = port['port']['allowed_address_pairs']
                if allowed_address_pairs:
                    for i in allowed_address_pairs:
                        allowed_address_pairss.append(i['ip_address'])

                ## 获取port的安全组
                security_group = '  '.join(port['port']['security_groups'])
                security_groups.append(security_group)
                ## 获取prot的ip
                addresses = port['port']['fixed_ips']
                for address in addresses:
                    addr.append(address['ip_address'])
                ## 获取port的浮动ip
                floatingip =  self.neutron.list_floatingips(port_id=interface_id)
                for floatingips in floatingip.values():
                    for floating_ip in floatingips:
                        if floating_ip['floating_ip_address']:
                            floating_ips.append(floating_ip['floating_ip_address'])

            self.server['interface_id']=interfaces
            self.server['security_groups']=security_groups
            self.server['address']=addr
            self.server['floating_ip']=floating_ips

            Volume_size = 0

            if self.nova.volumes.get_server_volumes(ser.id):
                volume_list = self.nova.volumes.get_server_volumes(ser.id)
                ## 获取实例所有卷大小之和
                for volume in volume_list:
                    volume_id = getattr(volume, "id", "")
                    volume_mata = self.cinder.volumes.get(volume_id)
                    volume_size = getattr(volume_mata, 'size', '')
                    Volume_size += volume_size

            self.server['volume'] = Volume_size

            self.servers.append(copy.deepcopy(self.server))

        return self.servers

if __name__ == '__main__':
    Ser = Server()
    Ser.server_mata()
