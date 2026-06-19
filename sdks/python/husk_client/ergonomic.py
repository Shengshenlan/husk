"""Phase 2.x: high-level ergonomic API.

The auto-generated `_generated/` client is endpoint-level (`create_sandbox`,
`list_sandboxes`, etc.). This module will expose an OO façade resembling
the upstream daytona-sdk style, e.g.::

    from husk_client.ergonomic import Husk

    hk = Husk(base_url="http://localhost:8000", api_key="hk_...")
    sb = hk.sandboxes.create(snapshot="py-3.12", cpu=2, memory="2GB")
    sb.process.exec("python script.py")
    sb.destroy()

Empty until Phase 2.x.
"""
