import uuid

class Host:
    def __init__(self, ip, mac, switch, switch_port):
        self.ip = ip
        self.mac = mac
        self.switch = switch
        self.switch_port = switch_port
        self.uuid = uuid.uuid1()

    def update(self, mac, switch, switch_port):
        self.mac = mac
        self.switch = switch
        self.switch_port = switch_port

    def __str__(self):
        return str(self.uuid)

    def attributes(self):
        return {
            "ip": self.ip,
            "mac": self.mac,
            "switch":self.switch,
            "switch_port":self.switch_port,
            "uuid": str(self.uuid),
            "forward_port": -1
            }
