from topology import Topology
from mitmproxy.mitmproxy import capture_site


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
