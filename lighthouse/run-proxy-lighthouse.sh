#!/usr/bin/sh

lighthouse \
    --max-wait-for-load 600000 \
    --chrome-flags="\
    --proxy-server=host.docker.internal:8080 \
    --no-error-reporting \
    --no-sandbox \
    --headless \
    --disable-field-trial-config \
    --ignore-privacy-mode \
    --ignore-certificate-errors \
    --disk-cache-dir=/dev/null \
    --disk-cache-size=1 \
    --user-data-dir=/static-quiche/tmp \
    --disable-account-consistency \
    --disable-sync \
    --disable-background-networking \
    --disable-default-apps \
    --disable-extensions \
    --disable-component-update \
    --disable-client-side-phishing-detection \
    --disable-domain-reliability \
    --disable-features=AutofillServerCommunication \
    --disable-safebrowsing \
    --metrics-recording-only \
    --disable-metrics \
    --disable-google-url-tracker"\
    "https://$1"
