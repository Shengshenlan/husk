"""Network egress rules for sandbox containers (M4 scaffold)."""


async def apply_egress_rules(container_ip: str, allow: list[str]) -> None:
    """Restrict a container's outbound traffic to ``allow`` (CIDRs / domains).

    Implementation lands in M4 — either iptables direct or a per-sandbox
    docker network with controlled forward rules.
    """
    raise NotImplementedError("Implemented in M4")
