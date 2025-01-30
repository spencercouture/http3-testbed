#!/usr/bin/sh

lighthouse \
    --chrome-flags="\
    --no-error-reporting \
    --no-sandbox \
    --headless \
    --disable-field-trial-config \
    --ignore-privacy-mode \
    --ignore-certificate-errors \
    --enable-quic \
    --quic-version=h3 \
    --origin-to-force-quic-on=* \
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
