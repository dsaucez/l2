from controller import *
import command

class MyRouting(RESTRequestHandlerRouting):

    def _routing(self, switch, flow):
        # determine if we already optimized the flow
        print ">>>>>>>>>>>???>>", self.url
        _flow = str(flow)
        if _flow in self.topology.flows.keys():
           error_msg = ">>>>>>>>>>> already optimal here from %s for %s" % (switch, _flow)
           print  error_msg
           raise Exception(error_msg)
        self.topology.flows[_flow] = True

        # impossible to optimize if unknown destination
        if flow.dstAddr not in self.topology.hosts.keys():
           self.set_status(204)
           self.finish()
           return

        # from what switch to what switch?
        _src = switch
        _dst = self.topology.hosts[flow.dstAddr].switch
        _mac = self.topology.hosts[flow.dstAddr].mac

        # pick one path 
        _path = self.topology.paths.onePath(_src, _dst)

	# compute the port to use on each switch on the (_src, _dst) path
        print "Compute optimal path:"
        _resp = {"commands":list()}
        for i in range(0, len(_path)):
            _src = _path[i]
	    # For the switch connected to the host, get the port to the host
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
                _resp["commands"].append(_cmd)
            # push the MAC:PORT on the other switches on the path
            else:
                try:
                    self.pushCommand(_src, _cmd)
                except Exception as e:
      	            print "Error with southbound 2", e

        return _resp

if __name__ == '__main__':
    main(MyRouting)
