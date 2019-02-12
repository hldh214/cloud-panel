#!/bin/bash
# 4 Ubuntu Only
# Usage: ./init.sh password port

# docker
apt-get update
apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
apt-key fingerprint 0EBFCD88
add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io

# shadowsocks
docker pull mritd/shadowsocks
docker run -dt --restart unless-stopped --name ssserver -p $2:$2 mritd/shadowsocks -s "-s 0.0.0.0 -p $2 -m
chacha20-ietf-poly1305 -k $1 --fast-open"
