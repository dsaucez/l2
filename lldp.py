from scapy.packet import *
from scapy.fields import *
from scapy.layers.l2 import Ether, sendp

TLV_DICTIONARY = {0x00: "End of LLDPDU",
                  0x01: "Chassis Id",
                  0x02: "Port Id",
                  0x03: "Time to Live",
                  0x04: "Port Description",
                  0x05: "System Name",
                  0x06: "System Description",
                  0x07: "System Capabilities",
                  0x08: "Management Address",
                  0x7f: "Organiation Specific"}

CHASSIS_ID_SUBTYPES = {0x00: "Reserved",
                       0x01: "Chassis component",
                       0x02: "Interface alias",
                       0x03: "Port component",
                       0x04: "MAC address",
                       0x05: "Network address",
                       0x06: "Interface name",
                       0x07: "Locally assigned"}

NETWORK_ADDRESS_TYPE = {0x01: "IPv4",
                        0x02: "IPv6"}

PORT_ID_SUBTYPES = {0x00: "Reserved",
                    0x01: "Interface alias",
                    0x02: "Port component",
                    0x03: "MAC address",
                    0x04: "Network address",
                    0x05: "Interface name",
                    0x06: "Agent circut ID",
                    0x07: "Locally assigned"}

class Chassis_Id(Packet):
    name = "Chassis ID"
    fields_desc = [BitEnumField("type", 0x01, 7, TLV_DICTIONARY),
               BitField("length", 7, 9),
               ByteEnumField("subtype", 0x04, CHASSIS_ID_SUBTYPES),
               ConditionalField(StrLenField("reserved", "", length_from=lambda x: x.length - 1),
                                lambda pkt: pkt.subtype == 0x00),
               ConditionalField(StrLenField("chassisComponent", "chassis comp", length_from=lambda x: x.length - 1),
                                lambda pkt: pkt.subtype == 0x01),
               ConditionalField(
                   StrLenField("interfaceAlias", "interface alias", length_from=lambda x: x.length - 1),
                   lambda pkt: pkt.subtype == 0x02),
               ConditionalField(StrLenField("portComponent", "port component", length_from=lambda x: x.length - 1),
                                lambda pkt: pkt.subtype == 0x03),
               ConditionalField(MACField("macaddr", "00:11:11:11:11:11"), lambda pkt: pkt.subtype == 0x04),
               ConditionalField(ByteEnumField("addrType", 0x00, NETWORK_ADDRESS_TYPE),
                                lambda pkt: pkt.subtype == 0x05),
               ConditionalField(IPField("ipaddr", "10.10.10.10"), lambda pkt: pkt.addrType == 0x01),
               ConditionalField(StrLenField("interfaceName", "yes", length_from=lambda x: x.length - 1),
                                lambda pkt: pkt.subtype == 0x06),
               ConditionalField(StrLenField("locallyAssigned", "yes", length_from=lambda x: x.length - 1),
                                lambda pkt: pkt.subtype == 0x07)]

class Port_Id(Packet):
    name = "Port ID"
    fields_desc = [BitEnumField("type", 0x02, 7, TLV_DICTIONARY),
               BitField("length", 7, 9),
               ByteEnumField("subtype", 0x03, PORT_ID_SUBTYPES),
               ConditionalField(StrLenField("reserved", "", length_from=lambda x: x.length - 1),
                                lambda pkt: pkt.subtype == 0x00),
               ConditionalField(StrLenField("interfaceAlias", "", length_from=lambda x: x.length - 1),
                                lambda pkt: pkt.subtype == 0x01),
               ConditionalField(ShortField("portComponent", None),
                                lambda pkt: pkt.subtype == 0x02),
               ConditionalField(MACField("macaddr", "de:ad:f0:0d:be:ef"), lambda pkt: pkt.subtype == 0x03),
               ConditionalField(ByteEnumField("addrType", 0x00, NETWORK_ADDRESS_TYPE),
                                lambda pkt: pkt.subtype == 0x04),
               ConditionalField(IPField("ipaddr", "10.10.10.10"), lambda pkt: pkt.addrType == 0x01),
               ConditionalField(StrLenField("interfaceName", "lo0", length_from=lambda x: x.length - 1),
                                lambda pkt: pkt.subtype == 0x05),
               ConditionalField(StrLenField("agentCircutID", "id_agent", length_from=lambda x: x.length - 1),
                                lambda pkt: pkt.subtype == 0x06),
               ConditionalField(StrLenField("locallyAssigned", "yes", length_from=lambda x: x.length - 1),
                                lambda pkt: pkt.subtype == 0x07)]


class RESTAPI(Packet):
    name = "REST API"
    fields_desc = [BitEnumField("type", 0x7F, 7, TLV_DICTIONARY),
               BitField("length", 7, 9),
               X3BytesField("OUI", 0xDEAD01),
               ByteField("sub-type", 0x01),
               StrLenField("url", "yes", length_from=lambda x: x.length - 4)]
class ThriftIP(Packet):
    name = "Thrift IP"
    fields_desc = [BitEnumField("type", 0x7F, 7, TLV_DICTIONARY),
               BitField("length", 7, 9),
               X3BytesField("OUI", 0xDEAD01),
               ByteField("sub-type", 0x02),
               StrLenField("ip", "yes", length_from=lambda x: x.length - 4)]

class ThriftPort(Packet):
    name = "Thrift port"
    fields_desc = [BitEnumField("type", 0x7F, 7, TLV_DICTIONARY),
               BitField("length", 7, 9),
               X3BytesField("OUI", 0xDEAD01),
               ByteField("sub-type", 0x03),
               StrLenField("port", "yes", length_from=lambda x: x.length - 1)]


class TTL(Packet):
    name = "TimeToLive"
    fields_desc = [BitEnumField("type", 0x03, 7, TLV_DICTIONARY),
               BitField("length", 0x02, 9),
               ShortField("seconds", 0)]


class EndOfPDU(Packet):
    name = "EndofLLDPDU"
    fields_desc = [BitEnumField("type", 0x00, 7, TLV_DICTIONARY),
               BitField("length", 0x00, 9)]


def create_lldp_packet(mac_addr, switch_name, port_id):
    # indicate the swith name
    chassis_tlv = Chassis_Id()
    chassis_tlv.subtype = 0x07
    chassis_tlv.length = len(switch_name) + 1
    chassis_tlv.locallyAssigned = switch_name

    # indicate the port ID
    port_tlv = Port_Id()
    port_tlv.subtype = 0x7
    port_tlv.length = len(port_id) + 1
    port_tlv.locallyAssigned = port_id

    # TTL
    ttl_tlv = TTL()
    ttl_tlv.length = 2
    ttl_tlv.seconds = 0
    
    # The end 
    end_tlv = EndOfPDU()

    # Create the frame
    frame = Ether()
    frame.src = mac_addr
    frame.dst = '01:80:c2:00:00:0e'
    frame.type = 0x88cc

    packet = frame / chassis_tlv / port_tlv / ttl_tlv / end_tlv
    return packet


