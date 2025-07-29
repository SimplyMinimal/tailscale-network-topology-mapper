# Tailscale Network Topology Mapper
### A visual way to view your ACL and Grant rules for Tailscale
I occasionally find myself just wanting to get a glance of how my ACL rules look without reading through the code. This is also useful for showing how our policies are set up to people who are not devs by trade.

![alt text](./images/Animation.gif)

### Initial Set Up

0. You will need Python3 and git installed.
1. `git clone https://github.com/SimplyMinimal/tailscale-network-topology-mapper`
2. `cd tailscale-network-topology-mapper`
3. `pip install -r requirements.txt`
4. Copy your ACL policy  into the contents of the example `policy.hujson` 
5. Edit `config.py` and change `COMPANY_DOMAIN="example.com"` to your actual company domain. Alternatively, you can set an environment variable`TS_COMPANY_DOMAIN` containing the company domain.

### Execution

6. Run `python main.py` to generate your network map. It should produce an updated `network_topology.html` file that you can open in your browser.

### Run as Docker container

If instead you want to run it using Docker, you can do so.

0. You will need docker and make installed.
1. `make build run`
2. Access the web server at [http://localhost:8080](http://localhost:8080)

You can filter down to specific groups or nodes using the filter bar at the top or by clicking on a node on the graph.

### Github Action Workflow

If you would like to have the network map be automatically updated whenever you push an update to your ACL file then take a look at this example workflow:
[.github/workflows/tailscale.yml](https://github.com/SimplyMinimal/tailscale-network-topology-mapper/blob/main/.github/workflows/tailscale.yml)

## Limitations

* This project is in an early alpha stage.
* It can only map what is available in the Tailscale 'policy.hujson' policy file. It is not an active scanning tool that will seek out other hosts.
* It only focuses on the ACL/Grant rules themselves but eventually this may start capturing ALL the available valid Tailscale sections.

Pull requests welcome! :)

## Experimental Ideas and TODOs

* Use `tailscale debug netmap` to build a more in-depth map
* Allow switching between layers such as port level, host level, user/group level
* Enhanced searching by keyword
* Improve overall site design

### Disclaimer:
This project is an independent creation and is not affiliated with Tailscale or its partners. It is solely intended as an expansion upon Tailscale's tools.
