FROM sitespeedio/browsertime:22.6.0
USER root

RUN apt-get update && apt-get install -y \
  iputils-ping \
  dnsutils \
  nano \
  libnss3-tools

# setup certs
RUN [ -d ~/.pki/nssdb ] || mkdir -p ~/.pki/nssdb
COPY RootCA.crt /root/ca.crt
RUN certutil -d sql:/root/.pki/nssdb -A -n 'smc ca' -i /root/ca.crt -t TCP,TCP,TCP

# copy chromium libraries(?) over
COPY chromeDevtoolsProtocol.js /usr/src/app/lib/chrome/chromeDevtoolsProtocol.js
COPY har.js /usr/src/app/lib/chrome/har.js

ENV BROWSERTIME_DOCKER=true BT_THREADS=4

ENTRYPOINT ["/usr/bin/env"]
CMD ["bash"]
