#!/usr/bin/env python3
import argparse
from commands import up, down, test_connection, run_testbed


def configure_cli_args():
    parser = argparse.ArgumentParser(description="HTTP/3 Testbed CLI")
    subparsers = parser.add_subparsers(
        dest="command_group", required=True, help="Command groups")

    # Topology commands
    topology_parser = subparsers.add_parser(
        "topology", help="Commands to manage topology")
    topology_parser .add_argument("name", type=str,
                                  help="Name/ID to use for topolgy/namespaces")
    topology_subparsers = topology_parser.add_subparsers(
        dest="topology_command", required=True)

    topology_subparsers.add_parser(
        "up", help="Bring up topology").set_defaults(func=up)
    topology_subparsers.add_parser(
        "down", help="Bring down topology").set_defaults(func=down)
    topology_subparsers.add_parser(
        "test_connection", help="Test the topology").set_defaults(func=test_connection)

    # Run testbed command
    run_parser = subparsers.add_parser(
        "run", help="Run the full testbed sequence")
    run_parser.add_argument("website", type=str, help="Website to test")
    run_parser.add_argument(
        "server", choices=["quiche", "h2o"], help="Server type")
    run_parser.add_argument(
        "performance_tool", choices=["browsertime", "lighthouse"], help="Performance measurement tool"
    )
    run_parser.set_defaults(func=run_testbed)

    return parser.parse_args()


def main():
    args = configure_cli_args()
    args.func(args)


if __name__ == "__main__":
    main()
