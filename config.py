import os

# Company domain configuration
COMPANY_DOMAIN = "example.com"
if "TS_COMPANY_DOMAIN" in os.environ:
    COMPANY_DOMAIN = os.environ["TS_COMPANY_DOMAIN"]
    print(f'Using {COMPANY_DOMAIN} as company domain')

# Policy file configuration
POLICY_FILE = os.path.join(os.path.dirname(__file__), "policy.hujson")

# Node color configuration
NODE_COLORS = {
    "tag": "#00cc66",      # Green for tags
    "group": "#FFFF00",    # Yellow for groups and autogroups
    "host": "#ff6666"      # Red for hosts
}

# Visualization configuration
VISUALIZATION_CONFIG = {
    "height": "800px",
    "width": "100%",
    "notebook": True,
    "directed": True,
    "filter_menu": True,
    "select_menu": True,
    "neighborhood_highlight": True,
    "cdn_resources": "remote"
}

# Logging configuration
LOG_FORMAT = "%(levelname)s [%(filename)s:%(lineno)d]: %(message)s"

# Valid network protocols for grant validation
VALID_PROTOCOLS = {
    "tcp", "udp", "icmp", "ah", "esp", "gre", 
    "ipv6-icmp", "ospf", "sctp"
}

# Port range limits
MIN_PORT = 1
MAX_PORT = 65535