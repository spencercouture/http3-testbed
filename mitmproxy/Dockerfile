FROM mitmproxy/mitmproxy

run pip install pytz
run pip install protobuf

ENTRYPOINT ["mitmdump"]
CMD ["-s", "/run/mitmproxy2mahimahi.py", "--set", "output=/run/output"]
