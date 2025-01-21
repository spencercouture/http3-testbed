#!/usr/bin/env python3.8
import glob
import os
import sys
file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

import mahi_pb2
import sys
import argparse
parser = argparse.ArgumentParser()

from dataclasses import dataclass

@dataclass
class RR:
    ip_port: str
    scheme: str
    req_first_line: str
    res_first_line: str
    request_headers: list
    response_headers: list
    response_body: str
def smart_print_rr(rr):
    rr.req_first_line = rr.req_first_line[:25] + "..." + rr.req_first_line[-25:] if len(rr.req_first_line) > 50 else rr.req_first_line
    rr.res_first_line = rr.res_first_line[:25] + "..." + rr.res_first_line[-25:] if len(rr.res_first_line) > 50 else rr.res_first_line

    string = f"{'-'*30}\n{rr.ip_port} ({rr.scheme})\n-{rr.req_first_line}\t\n-{rr.res_first_line}\n\n"
    string += "Request:\n"
    for (rhk,rhv) in rr.request_headers:
        rhv = rhv[:25] + "..." + rhv[-25:] if len(rhv) > 50 else rhv 
        string += f"\t{rhk}: {rhv}\n"
    string += "Response:\n"
    for (rhk,rhv) in rr.response_headers:
        rhv = rhv[:25] + "..." + rhv[-25:] if len(rhv) > 50 else rhv 
        string += f"\t{rhk}: {rhv}\n"
    string += f"body_size: {len(rr.response_body)}\n"
    string += f"{'-'*30}\n"
    return string

def main():
    if len(sys.argv) < 1:
        print("No files supplied. Usage: ./parse_mahimahi.py <save_file1> <save_file2> ...")
        exit

    # rrs = get_rrs(sys.argv[1], True)
    rrs = []
    for file in sys.argv[1:]:
        # print(f"parsing file {file}")
        with open(file, 'rb') as f:
            mahi_rr = mahi_pb2.RequestResponse()
            mahi_rr.ParseFromString(f.read())
            rrs.append(get_rr(mahi_rr))
    
    rrs.sort(key=lambda rr: rr.req_first_line)
    for rr in rrs:
        print(smart_print_rr(rr))

    # breakpoint()

def get_rr(rr, sort_headers=False):
    https = "https" if rr.scheme == mahi_pb2.RequestResponse.Scheme.Value("HTTPS") else "http" 

    request_headers = []
    for request_header in rr.request.header:
        k = request_header.key.decode()
        v = request_header.value.decode()
        k_stripped = k.lower().strip()
        request_headers.append((k_stripped,v))

    response_headers = []
    for response_header in rr.response.header:
        k = response_header.key.decode()
        v = response_header.value.decode()
        k_stripped = k.lower().strip()
        response_headers.append((k_stripped,v))

    # optionally sort headers alphabetically for easier comparison
    if sort_headers:
        request_headers.sort(key=lambda rh: rh[0])
        response_headers.sort(key=lambda rh: rh[0])


    # response_headers_stripped = []
    # for k, v in response_headers.items():
    #     if k not in ['expires', 'date', 'last-modified', 'link', 'alt-svc', 'connection', 'transfer-encoding']:
    #         response_headers_stripped.append(v)

    response_line = rr.response.first_line.decode()
    request_line = rr.request.first_line.decode()
    response_body = str(rr.response.body.decode("iso-8859-1"))
    # scheme = rr.scheme.decode()
    #build RR and return 

    return RR(
        f"{rr.ip}:{rr.port}", # ip_port
        https,
        request_line,
        response_line,
        request_headers,
        response_headers,
        response_body
    )

if __name__ == '__main__':
    main()
