#!/usr/bin/env python2
# coding=utf-8

import argparse
from keystoneauth1 import session
from keystoneauth1.identity import v3 as auth_v3
from novaclient import client as noclient
import neutronclient
from neutronclient.v2_0 import client as neclient
import copy
import sys
import logging
import subprocess

LOG = logging.getLogger(__name__)

auth = auth_v3.Password(auth_url='http://xxx.xxx.xxx.xxx:35357/v3',
                        username='admin',
                        password='xxxxxx',
                        project_name='admin',
                        user_domain_name='Default',
                        project_domain_name='Default'
                        )
sess = session.Session(auth=auth)

def get_nova_client(api_version='2.1'):
    return noclient.Client(
        api_version,
        region_name='RegionOne',
        endpoint_type='internal',
        session=sess)

def get_neutron_client():
    return neclient.Client(
        region_name='RegionOne',
        interface='internal',
        session=sess)

class PingTest(object):
    
    def __init__(self,conf):
        self.nova = get_nova_client()
        self.neutron = get_neutron_client()
        self.server = conf.server

    #run linux command 
    def shell(self,cmds):
        try:
            LOG.debug ('Runing cmd: %s', cmds)
            return subprocess.check_output(cmds)
        except subprocess.CalledProcessError:
            LOG.exception ('Run command failed: %s', cmds)
            return ''        
    
    def ping_cmd(self,ip):
        #ping one packet
        cmds = ['ping','-c','1','%s' %ip ]
        return cmds

    def enter_ns_cmd(self,ns):
        cmds = ['ip','netns','exec','%s' %ns]      
        return cmds      
 
    def get_info(self):
        if self.server:
            try:
                interface_list = self.nova.servers.interface_list(self.server)
            except:
                LOG.ERROR ('this server id:%s  no interface!',self.server)  

            #get ns by interface
            for interface in interface_list:
                #print (dir(interface))
                port_id = getattr(interface, "port_id", '')
                net_id  = getattr(interface, "net_id", '')
                addr = getattr(interface, "fixed_ips", '')
                ip = addr[0]['ip_address']
      
                #get gw port
                gw_port = self.neutron.list_ports(network_id=net_id,device_owner="network:ha_router_replicated_interface") 
                if gw_port['ports']: 
                    #get router id
                    router_id = gw_port['ports'][0]['device_id']
  
                    l3_agents = self.neutron.list_l3_agent_hosting_routers(router_id)
                    for i in l3_agents['agents']:
                       num = 0
                       if i['ha_state'] == "active":
                          host = i['host']
                          num += 1
                       if num > 1:
                          LOG.ERROR ("the vrouter: %s is not normal!", %router_id)               
                          raise Exception('vrouter ha error!')
                    return host,router_id,ip 
                else:
                    l2_agents = self.neutron.list_dhcp_agent_hosting_networks(net_id) 
                    hosts = []
                    for i in l2_agents['agents']:
                        host = i['host']                      
                        hosts.append(copy.deepcopy(host)) 
                    return hosts,net_id,ip 


    def ping(self):
        hosts,ns,ip = self.get_info()
        cmd1 = self.ping_cmd(ip)
        #l3 ping 	
        if not isinstance(hosts,list):
            cmd2 = self.enter_ns_cmd("qrouter-" + ns)   
            cmd3 = ['ssh', '%s' %hosts]+cmd2+cmd1
            self.shell(cmd3)
        #l2 ping 	
        else:
            cmd2 = self.enter_ns_cmd("qdhcp-" + ns)
            for host in hosts: 
                cmd3 = ['ssh', '%s' %host]+cmd2+cmd1
                self.shell(cmd3)

def main():
    parser = argparse.ArgumentParser()
    # basic info
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-s', '--server', required=True)

    conf = parser.parse_args(sys.argv[1:])


    log_level = logging.INFO
    if conf.debug:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)
    
    ping = PingTest(conf)

    ping.ping() 

if __name__ == "__main__":
    main()


