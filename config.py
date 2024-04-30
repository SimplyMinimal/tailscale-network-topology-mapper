import os

COMPANY_DOMAIN = "example.com"
if "TS_COMPANY_DOMAIN" in os.environ:
    COMPANY_DOMAIN = os.environ["TS_COMPANY_DOMAIN"]
    print(f'Using {COMPANY_DOMAIN} as company domain')

POLICY_FILE = os.path.join(os.path.dirname(__file__), "policy.hujson")