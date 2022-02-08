#!/bin/bash
echo > /etc/apt/apt.conf.d/20auto-upgrades << "END"
APT::Periodic::Update-Package-Lists "0"
APT::Periodic::Unattended-Upgrade "0"
END
