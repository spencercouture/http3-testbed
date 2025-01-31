#!/usr/bin/env python3
import argparse
from commands import *


def configure_cli_args():
    parser = argparse.ArgumentParser(description="HTTP/3 Testbed CLI")
    subparsers = parser.add_subparsers(
        dest="command_group", required=True, help="Command groups")

    # Topology commands
    topology_parser = subparsers.add_parser(
        "topology", help="Commands to manage topology")
    topology_parser.add_argument("name", type=str,
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
        "performance_tool", choices=["browsertime", "lighthouse"], help="Performance measurement tool")
    run_parser.set_defaults(func=run_testbed)

    # Client commands
    client_parser = subparsers.add_parser("client", help="Commands to run clients")
    client_parser.add_argument("client", choices=clients.keys(), help="Target client")
    client_cmd_parser = client_parser.add_subparsers(
        dest="client_command", required=True)
    run_parser = client_cmd_parser.add_parser(
        "run", help="Run a client for a website in a particular namespace")
    run_parser.add_argument("--website", required=True, type=str, help="Website to target")
    run_parser.add_argument("--namespace-id", required=True, type=str, help="Name/ID of topology to run on")
    run_parser.add_argument("--destination", required=True, type=str, default="results/", help="Location to save files to")
    run_parser.set_defaults(func=run_client)

    # Server commands
    server_parser = subparsers.add_parser(
        "server", help="Commands to manage servers")
    server_parser.add_argument(
        "server", choices=servers.keys(), help="Target server")
    server_cmd_parser = server_parser.add_subparsers(
        dest="server_command", required=True)
    start_parser = server_cmd_parser.add_parser(
        "start", help="Start a server in a particular namespace")
    start_parser.add_argument("--website", required=True, type=str, help="Website to serve")
    start_parser.add_argument("--namespace-id", required=True, type=str, help="Name/ID of topology to run on")
    start_parser.add_argument("--address", required=True, type=str, default="10.0.9.83", help="Address to serve on")
    start_parser.add_argument("--port", type=int, default=443, help="Port to server on (default 443)")
    start_parser.set_defaults(func=start_server)
    stop_parser = server_cmd_parser.add_parser("stop", help="Stop a server in a particular namespace")
    stop_parser.add_argument("--namespace-id", required=True, type=str, help="Name/ID of topology to stop in")
    stop_parser.set_defaults(func=stop_server)
    copy_parser = server_cmd_parser.add_parser("copy", help="Copy server files to a certain location")
    copy_parser.add_argument("--namespace-id", required=True, type=str, help="Name/ID of topology to stop in")
    copy_parser.add_argument("--destination", required=True, type=str, help="Location to copy server files to")
    copy_parser.set_defaults(func=copy_server_files)

    # site commands
    capture_parser = subparsers.add_parser(
        "capture", help="Capture a given website")
    capture_parser.add_argument(
        "website", type=str, help="Target website (e.x.: www.wikipedia.org")
    capture_parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing protobuf_files")
    capture_parser.set_defaults(func=capture)

    return parser.parse_args()


def main():
    args = configure_cli_args()
    args.func(args)


if __name__ == "__main__":
    main()
