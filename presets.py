from topology import Topology
from certs.certs import create_certs
from mitmproxy.mitmproxy import get_hostnames
from dns import start_dnsmasq
from servers import quiche


# the dictionary of name->functions to choose from CLI
PRESETS = {}


def register_preset(name):
    def wrapper(func):
        PRESETS[name] = func
        return func
    return wrapper


@register_preset("full_quiche_run")
def full_quiche_run():
    quiche_addr = "10.0.9.83"
    # run full testbed for each of the sites
    sites = [("www.unh.edu","unh")]
    for (site, nsid) in sites:
        # first bring the topo up
        topo = Topology(nsid).up()

        # get certs and DNS configured
        hostnames = get_hostnames(site)
        cert_dir = create_certs(hostnames)
        start_dnsmasq(topo, hostnames, quiche_addr)

        # start quiche
        quiche.start(topo, site, quiche_addr, 443, cert_dir)


