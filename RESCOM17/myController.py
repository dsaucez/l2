import sys
sys.path.append("../")
from controller import *
import command

class MyRouting(RESTRequestHandlerRouting):
    def getPath(self, src, dst, flow):
        """
	Returns one valid path between switch `src` and switch `dst` in the
	opology. The path is represented as a list of string where each item
        is the name of the switch, in order from `src` to `dst`, included.
	Example:
	      if the path from src=a to dst=d is a->b->c->d, then the returned
              value is ["a", "b", "c", "d"] 

        :param src: origin switch name
        :type src: string

        :param dst: target switch name
        :type dst: string

        :param flow: Flow information
        :type flow:  Flow

        :return: a list of switch names
        """
#        raise Exception("You have to implement it!!!")
        return self.topology.paths.onePath(src, dst)

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

        # == Identify source and destination switches for the flow =======
        src = switch
        dst = self.topology.hosts[flow.dstAddr].switch

        # == Pick one path ===============================================
        path = self.getPath(src, dst, flow)

	# == Diffuse the port to use on each switch on the (src, dst) path

        # list of commands to be run on `switch`
        commands = list()

        # traverse the path
        for i in range(0, len(path)):
            _src = path[i]
	    # For the switch connected to the destination host, get the port to
	    # the host
            if i == len(path) - 1:
               portid = self.topology.hosts[flow.dstAddr].switch_port 
	    # For switches on the path to the host, get the port to the
	    # next-hop
            else:
                neighbor = path[i+1]
                portid = self.topology.G.edge[_src][neighbor][_src]

            # Commands to run on the switch to add the flow
            cmds = list()
            cmd1 = command.flowPort(flow, portid)
            cmds.append(cmd1)

	    # do not push the command to the switch that made the request in
	    # order to update it last (to avoid loops)
            if i == 0:
                for cmd in cmds:
                    commands.append(cmd)
            # push the MAC:PORT on the other switches on the path
            else:
                try:
                    self.pushCommands(_src, cmds)
                except Exception as e:
      	            print "Error with southbound 2", e
        return commands

if __name__ == '__main__':
    main(MyRouting)
