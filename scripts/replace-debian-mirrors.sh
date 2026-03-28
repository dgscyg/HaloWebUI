#!/bin/sh

set -eu

debian_mirror="${1:-}"
debian_security_mirror="${2:-}"

if [ -z "$debian_mirror" ] || [ -z "$debian_security_mirror" ]; then
    echo "usage: $0 <debian-mirror> <debian-security-mirror>" >&2
    exit 1
fi

replace_sources_file() {
    sources_file="$1"

    if [ ! -f "$sources_file" ]; then
        return 0
    fi

    sed -i \
        -e "s|http://deb.debian.org/debian|${debian_mirror}|g" \
        -e "s|https://deb.debian.org/debian|${debian_mirror}|g" \
        -e "s|http://deb.debian.org/debian-security|${debian_security_mirror}|g" \
        -e "s|https://deb.debian.org/debian-security|${debian_security_mirror}|g" \
        -e "s|http://security.debian.org/debian-security|${debian_security_mirror}|g" \
        -e "s|https://security.debian.org/debian-security|${debian_security_mirror}|g" \
        "$sources_file"
}

replace_sources_file /etc/apt/sources.list.d/debian.sources
replace_sources_file /etc/apt/sources.list
