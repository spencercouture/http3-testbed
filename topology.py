# from setup.process import run
import math
from process import runcmd
from dns import DNS_ADDR


class Topology:
    server_ns_tag = "-servers"
    client_ns_tag = "-clients"

    # TODO: put a limit on the length of nsid
    def __init__(self, nsid):
        # set our NS ID, and make our client/server ones for ease later
        self.nsid = nsid
        self.server_ns = f"{nsid}{Topology.server_ns_tag}"
        self.server_br = f"brd{nsid}0"
        self.client_ns = f"{nsid}{Topology.client_ns_tag}"
        self.client_br = f"brd{nsid}0"
        # internal counters for dynamic naming of additional servers/clients
        self.server_veth_id = 0
        self.client_veth_id = 0

    # brings the transit network, client/server namespaces, and dns server up
    def up(self):
        # creates the transit network
        self._create_transit_network()

        # setup the client and server namespaces
        self._setup_client_ns()
        self._setup_server_ns()

        # sets up the namespace, veth pair, and ip for the DNS server
        self._setup_dns(DNS_ADDR)


    # connects an arbitrary NS to the -clients NS with a given IP:
    # - create veth pairs
    # - add one to client NS and adds it to bridge (and bring it up)
    # - add other one to client-specific NS (must already be created)
    # - adds an address and sets the default route (in custom ns)
    def attach_client_with_ip(self, ns, ip):
        # create our dynamic names and increment our internal counter
        veth0 = f"vclt{self.nsid}{self.client_veth_id}"
        veth1 = f"vclt{self.nsid}{self.client_veth_id+1}"
        self.client_veth_id += 2
        # create the veth pair
        self.create_veth_pairs(veth0, veth1)

        # move one into the provided namespace (with the ip and default route)
        runcmd(f"ip link set {veth0} netns {ns}")
        runcmd(f"ip link set dev {veth0} up", namespace=ns)
        runcmd(f"ip addr add {ip}/24 dev {veth0}", namespace=ns)
        runcmd("ip route add default via 10.0.1.1", namespace=ns)

        # move one to the client NS on the bridge
        runcmd(f"ip link set {veth1} netns {self.client_ns}")
        runcmd(f"ip link set dev {veth1} up", namespace=self.client_ns)
        runcmd(f"ip link set {veth1} master {self.client_br}",
               namespace=self.client_ns)

    # connects an arbitrary NS to the -servers NS with a given IP:
    # - create veth pairs
    # - add one to server NS (and bring it up)
    # - add other one to server-specific NS (must already be created)
    # - adds the address (should be in 10.0.9.1/24 range)
    def attach_server_with_ip(self, ns, ip):
        # create our dynamic names and increment our internal counter
        veth0 = f"vsrv{self.nsid}{self.server_veth_id}"
        veth1 = f"vsrv{self.nsid}{self.server_veth_id+1}"
        self.server_veth_id += 2
        # create the veth pair
        self.create_veth_pairs(veth0, veth1)

        # move one into the provided namespace (with the ip and default route)
        runcmd(f"ip link set {veth0} netns {ns}")
        runcmd(f"ip link set dev {veth0} up", namespace=ns)
        runcmd(f"ip addr add {ip}/24 dev {veth0}", namespace=ns)
        runcmd("ip route add default via 10.0.9.1", namespace=ns)

        # move one to the server NS on the bridge
        runcmd(f"ip link set {veth1} netns {self.server_ns}")
        runcmd(f"ip link set dev {veth1} up", namespace=self.server_ns)
        runcmd(f"ip link set {veth1} master {self.server_br}",
               namespace=self.server_ns)

    # creates a namespace "nsid" and sets its loopback up (?)
    def create_namespace(nsid):
        runcmd(f"ip netns add {nsid}")
        runcmd("ip link set dev lo up", namespace=nsid)

    # creates a bridge "br_name" in the namespace "nsid"
    def create_bridge(ns, br_name):
        runcmd(f"ip link add {br_name} type bridge", namespace=ns)
        runcmd(f"ip link set dev {br_name} up", namespace=ns)

    # creates two veth pairs (n and n+1) and disable offloading
    def create_veth_pairs(self, v1, v2):
        runcmd(f"ip link add {v1} type veth peer name {v2}")
        runcmd(f"ethtool -K {v1} tso off gso off gro off")
        runcmd(f"ethtool -K {v1} tso off gso off gro off")

    # removes all of the namespaces we know about, plus any others supplied
    def teardown(self, *additional_namespaces):
        server_ns = f"{self.nsid}{Topology.server_ns_tag}"
        client_ns = f"{self.nsid}{Topology.client_ns_tag}"
        # List of namespaces to delete, including the default ones
        namespaces = [server_ns, client_ns]
        # Add the transit namespaces (created in _create_transit_network)
        for i in range(4):
            namespaces.append(f"{self.nsid}-ns{i}")
        # Add any additional namespaces provided as arguments
        namespaces.extend(additional_namespaces)

        # Delete the namespaces
        for ns in namespaces:
            runcmd(f"ip netns del {ns}")

    def _create_transit_network(self):
        # create 4 namespaces, each with their own bridge
        for i in range(4):
            ns = f"{self.nsid}-ns{i}"
            br = f"br{ns}"
            Topology.create_namespace(ns)
            Topology.create_bridge(ns, br)

        # create 5 veth pairs
        for i in range(0, 10, 2):
            v1 = f"veth{self.nsid}{i}"
            v2 = f"veth{self.nsid}{i+1}"
            self.create_veth_pairs(v1, v2)

        # connects the veths like so:
        # ns0 : veth1, veth2
        # ns1 : veth3, veth4
        # ns2 : veth5, veth6
        # ns3 : veth7, veth8
        m = [-1, 0, 0, 1, 1, 2, 2, 3, 3, -1]
        for i in range(1, 9):
            veth = f"veth{self.nsid}{i}"
            target_ns = f"{self.nsid}-ns{m[i]}"
            runcmd(f"ip link set {veth} netns {target_ns}")
            runcmd(f"ip link set {veth} master br{target_ns}",
                   namespace=target_ns)
            runcmd(f"ip link set dev {veth} up", namespace=target_ns)

    # sets up the client NS components:
    #  - creates the namespace
    #  - adds veth9 into it
    #  - creates a bridge in the namespace and brings it up
    def _setup_client_ns(self):
        Topology.create_namespace(self.client_ns)
        Topology.create_bridge(self.client_ns, self.client_br)
        veth9 = f"veth{self.nsid}9"
        # sets veth9 to client NS
        runcmd(f"ip link set {veth9} netns {self.client_ns}")
        runcmd(f"ip link set dev {veth9} up", namespace=self.client_ns)
        # adds veth9d to the bridge
        runcmd(f"ip link set veth{self.nsid}9 master brd{self.nsid}0",
               namespace=self.client_ns)
        # allows non-root services to use ports?
        runcmd("sysctl -w net.ipv4.ip_unprivileged_port_start=1",
               namespace=self.client_ns)

    # sets up the server NS components:
    #  - creates the namespace
    #  - moves veth0 into it
    #  - give veth an ip of 10.0.1.1/24
    def _setup_server_ns(self):
        Topology.create_namespace(self.server_ns)
        Topology.create_bridge(self.server_ns, self.server_br)
        # give the server bridge the address 10.0.9.1/24
        runcmd(f"ip addr add 10.0.9.1/24 dev {self.server_br}",
               namespace=self.server_ns)
        # add veth0 to -servers NS and give it the ip 10.0.1.1
        veth0 = f"veth{self.nsid}0"
        runcmd(f"ip link set {veth0} netns {self.server_ns}")
        runcmd(f"ip link set dev {veth0} up", namespace=self.server_ns)
        runcmd(f"ip addr add 10.0.1.1/24 dev {veth0}",
               namespace=self.server_ns)
        # set the kernel flags
        runcmd("sysctl -w net.ipv4.ip_forward=1", namespace=self.server_ns)
        runcmd("sysctl -w net.ipv4.ip_forward=1", namespace=self.server_ns)
        runcmd("sysctl -w net.ipv4.ip_unprivileged_port_start=1",
               namespace=self.server_ns)

    # sets up the namespaces/veth pairs/addresses for the DNS server
    # adds 10.0.1.4
    def _setup_dns(self, ip):
        vdns0 = f"vdns{self.nsid}0"
        vdns1 = f"vdns{self.nsid}1"
        # create vethd3 and vethd4 (both go into -client, used to talk to/from
        #   bridge to client NS)
        runcmd(f"ip link add {vdns0} type veth peer name {vdns1}")
        runcmd(f"ethtool -K {vdns0} tso off gso off gro off")
        runcmd(f"ethtool -K {vdns1} tso off gso off gro off")
        # create the veths and add to the -client NS
        runcmd(f"ip link set {vdns0} netns {self.client_ns}")
        runcmd(f"ip link set dev {vdns0} up", namespace=self.client_ns)
        runcmd(f"ip link set {vdns1} netns {self.client_ns}")
        runcmd(f"ip link set dev {vdns1} up", namespace=self.client_ns)
        # adds the ip and adds one of the veths to the bridge
        runcmd(f"ip addr add {ip}/24 dev {vdns1}", namespace=self.client_ns)
        runcmd(f"ip link set {vdns0} master {self.client_br}",
               namespace=self.client_ns)

    # applies the given impairements
    def apply_impairements(self, bw, rtt, bdp, first=False, bwup=None, loss=0):
        mtu = 1514

        if not first:
            op = "change"
        else:
            op = "add"

        if bwup is None:
            bwup = bw

        bdp_bytes = int(
            math.ceil((bw / 8. * 1024. * 1024.) * (rtt / 1000.) * bdp))
        oversized_bdp_packets = int(math.ceil(bdp_bytes * 10. / mtu))

        if loss == 0.0:
            # adding qdiscs - delay
            runcmd(f"ip netns exec {self.nsid}-ns1 tc qdisc {op} dev veth{self.nsid}4 root handle 1: netem delay {rtt / 2}ms limit {oversized_bdp_packets}")
            runcmd(f"ip netns exec {self.nsid}-ns2 tc qdisc {op} dev veth{self.nsid}5 root handle 1: netem delay {rtt / 2}ms limit {oversized_bdp_packets}")
        else:
            print(f"loss type: {type(loss)}, {loss}")
            if type(loss) is str:
                # adding qdiscs - delay (burst) loss
                runcmd(f"ip netns exec {self.nsid}-ns1 tc qdisc {op} dev veth{self.nsid}4 root handle 1: netem delay {rtt / 2}ms loss {loss} limit {oversized_bdp_packets}")
                runcmd(f"ip netns exec {self.nsid}-ns2 tc qdisc {op} dev veth{self.nsid}5 root handle 1: netem delay {rtt / 2}ms loss {loss} limit {oversized_bdp_packets}")
            else:
                # adding qdiscs - delay loss
                runcmd(f"ip netns exec {self.nsid}-ns1 tc qdisc {op} dev veth{self.nsid}4 root handle 1: netem delay {rtt / 2}ms loss random {loss * 100:.2f}% limit {oversized_bdp_packets}")
                runcmd(f"ip netns exec {self.nsid}-ns2 tc qdisc {op} dev veth{self.nsid}5 root handle 1: netem delay {rtt / 2}ms loss random {loss * 100:.2f}% limit {oversized_bdp_packets}")
        # adding qdiscs - rate shaping
        runcmd(f"ip netns exec {self.nsid}-ns3 tc qdisc {op} dev veth{self.nsid}7 root handle 1: tbf rate {bwup}mbit burst {mtu} limit {bdp_bytes}")
        runcmd(f"ip netns exec {self.nsid}-ns0 tc qdisc {op} dev veth{self.nsid}2 root handle 1: tbf rate {bw}mbit burst {mtu} limit {bdp_bytes}")


    # checks whether or not the given topology with the nsid exists
    # ... this simply checks the -clients and -servers NS
    def exists(self):
        ns_out = runcmd("ip netns ls").stdout.decode("utf-8").strip()
        ns_list = [self.client_ns, self.server_ns]
        for ns in ns_list:
            if ns not in ns_out:
                return False
        return True


if __name__ == "__main__":
    nsid = "soda"
    t = Topology(nsid)
    t.up()
    t.attach_client_with_ip("quiche-client", "10.0.1.63")
    t.attach_client_with_ip("quiche-server", "10.0.9.93")
