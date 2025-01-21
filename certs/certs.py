import os
import hashlib
from process import run


# generates a hash from the list of hostnames
# this is used to store the certificates for a site.
# the helper function exists to use this logic in other places
# (like in server setup functions to get the path to the certs)
def generate_host_hash(hostnames_list):
    hostnames = sorted(list(set(hostnames_list)))
    hostnames_string = ",".join(hostnames)

    m = hashlib.md5()
    m.update(hostnames_string.encode())
    hash = m.hexdigest()
    return hash


# creates certs for a list of hostnames.
# certs are stored in the certs/ directory,
# named by a hash of all their hostnames concatenated together.
# (if you supply a website, it will use that as the name of the file)
def create_certs(hostnames_list):
    # create our directory and generate the certs
    hash = generate_host_hash(hostnames_list)
    # if it already exists, skip
    cert_path = os.path.abspath(f"certs/{hash}")
    if os.path.exists(cert_path):
        return cert_path
    os.makedirs(cert_path)

    cert_args = ["certs/cert.sh", f"{cert_path}/cert"]
    cert_args += hostnames_list

    run(cert_args)

    return cert_path
