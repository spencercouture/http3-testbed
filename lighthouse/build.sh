cp ../certs/RootCA.crt .
docker build --no-cache -t scouture/lighthouse .
rm RootCA.crt
