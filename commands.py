from topology import Topology


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
