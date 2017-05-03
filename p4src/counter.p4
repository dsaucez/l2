/*
Copyright 2013-present Barefoot Networks, Inc. 

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

#include "headers.p4"
#include "tables.p4"
#include "cpu.p4"


// == Headers =================================
header ethernet_t ethernet;
header ipv4_t ipv4;
header udp_t udp;
header tcp_t tcp;


metadata super_meta_t super_meta;

// == Checksum ===============================
field_list ipv4_checksum_list {
    ipv4.version;
    ipv4.ihl;
    ipv4.diffserv;
    ipv4.totalLen;
    ipv4.identification;
    ipv4.flags;
    ipv4.fragOffset;
    ipv4.ttl;
    ipv4.protocol;
    ipv4.srcAddr;
    ipv4.dstAddr;
}

field_list_calculation ipv4_checksum {
    input {
        ipv4_checksum_list;
    }
    algorithm : csum16;
    output_width : 16;
}

calculated_field ipv4.hdrChecksum  {
    verify ipv4_checksum;
    update ipv4_checksum;
}


// == Parsers =================================
parser start {
    set_metadata(super_meta.ingress_port, standard_metadata.ingress_port);
    return parse_ethernet;
}

parser parse_ethernet {
    extract(ethernet);
    set_metadata(super_meta.etherType, ethernet.etherType);
    return select(latest.etherType) {
        ETHERTYPE_CPU  : parse_cpu_header;
        ETHERTYPE_IPV4 : parse_ipv4;
        default: ingress;
    }
}

parser parse_ipv4 {
   extract(ipv4);
   set_metadata(super_meta.srcAddr, latest.srcAddr);
   set_metadata(super_meta.dstAddr, latest.dstAddr);
   set_metadata(super_meta.protocol, latest.protocol);
   return select(latest.protocol) {
     PROTO_UDP : parse_udp;
     PROTO_TCP : parse_tcp;
     default: ingress;
   }
}

parser parse_udp {
    extract(udp);
    set_metadata(super_meta.srcPort, latest.srcPort);
    set_metadata(super_meta.dstPort, latest.dstPort);
    return select(latest.dstPort) {
      default: ingress;
    }
}

parser parse_tcp {
    extract(tcp);
    set_metadata(super_meta.srcPort, latest.srcPort);
    set_metadata(super_meta.dstPort, latest.dstPort);
    return select(latest.dstPort) {
      default: ingress;
    }
}

parser parse_cpu_header {
    extract(cpu_header);
    return select(latest.etherType) {
        ETHERTYPE_IPV4 : parse_ipv4;
        default: ingress;
    }
//    return ingress;
}

// == Actions ==================================
action _drop() {
    drop();
}

action _nop() {
}

/* Set the source mac of the frame */
action set_src_mac(smac) {
    modify_field(ethernet.srcAddr, smac);
}

/* Set the destination mac of a frame */
action set_dst_mac(dmac) {
    modify_field(ethernet.dstAddr, dmac);
}

/* Set the next-hop to use and the interface */
action set_next_hop(nh, iface) {
    modify_field(super_meta.local, 0); // has to change destination MAC
    modify_field(super_meta.nh, nh); // next-hop IP address
    modify_field(standard_metadata.egress_spec, iface); // interface to reach the next-hop
}

/* Use destination as next-hop and the interface */
action set_next_local(iface) {
    modify_field(super_meta.local, 1);  // no need to change MAC
//    modify_field(super_meta.nh, 0.0.0.0); // next-hop IP address
    modify_field(standard_metadata.egress_spec, iface); // interface to reach the next-hop
}

/* Set the output port*/
action set_out_port(iface) {
    modify_field(standard_metadata.egress_spec, iface); // interface to reach the next-hop
}

/* Set the next hop mac and interface directly */
action set_fast_forward(nh_mac, iface) {
   set_dst_mac(nh_mac);                                // impose destination mac 
   modify_field(standard_metadata.egress_spec, iface); // interface to reach the next-hop
   modify_field(super_meta.fast, 1);
}
// == Controls ===================================
control ingress {
    apply(flow_table);

    if (super_meta.fast != 1){
       // L2 switch
       apply(mac_table);        // figure out the next port to forward the packet to
/*
         // Router
         // DEPRECATED
         apply(fib_table);      // figure out the next-hop and interface to forward the packet to
         if (super_meta.local == 0) {
             apply(arp_table);      // set the MAC address of the next-hop (dest)
         }
*/
    }
}

control egress {
    if (standard_metadata.instance_type == 0){
// DEPRECATED         apply(ttl_table);
         apply(port_table);    // set the MAC address of the network port (src)
         apply(no_arp_table);  // do not forward ARP's
    }
    else {
         apply(redirect);
    }
}
