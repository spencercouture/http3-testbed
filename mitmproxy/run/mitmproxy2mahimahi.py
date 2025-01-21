"""
This inline script can be used to dump flows as HAR files.
"""


import json
import sys
import base64
import zlib
import sys
import os
import mahi_pb2
import string
import random

from pprint import pprint

from datetime import datetime
import pytz

import mitmproxy

from mitmproxy import version
from mitmproxy.utils import strutils
from mitmproxy.net.http import status_codes

import parse_mahimahi

import errno    
import os

def load(loader):
    loader.add_option(
        name="output",
        typespec=str,
        default="output",
        help="Specify the output directory",
    )

def mkdir_p(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def getCode(length = 10, char = string.ascii_uppercase +
                          string.digits +           
                          string.ascii_lowercase ):
    return ''.join(random.choice( char) for x in range(length))


def start():
    """
        Called once on script startup before any other events.
    """
    if len(sys.argv) != 2:
        raise ValueError(
            'Usage: -s "mahimahidump.py directory" '
        )



def calcMahimahiHash(str_in):
    import ctypes
    v = ctypes.c_uint32(2166136261).value
    for i in range(len(str_in)): 
        v = ctypes.c_uint32(v ^ str_in[i]).value
        v = ctypes.c_uint32(v * 16777619).value
    return v




def response(flow):
    """
       Called when a server response has been received.
    """

    # -1 indicates that these values do not apply to current request
    ssl_time =-1
    connect_time = -1

    reqresp = mahi_pb2.RequestResponse()
    scheme = mahi_pb2.RequestResponse.HTTPS if flow.request.url.lower().startswith('https://') else mahi_pb2.RequestResponse.HTTP
    print(flow.server_conn.address)
    print(dir(flow.server_conn))

    reqresp.scheme = scheme
    reqresp.ip, reqresp.port = flow.server_conn.address 

    #reqresp.request = mahi_pb2.HTTPMessage()
    first_line = bytes(flow.request.method + " "+flow.request.path+" HTTP/1.1",'utf-8')
    reqresp.request.first_line = first_line
    if flow.request.raw_content:
        reqresp.request.body = flow.request.raw_content

    # add the host header here
    host, ip = flow.server_conn.address
    host_hdr = reqresp.request.header.add()
    host_hdr.key = bytes("Host", 'utf-8')
    host_hdr.value = bytes(f"{host}", 'utf-8')

    for k,v in flow.request.headers.items():
        _hdr = reqresp.request.header.add()
        _hdr.key = bytes(k,'utf-8')
        _hdr.value = bytes(v,'utf-8')

    status_code = flow.response.status_code
    reqresp.response.first_line = bytes("HTTP/1.1 "+str(status_code)+" "+status_codes.RESPONSES.get(status_code, ""),'utf-8')
        

    for k,v in flow.response.headers.items():
        if k.lower() == "transfer-encoding" and 'chunked' in v.lower():
            continue
        _hdr = reqresp.response.header.add()
        _hdr.key = bytes(k,'utf-8')
        _hdr.value = bytes(v,'utf-8')
    if flow.response.raw_content is not None:
        reqresp.response.body = flow.response.raw_content
    else:
        reqresp.response.body = bytes('','utf-8')


    qotationmark = str(first_line).find('?')
    if qotationmark == -1:
        filename_hash = calcMahimahiHash(first_line)
    else:
        print(first_line[:qotationmark-2])
        print(first_line)
        filename_hash = calcMahimahiHash(first_line[:qotationmark-2])
    

    # print(dir(mitmproxy.ctx.options))
    output_dir = mitmproxy.ctx.options.output


    mkdir_p(output_dir)
    while True:
        pathname = os.path.join(output_dir,getCode()+'_'+str(filename_hash)+'.save')
        if not os.path.exists(pathname):
            break

    f = open(pathname, "wb")
    f.write(reqresp.SerializeToString())
    f.close()

    # write our custom file 
    with open(os.path.join(output_dir, "pp_sorted.txt"), 'a+') as pp_file:
        pp_file.write(parse_mahimahi.smart_print_rr(parse_mahimahi.get_rr(reqresp)))

def done():
    """
        Called once on script shutdown, after any other events.
    """
    mitmproxy.ctx.log("Dump finished ")


def format_datetime(dt):
    return dt.replace(tzinfo=pytz.timezone("UTC")).isoformat()


def format_cookies(cookie_list):
    rv = []

    for name, value, attrs in cookie_list:
        cookie_har = {
            "name": name,
            "value": value,
        }

        # HAR only needs some attributes
        for key in ["path", "domain", "comment"]:
            if key in attrs:
                cookie_har[key] = attrs[key]

        # These keys need to be boolean!
        for key in ["httpOnly", "secure"]:
            cookie_har[key] = bool(key in attrs)

        # Expiration time needs to be formatted
        expire_ts = cookies.get_expiration_ts(attrs)
        if expire_ts is not None:
            cookie_har["expires"] = format_datetime(datetime.fromtimestamp(expire_ts))

        rv.append(cookie_har)

    return rv


def format_request_cookies(fields):
    return format_cookies(cookies.group_cookies(fields))


def format_response_cookies(fields):
    return format_cookies((c[0], c[1].value, c[1].attrs) for c in fields)


def name_value(obj):
    """
        Convert (key, value) pairs to HAR format.
    """
    return [{"name": k, "value": v} for k, v in obj.items()]
