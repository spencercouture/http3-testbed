cp ../certs/RootCA.crt .
docker build --no-cache -t scouture/browsertime .
rm RootCA.crt
