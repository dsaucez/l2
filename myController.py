from controller import *
import command

class MyRouting(RESTRequestHandlerRouting):
    def getOnePath(self, src, dst):
        return self.topology.paths.onePath(_src, _dst)

    def _routing(self, switch, flow):
        # == Sanity checks ===============================================
        # determine if we already optimized the flow
        _flow = str(flow)
        if _flow in self.topology.flows.keys():
           error_msg = "Already optimal from %s for %s" % (switch, _flow)
           raise Exception(error_msg)
        self.topology.flows[_flow] = True

        # impossible to optimize if unknown destination
        if flow.dstAddr not in self.topology.hosts.keys():
           error_msg = "unknown destination"
           raise Exception(error_msg)
        # ================================================================

        # == Identify source and destination switches for the flow =======
        _src = switch
        _dst = self.topology.hosts[flow.dstAddr].switch
        # ================================================================
#        _mac = self.topology.hosts[flow.dstAddr].mac

        # == Pick one path ===============================================
        _path = self.getOnePath(_src, _dst)
        # ================================================================

	# compute the port to use on each switch on the (_src, _dst) path
        print "Compute optimal path:"
        commands = list()
        for i in range(0, len(_path)):
            _src = _path[i]
	    # For the switch connected to the destination host, get the port to
	    # the host
            if i == len(_path) - 1:
               _portid = self.topology.hosts[flow.dstAddr].switch_port 
	    # For switches on the path to the host, get the port to the
	    # next-hop
            else:
                _neighbor = _path[i+1]
                _portid = self.topology.G.edge[_src][_neighbor][_src]
            # Command to run on the switch to add the flow
            _cmd = command.flowPort(flow, _portid)

	    # do not push the command to the switch that made the request in
	    # order to update it last (to avoid loops)
            if i == 0:
                commands.append(_cmd)
            # push the MAC:PORT on the other switches on the path
            else:
                try:
                    self.pushCommand(_src, _cmd)
                except Exception as e:
      	            print "Error with southbound 2", e
        return commands

if __name__ == '__main__':
    main(MyRouting)
