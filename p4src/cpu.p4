///////////////////////////////////////
#define ETHERTYPE_CPU 0xDEAD
header_type cpu_header_t {
    fields {
        preamble : 64;
        if_index : 16;
        etherType: 16;
    }
}

// == Headers for CPU
header cpu_header_t cpu_header;

field_list copy_to_cpu_fields {
	super_meta;
	standard_metadata;
}


action do_cpu_encap() {
	// CPU
	add_header(cpu_header);
        modify_field(cpu_header.etherType, ethernet.etherType);
        modify_field(ethernet.etherType, ETHERTYPE_CPU);
        modify_field(cpu_header.preamble, 0);
	modify_field(cpu_header.if_index, super_meta.ingress_port);
}

table redirect {
    reads {
        standard_metadata.instance_type : exact;
    }
    actions {
        _drop;
        _nop;
        do_cpu_encap;
    }
    size : 16;
}


action add_flow() {
	modify_field(super_meta.fast, 0);
	clone_ingress_pkt_to_egress(250, copy_to_cpu_fields);
}
