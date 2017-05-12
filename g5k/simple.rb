#!/usr/bin/ruby
require 'distem'

img_p4 = "file:///home/dsaucez/p4/p4-tornado-networkx-lxc-img.tar.gz"
img = "file:///home/dsaucez/p4/client-lxc-img.tar.gz"
hosts = ARGV[0].split(',')


Distem.client { |cl|

  cl.vnetwork_create('adm', '220.0.0.0/8', {'network_type' => 'vxlan'})

  cl.vnetwork_create('vnet10-11', '10.42.0.0/16', {'network_type' => 'vxlan'})
  cl.vnetwork_create('vnet10-12', '10.42.0.0/16', {'network_type' => 'vxlan'})
  
  nodes = ['h11', 'h12', 's10']
  cl.vnode_create('h11',
         {
           'host' => hosts[0],
           'vfilesystem' =>{'image' => img,'shared' => true},
           'vifaces' => [
                         {'name' => 'ifadm', 'vnetwork' => 'adm', 'address' => '220.0.0.11'},
                         {'name' => 'if0', 'vnetwork' => 'vnet10-11', 'address' => '10.42.11.11', 'macaddress' => '1e:de:ad:10:11:11'},
                        ]
         })
   cl.vnode_create('h12',
         {
           'host' => hosts[1],
           'vfilesystem' =>{'image' => img,'shared' => true},
           'vifaces' => [
                         {'name' => 'ifadm', 'vnetwork' => 'adm', 'address' => '220.0.0.12'},
                         {'name' => 'if0', 'vnetwork' => 'vnet10-12', 'address' => '10.42.12.12', 'macaddress' => '1e:de:ad:10:12:12'},
                        ]
         })


  cl.vnode_create('s10',
         {
           'host' => hosts[2],
           'vfilesystem' =>{'image' => img_p4,'shared' => true},
           'vifaces' => [
                         {'name' => 'ifadm', 'vnetwork' => 'adm', 'address' => '220.0.0.10'},
                         {'name' => 'if11', 'vnetwork' => 'vnet10-11', 'address' => '10.42.11.10', 'macaddress' => '1e:de:ad:10:11:10'},
                         {'name' => 'if12', 'vnetwork' => 'vnet10-12', 'address' => '10.42.12.10', 'macaddress' => '1e:de:ad:10:12:10'},
                        ]
         })


  puts "Starting vnodes..."
  cl.vnodes_start(nodes)
  puts "Waiting for vnodes to be here..."
  sleep(30)
  ret = cl.wait_vnodes({'vnodes' => nodes,'timeout' => 1200, 'port' => 22})
  if ret
    puts "Setting global /etc/hosts..."
    cl.set_global_etchosts

    puts "Setting the nodes..."
    # We Add a default route to h11
    cl.vnode_execute('h11', "ip route add 0.0.0.0/0 via 10.10.11.10")
    # We Add a default route to h12
    cl.vnode_execute('h12', "ip route add 0.0.0.0/0 via 10.10.12.10")
    puts "Done"
  else
    puts "vnodes are unreachable"
  end
}
