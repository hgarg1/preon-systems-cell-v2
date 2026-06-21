from __future__ import annotations

import ipaddress


def calculate(payload: dict) -> dict:
    cidr = str(payload.get("cidr", ""))
    try:
        network = ipaddress.IPv4Network(cidr, strict=False)
        hosts = list(network.hosts())
        return {
            "network": str(network.network_address),
            "broadcast": str(network.broadcast_address),
            "mask": str(network.netmask),
            "prefix_length": network.prefixlen,
            "first_host": str(hosts[0]) if hosts else str(network.network_address),
            "last_host": str(hosts[-1]) if hosts else str(network.broadcast_address),
            "host_count": len(hosts),
        }
    except ValueError as exc:
        return {"error": str(exc)}
