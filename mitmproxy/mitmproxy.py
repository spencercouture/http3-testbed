import os
import shutil
import time
from process import runcmd
from mitmproxy.run.mahi_pb2 import RequestResponse 

# path of this script and sites/
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SITES_DIR = os.path.join(SCRIPT_DIR, "..", "sites")
SITES_DIR = os.path.abspath(SITES_DIR)


# creates a directory in sites/ for the argument. then:
#   - creates protobuf_files/ and fills with the captured site
#   - starts a http proxy via the `mahaimahi-gen` container
#   - runs the browsertime container and points it to mahimahi-gen
#   - ... files then get populated into protobuf_files (with pp_sorted.txt)
def capture_site(site, overwrite=False):
    site_path = os.path.join(SITES_DIR, site)
    proto_path = os.path.join(site_path, "protobuf_files")

    # if the profobuf_files dir exist, rm if overwrite is supplied
    if os.path.exists(proto_path):
        if not overwrite:
            print(f"{proto_path} exists and overwrite was not supplied.")
            print("Quitting...")
            return False
        shutil.rmtree(proto_path)

    # make the dirs
    os.makedirs(site_path, exist_ok=True)

    # clean the run/output dir
    rundir = os.path.join(SCRIPT_DIR, "run")
    output_path = os.path.join(rundir, "output")
    shutil.rmtree(output_path, ignore_errors=True)
    os.makedirs(output_path, exist_ok=True)

    # starts the mahimahi-gen container
    dflags = f"-v {rundir}:/run/ --rm -it -p 8080:8080 --detach"
    mitm = runcmd(f"docker run {dflags} mahimahi-gen").stdout
    print("Sleeping for 3 seconds to ensure mitmproxy is up...")
    time.sleep(3)

    # runs the browsertime container
    dflags = "--add-host=host.docker.internal:host-gateway --rm"
    btflags = f"--video --visualMetrics --proxy.https host.docker.internal:8080 --iterations 1 --timeouts.pageCompleteCheck 600000"
    runcmd(f"docker run {dflags} sitespeedio/browsertime:22.6.0 {btflags} https://{site}")

    # copy files over
    shutil.copytree(output_path, proto_path, dirs_exist_ok=True)

    # stop the mahimahi gen container
    runcmd(f"docker stop {mitm.decode('utf-8').strip()}")

    return True


# gets the list of hostnames for a given website
def get_hostnames(site):
    if not site_exists(site):
        return False

    # iterate through each .save file
    proto_path = os.path.join(os.path.join(SITES_DIR, site), "protobuf_files")
    hostnames = []
    for file in os.listdir(proto_path):
        file = os.path.join(proto_path, file)
        # skip dirs and non .save files
        if not os.path.isfile(file) or not file.endswith(".save"):
            continue

        # read in protobuf structure
        reqrep = RequestResponse()
        with open(file, "rb") as f:
            reqrep.ParseFromString(f.read())

        # pull out host field
        request_headers = {}
        for request_header in reqrep.request.header:
            k = request_header.key.decode()
            v = request_header.value.decode()
            k_stripped = k.lower().strip()
            request_headers[k_stripped] = v
        hostnames.append(request_headers["host"])

    return set(hostnames)


# returns whether or not a site exists
def site_exists(site):
    site_path = os.path.join(SITES_DIR, site)
    proto_path = os.path.join(site_path, "protobuf_files")
    return os.path.exists(proto_path)


# gets the protobuf_files path
def get_protobuf_path(site):
    assert site_exists(site)
    return os.path.join(SITES_DIR, site, "protobuf_files")


if __name__ == "__main__":
    capture_site("www.wikipedia.org", overwrite=True)
