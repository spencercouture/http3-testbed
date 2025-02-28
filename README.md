# HTTP/3 Testbed

This is a WIP and will be filled out more later on--for now it documents its build steps and simple usage

## Building
The following steps assume a fresh install of Debian 12 (bookworm).

The process of building this project involves:
 - installing necessary packages
 - building mahimahi-gen, browsertime, and lighthouse docker containers
 - building quiche (and respective container)

### Installing Dependencies
First install required apt packages:
`sudo apt-get update -y && sudo apt-get install -y git ethtool python3-protobuf python3-numpy cmake build-essential dnsmasq`

Install Docker (steps from: https://docs.docker.com/engine/install/debian/):
```
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

Install Rust/Cargo (steps from: ):
```
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```
Clone Repo and Build Containers:
```
# clone repo
git clone --recurse-submodules https://github.com/spencercouture/http3-testbed.git

# build browsertime
cd http3-testbed
pushd browsertime
./build.sh
popd

# build lighthouse
pushd lighthouse
./build.sh
popd

# build mahimahi-gen
pushd mitmproxy
./build.sh
popd

# build quiche
pushd quiche
make docker-protobuf-build
popd
```

## CLI

### Design
Interacting with this repository involves using the `main.py` script to interact with the CLI, like so:
`sudo ./main.py <cmd> ...`

The CLI provides commands that can be used to capture websites, bring up/down topologies, start servers, run clients, etc. Commands are split up into command groups with respective subcommands. Each command/subcommand may have its own requirements for arguments, but the argparse output should be helpful in explaining which if you miss them.

Most of these commands execute a single build step. In order to run a full testbed start to finish, the following steps must occur:
 - website is captured
 - topology is started (requires a namespace-id)
 - server is started (reqs. namespace-id to add to and a website to serve)
 - client is run (reqs. namespace-id to run on and website to connect to)

### Commands

#### Capture
Usage: `./main.py capture <website> [--overwrite]`

... where `<website>` is in the form of `www.unh.edu`. `--overwrite` is used to replace an existing website's protobuf_files.

The capture command is used to capture websites in `sites/`. This is accomplished by spinning up a `mahimahi-gen` container that acts as an HTTPS proxy. This container uses mitmproxy with a custom python script to output all the traffic as mahimahi protobuf files. It also outputs a `pp_sorted.txt` file that lets you browse the headers (clumsily) as a text file.

Previously, a browsertime container was used as the client (with the --proxy.https flag set to the aforementioned container), but due to browsertime's performance limitations, I updated to use lighthouse as the client instead. This proves to be much more efficient. The code to use browsertime as a client still exists in `mitmproxy.py` and can be uncommented out if needed.


### Usage
Here are the high-level commands (and their respective subcommands):
- Topology: manage testbed topologies
  - up: Bring up a topology
  - down: Tear down a topology
- Run: Execute a full test sequence  
  - Requires a website, server (quiche or h2o), and performance tool (browsertime or lighthouse)  

- Client: Run clients in a topology  
  - run: Specify client, website, namespace ID, and destination  

- Server: Manage HTTP/3 servers  
  - start: Start a server with a website, namespace ID, address, and optional port  
  - stop: Stop a running server in a given namespace  
  - copy: Copy server files to a destination  

- Site: Perform site-related tasks  
  - capture: Capture a website with an optional overwrite flag  

THINGS OF NOTE!!!
this testbed is capability of bringing up ONE topology at a time (names WILL conflict with eachother). therefore, if a topology is up and another one is attempted to be brought up, the former will be overridden.

## topology

how the topology works:

client space is 10.0.1.1/24

server space is 10.0.9.1/24

notes - server should be not in the 10.0.1.1/24 range, to make sense topologically

the difference between adding servers and adding clients is:

- servers assume their own namespace, they create a new veth pair, and add one into the ns, and one into the server-ns and just give it whatever address?
- clients assume their own namespace. they create a new veth pair and add one into the ns, and one into the client-ns and bridge.

## servers

in order to add a new server, create a new class that provides these functions:
def intialize_server(certs? ip? hostname?)

# ns-servers - veth0 | veth1 - ns0 - veth2 | veth3 - ns1 - veth4 | veth5 - ns2 - veth6 | veth7 - ns3 - veth8 | veth9 - ns-client <> docker
