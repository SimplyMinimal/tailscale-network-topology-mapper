# Tailscale Network Topology Mapper
### A visual way to view your ACL rules for Tailscale


![alt text](Animation.gif)

# Initial Set Up
0. You will need Python3 and git installed.
1. `git clone https://github.com/SimplyMinimal/tailscale-network-topology-mapper`
2. `cd tailscale-network-topology-mapper`
3. `pip install -r requirements.txt`
4. Copy your ACL policy  into the contents of the example `policy.hujson` 
5. Edit `create-network-map.py` and change `COMPANY_DOMAIN="example.com"` to your actual company domain 

# Execution
6. run `python create-network-map.py` to generate your network map. It should produce an updated `network_topology.html` file that you can open in your browser.
