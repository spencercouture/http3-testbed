from topology import Topology
from certs.certs import create_certs
from mitmproxy.mitmproxy import get_hostnames, capture_site
from dns import start_dnsmasq
from servers import quiche
from clients import browsertime, lighthouse
import os


# the dictionary of name->functions to choose from CLI
PRESETS = {}


def register_preset(name):
    def wrapper(func):
        PRESETS[name] = func
        return func
    return wrapper


@register_preset("full_quiche_run")
def full_quiche_run(result_dir):
    quiche_addr = "10.0.9.83"
    # run full testbed for each of the sites
    sites = [("www.wikipedia.org", "wiki")]
    for (site, nsid) in sites:
        # capture the site. (if not already present)
        capture_site(site)

        site_res_dir = os.path.join(result_dir, site)
        if os.path.isdir(site_res_dir):
            print(f"error: {site_res_dir} exists. skipping {site}...")
            continue

        # first bring the topo up
        topo = Topology(nsid)
        topo.up()

        # get certs and DNS configured
        hostnames = get_hostnames(site)
        cert_dir = create_certs(hostnames)
        start_dnsmasq(topo, hostnames, quiche_addr)

        # start quiche
        quiche.start(topo, site, quiche_addr, 443, cert_dir)

        # run browsertime
        print("running browsertime...")
        btpath = os.path.join(site_res_dir, "browsertime")
        btstats = browsertime.run(topo, site, btpath)

        # run lighthouse
        print("running lighthouse...")
        lhpath = os.path.join(site_res_dir, "lighthouse")
        lhstats = lighthouse.run(topo, site, lhpath)

        # stop server and copy files
        quiche_path = os.path.join(site_res_dir, "quiche")
        quiche.copy_files(topo, quiche_path)
        quiche.stop(topo)

        # remove topology and added server ns
        topo.teardown()
