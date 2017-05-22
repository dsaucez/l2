def flowPort(flow, portid):
    """
    Return the command to execute on a bmv2 switch in order to impose `portid`
    as egress port for any packet belonging to `flow`

    :param flow: flow to match
    :type flow: Flow
    
    :param portid: egress port number on the switch
    :type portid: int

    :return: the string corresponding to the command to execute on the bmv2 switch
    """
    _flow = str(flow)
    _cmd = "table_add flow_table set_fast_forward %s => %d" % (_flow, portid)
    return _cmd

def flowIgnore(flow):
    """
    Return the command to execute on a bmv2 switch in order to bypass the Flow
    table for any packet belonging to `flow`

    :param flow: flow to match
    :type flow: Flow
    
    :return: the string corresponding to the command to execute on the bmv2 switch
    """
    _flow = str(flow)
    _cmd = "table_add flow_table _nop %s =>" %(_flow)
    return _cmd

def macPort(mac, portid):
    """
    Return the command to execute on a bmv2 switch in order to impose `portid`
    as egress port for any frame with `mac` destination MAC address

    :param mac: destination MAC address to match
    :type mac: string
    
    :param portid: egress port number on the switch
    :type portid: int

    :return: the string corresponding to the command to execute on the bmv2 switch
    """
    _cmd = "table_add mac_table set_out_port %s => %d" % (mac, portid)
    return _cmd
