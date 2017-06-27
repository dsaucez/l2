#!/usr/bin/ruby
require 'distem'

img_p4 = "file:///home/dsaucez/p4/p4-tornado-lxc-img.tar.gz"
img = "file:///home/dsaucez/p4/client-lxc-img.tar.gz"
hosts = ARGV[0].split(',')


Distem.client { |cl|



  puts "Creat networks..."
  
  # admin network
  cl.vnetwork_create('adm', '220.0.0.0/8', {'network_type' => 'vxlan'})
 
  # control network
  cl.vnetwork_create('ctrlnet', '10.164.0.0/24', {'network_type' => 'vxlan'})

  # data networks
  cl.vnetwork_create('s10net', '10.164.10.0/24', {'network_type' => 'vxlan'})
  cl.vnetwork_create('s20net', '10.164.20.0/24', {'network_type' => 'vxlan'})
  cl.vnetwork_create('s10-s20net', '10.164.120.0/24', {'network_type' => 'vxlan'})

  # Create the nodes
  h = 0
  nodes = [ ]
  node = 'controller'
  nodes.push(node)
  cl.vnode_create(node,
         {
           'host' => hosts[h],
           'vfilesystem' =>{'image' => img_p4,'shared' => true},
           'vifaces' => [
                         {'name' => 'ifadm', 'vnetwork' => 'adm', 'address' => '220.0.0.1'},
                         {'name' => 'if0', 'vnetwork' => 'ctrlnet', 'address' => '10.164.0.1'},
                        ]
         })
  
  h += 1
  node = 's10'
  nodes.push(node)
  cl.vnode_create(node,
         {
           'host' => hosts[h],
           'vfilesystem' =>{'image' => img_p4,'shared' => true},
           'vifaces' => [
                         {'name' => 'ifadm', 'vnetwork' => 'adm', 'address' => '220.0.0.10'},
                         {'name' => 'if0', 'vnetwork' => 'ctrlnet', 'address' => '10.164.0.10'},
                         {'name' => 'if1', 'vnetwork' => 's10-s20net', 'address' => '10.164.120.10', 'macaddress' => '1e:de:ad:10:20:10'},
                         {'name' => 'if2', 'vnetwork' => 's10net', 'address' => '10.164.10.10', 'macaddress' => '1e:de:ad:10:00:10'},
                        ]
         })
  
  h += 1
  node = 's20'
  nodes.push(node)
  cl.vnode_create(node,
         {
           'host' => hosts[h],
           'vfilesystem' =>{'image' => img_p4,'shared' => true},
	   'vifaces' => [
                         {'name' => 'ifadm', 'vnetwork' => 'adm', 'address' => '220.0.0.20'},
                         {'name' => 'if0', 'vnetwork' => 'ctrlnet', 'address' => '10.164.0.20'},
                         {'name' => 'if1', 'vnetwork' => 's10-s20net', 'address' => '10.164.120.20', 'macaddress' => '1e:de:ad:10:20:20'},
                         {'name' => 'if2', 'vnetwork' => 's20net', 'address' => '10.164.20.20', 'macaddress' => '1e:de:ad:20:00:20'},
                        ]
         })
  
  h += 1
  node = 'h11'
  nodes.push(node)
  cl.vnode_create(node,
         {
           'host' => hosts[h],
           'vfilesystem' =>{'image' => img,'shared' => true},
           'vifaces' => [
                         {'name' => 'ifadm', 'vnetwork' => 'adm', 'address' => '220.0.0.11'},
                         {'name' => 'if1', 'vnetwork' => 's10net', 'address' => '10.164.10.11', 'macaddress' => '1e:de:ad:10:00:11'},
                        ]
         })
   
  h += 1
  node = 'h21'
  nodes.push(node)
  cl.vnode_create(node,
         {
           'host' => hosts[h],
           'vfilesystem' =>{'image' => img,'shared' => true},
	   'vifaces' => [
                         {'name' => 'ifadm', 'vnetwork' => 'adm', 'address' => '220.0.0.21'},
                         {'name' => 'if1', 'vnetwork' => 's20net', 'address' => '10.164.20.21', 'macaddress' => '1e:de:ad:20:00:21'},
                        ]
         })

  puts nodes

  puts "Starting vnodes..."
  cl.vnodes_start(nodes)
  puts "Waiting for vnodes to be here..."
  sleep(30)
  ret = cl.wait_vnodes({'vnodes' => nodes,'timeout' => 1200, 'port' => 22})
  if ret
    puts "Setting global /etc/hosts..."
    cl.set_global_etchosts

    puts "Setting the nodes..."
    # Add a route to s20 network on s10 via s20
    cl.vnode_execute('s10', "ip route add 10.164.20.0/24 via 10.164.120.20")
    # Add a route to s20 network on h11 via s10
    cl.vnode_execute('h11', "ip route add 10.164.20.0/24 via 10.164.10.10")

    # Add a route to s10 network on s20 via s10
    cl.vnode_execute('s20', "ip route add 10.164.10.0/24 via 10.164.120.10")
    # Add a route to s10 network on h21 via s20
    cl.vnode_execute('h21', "ip route add 10.164.10.0/24 via 10.164.20.20")

    # Deactivate forwarding on s10 and s20
    cl.vnode_execute('s10', "sysctl -w net.ipv4.ip_forward=0")
    cl.vnode_execute('s20', "sysctl -w net.ipv4.ip_forward=0")

    puts "Done"
  else
    puts "vnodes are unreachable"
  end
}
