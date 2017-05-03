import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.queues
import tornado.web
import json
import sys
import os
import subprocess
from subprocess import Popen, PIPE

def send_to_CLI(cmd, cli_port):
    """
    Send the command `cmd` to the CLI of the P4 switch
    """
    this_dir = os.path.dirname(os.path.realpath(__file__))
    args = [os.path.join(this_dir, "sswitch_CLI2.sh"), str(cli_port)]
    p = Popen(args, stdout=PIPE, stdin=PIPE)
    output = p.communicate(input=cmd)[0]
    return output

# == sanity checks
if len(sys.argv) != 2:
   print "usage %s <HTTP port>" % (sys.argv[0])
   exit(-1)

PORT = int(sys.argv[1])

class RESTRequestHandlerCmds(tornado.web.RequestHandler):
    # POST /host
    def post(self):
        results = list();
        self.set_header("Content-Type", 'application/json; charset="utf-8"')
        params = json.loads(self.request.body.decode())
        print "Execute commands: ", str(params["commands"])
        for cmd in params["commands"]:
           r = send_to_CLI(cmd, params["thrift_port"])
           results.append((cmd, r))
        self.set_status(201)
        self.finish(json.dumps({"output":results}))

# launch server
rest_app = tornado.web.Application([
           ("/commands", RESTRequestHandlerCmds)
           ])
rest_server = tornado.httpserver.HTTPServer(rest_app)
rest_server.listen(PORT)
tornado.ioloop.IOLoop.current().start()
print "ICI"
