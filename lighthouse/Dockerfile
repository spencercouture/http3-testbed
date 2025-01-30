FROM node
USER root

RUN apt-get update && apt-get install -y \
    iputils-ping \
    dnsutils \
    nano \
    libnss3-tools \
    libatk1.0-dev \
    libasound2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxtst6 \
    libdbus-1-3 \
    libatspi2.0-dev \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgbm1 \
    libcups2 \
    libxkbcommon0 \
    chromium

RUN npm install -g lighthouse

RUN [ -d ~/.pki/nssdb ] || mkdir -p ~/.pki/nssdb

COPY RootCA.crt /root/ca.crt

RUN certutil -d sql:/root/.pki/nssdb -A -n 'smc ca' -i /root/ca.crt -t TCP,TCP,TCP

# # initialize node project
# RUN mkdir -p /lighthouse/ 
# WORKDIR /lighthouse
# RUN npm init -y
# RUN npm install lighthouse chrome-launcher fs
# WORKDIR /


ENTRYPOINT ["/usr/bin/env"]
CMD ["bash"]
