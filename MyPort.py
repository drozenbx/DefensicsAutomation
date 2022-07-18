import GlobalVariables


class MyPort:
    def __init__(self, ip, mac, virtual_ip, virtual_mac, device_name, ipv6, ipv6_LP, giga):
        self.ip = ip
        self.mac = mac
        self.virtual_ip = virtual_ip
        self.virtual_mac = virtual_mac
        self.device_name = device_name
        self.ipv6 = ipv6
        self.ipv6_LP = ipv6_LP
        self.giga = giga

    def print_data(self):
        GlobalVariables.logger.info("ip: " + self.ip)
        GlobalVariables.logger.info("mac: " + self.mac)
        GlobalVariables.logger.info("virtual_ip: " + self.virtual_ip)
        GlobalVariables.logger.info("virtual_mac: " + self.virtual_mac)
        GlobalVariables.logger.info("device_name: " + self.device_name)
        GlobalVariables.logger.info("ipv6: " + self.ipv6)
        GlobalVariables.logger.info("ipv6 LP: " + self.ipv6_LP)
        GlobalVariables.logger.info("giga: " + str(self.giga))
