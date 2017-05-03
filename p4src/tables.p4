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

// == Tables ====================================
table ttl_table {
   reads {
       ipv4.ttl : exact;
   }
   actions {
       _nop;
       _drop;
   }
   size : 1;
}

/* Associate an IP prefix to a (next-hop, interface) pair */
table fib_table {
   reads {
      ipv4.dstAddr : lpm;
   }
   actions {
      set_next_hop;
      set_next_local;
      _drop;
      _nop;
   }
   size : 256;
}
counter fib_table_stats {
    type : bytes;
    direct: fib_table;
}

/* Associate an IP to a MAC address */
table arp_table {
   reads {
      super_meta.nh : exact;
   }
   actions {
      set_dst_mac;
      _drop;
      _nop;
   }
   size : 65535;
}
counter arp_table_stats {
    type : bytes;
    direct: arp_table;
}

table mac_table {
   reads {
      ethernet.dstAddr : exact;
   }
   actions {
      set_out_port;
      _drop;
   }
}
counter mac_table_stats {
    type : bytes;
    direct : mac_table;
}

/* Define the source MAC address to use for forwarding */
table port_table {
   reads {
      standard_metadata.egress_port : exact;
   }
   actions {
      set_src_mac;
      _drop;
   }
   size : 256;
}
counter port_table_stats {
    type : bytes;
    direct: port_table;
}

table flow_table {
   reads {
      ipv4.srcAddr : exact;
      ipv4.dstAddr : exact;
      ipv4.protocol: exact;
      super_meta.srcPort  : exact;
      super_meta.dstPort  : exact;
   }
   actions {
      _nop;
      _drop;
      add_flow;
      set_fast_forward;
   }
   size: 65535;
}
counter flow_table_stats {
   type : bytes;
   direct : flow_table;
}

table no_arp_table {
   reads {
      ethernet.etherType : exact;
   }
   actions {
      _nop;
      _drop;
   }
   size: 2;
}
