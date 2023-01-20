#!/bin/bash

MY_HOSTNAME="$(hostnamectl --static)"
KERNEL_LOG=$(journalctl _TRANSPORT=kernel --since "10 minutes ago" --no-pager --no-hostname -o short-full -a)

PING_MESSAGE="$(jq \
    --null-input \
    --arg ips "$(ip -brief a | awk '{if ($2 == "UP") {for(i=3;i<=NF;++i)print $i}}' | tr '\n' ' ')" \
    --arg uptime "$(cat /proc/uptime | awk '{ print $1 }')" \
    --arg hostname "$MY_HOSTNAME" \
    --compact-output \
    '{"name": $hostname, "interval": 60, "additional_data": {"uptime": $uptime, "ips": $ips}}')"

if [[ -n "$MY_HOSTNAME" ]]
then
    for i in 1 2 3 ; do
        voc2mqtt \
            -t "/voc/checkin" \
            -m "$PING_MESSAGE" && break
    done

    for i in 1 2 3 ; do
        voc2mqtt \
            -t "hosts/$(hostnamectl --static | sed 's/\.c3voc\.de$//g')/checkin" \
            -m "$PING_MESSAGE" && break
    done
fi

for file in /usr/local/sbin/check_system.d/*.sh
do
    if [ -x "${file}" ]; then
        . "${file}"
    fi
done
