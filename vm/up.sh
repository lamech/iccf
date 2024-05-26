#!/bin/bash -v
sudo apt-get update -yqq
sudo apt-get install -yqq git make unzip software-properties-common acl
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt-get install -yqq ansible
ansible-playbook -i inventory -c local up.yaml
