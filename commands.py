from topology import Topology
from mitmproxy.mitmproxy import capture_site, site_exists, get_hostnames
from servers import quiche
from certs.certs import create_certs
from dns import start_dnsmasq
import os

# add new servers here
servers = {
    "quiche": quiche
}


# stars the server:
#  - ensures the topology is up
#  - ensures the site exists
#  - generates the certificates
def start_server(args):
    server = servers[args.server]

    # check if the topology is up and the site exists
    topo = Topology(args.namespace_id)
    if not topo.exists():
        print(f"Unable to start server: {args.namespace_id} topology not found!")
        return False
    if not site_exists(args.website):
        print(f"Unable to start server: {args.website} not found in `sites/`!")
        return False

    # gets the hostnames for the site
    hostnames = get_hostnames(args.website)
    # generates the certificates for the site
    cert_dir = create_certs(hostnames)
    # start DNS server with the given hostnames/addresses
    start_dnsmasq(topo, hostnames, args.address)

    # call the server start method
    server.start(topo, args.website, args.address, args.port, cert_dir)
    return True

# stops the server
def stop_server(args):
    server = servers[args.server]
    topo = Topology(args.namespace_id)
    if not topo.exists():
        print(f"Unable to stop server: {args.namespace_id} topology not found!")
        return False
    server.stop(topo)
    return True

# copies a servers files to a certain location
def copy_server_files(args):
    server = servers[args.server]
    topo = Topology(args.namespace_id)
    if not topo.exists():
        print(f"Unable to copy files from server: {args.namespace_id} topology not found!")
        return False
    if not os.path.isdir(args.destination):
        print(f"Unable to copy server files. {args.destination} does not exist!")
        return False
    server.copy_files(topo, args.destination)
    return True




# topology commands
def up(args):
    Topology(args.name).up()


def down(args):
    Topology(args.name).teardown()


def test_connection(args):
    print("Testing connection...")


def save_results(args):
    print("Collecting results...")


def run_testbed(args):
    print("Running full testbed sequence...")


# site commands
def capture(args):
    capture_site(args.website, overwrite=args.overwrite)
