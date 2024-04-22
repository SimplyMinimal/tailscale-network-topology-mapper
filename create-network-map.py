import os
import json
import hjson
from pyvis.network import Network

# TODO: Update your company domain here
COMPANY_DOMAIN="example.com"

def load_json_or_hujson_file(filename):
    if not os.path.isfile(filename):
        print(f"Error: File '{filename}' not found.")
        return None

    with open(filename, 'r') as f:
        # Try loading as JSON
        try:
            data = json.load(f)
            return data
        except ValueError:
            # If loading as JSON fails, try loading as HuJSON
            f.seek(0)
            try:
                data = hjson.load(f)
                return data
            except Exception as e:
                print(f"Error decoding '{filename}' as HuJSON: {e}")
                return None


# Step 1: Parse the ACL File using json
acl_file_path = 'policy.hujson'
acl_data = load_json_or_hujson_file(acl_file_path)
if acl_data is None:
    print("Error: Could not parse ACL policy file")
    exit(1)

# Step 2: Extract Hosts, Groups, and Tag Owners
hosts = acl_data.get('hosts', {})
groups = acl_data.get('groups', {})
tag_owners = acl_data.get('tagOwners', {})

# Step 3: Extract ACL Rules
acls = acl_data.get('acls', [])

# Preprocess ACL rules to merge nodes with similar hostnames
merged_acls = []
for rule in acls:
    src = set()
    dst = set()
    for node in rule['src']:
        if node.startswith('tag:'):
            src.add(node)  # Preserve the entire tag format
            #src.add(node.split(':')[1])  # Extract tag name
        elif node.startswith('autogroup:'):
            src.add(node)  # Preserve the entire autogroup format
        elif node.startswith('group:'):
            src.add(node)  # Preserve the entire group format
            #src.add(node.split(':')[1])  # Extract group name
        else:
            hostname = node.split(':')[0]  # Extract hostname
            src.add(hostname)
    for node in rule['dst']:
        if node.startswith('tag:'):
            dst.add(node)  # Preserve the entire tag format
            #dst.add(node.split(':')[1])  # Extract tag name
        elif node.startswith('autogroup:'):
            dst.add(node)  # Preserve the entire autogroup format
            #dst.add(node.split(':')[1])  # Extract group name
        elif node.startswith('group:'):
            dst.add(node)  # Preserve the entire group format
            #dst.add(node.split(':')[1])  # Extract group name
        else:
            hostname = node.split(':')[0]  # Extract hostname
            dst.add(hostname)
    merged_acls.append({'action': rule['action'], 'src': src, 'dst': dst})

# Step 4: Construct Network Topology Graph
net = Network(height="800px", width="100%", notebook=True, directed=True, filter_menu=True,select_menu=True,neighborhood_highlight=True, cdn_resources='remote')

# Define colors for different node types
group_color = "#FFFF00"  # Group color (Yellow)
tag_color = "#00cc66"    # Tag color (Green)
host_color = "#ff6666"   # Host color (Red)

# TODO: Coalesce this into a smaller function
# Add nodes and edges based on preprocessed ACL rules
for rule in merged_acls:
    for src in rule['src']:
        if src.startswith('tag:'):
            net.add_node(src, color=tag_color)
        elif COMPANY_DOMAIN in src:
            net.add_node(src, color=group_color)
        elif src.startswith('autogroup:'):
            net.add_node(src, color=group_color)
        elif 'group:' in groups:
            net.add_node(src, color=group_color)
        else:
            net.add_node(src, color=host_color)
            
        for dst in rule['dst']:
            if dst.startswith('tag:'):
                net.add_node(dst, color=tag_color)
            elif COMPANY_DOMAIN in dst:
                net.add_node(dst, color=group_color)
            elif dst.startswith('autogroup:'):
                net.add_node(dst, color=group_color)                
            elif 'group:' in groups:
                net.add_node(dst, color=group_color)
            else:
                net.add_node(dst, color=host_color)
            net.add_edge(src, dst, arrows={'to': {'enabled': True}})  # Specify arrow options as a dictionary


# Step 5: Add a legend for the colors
legend_html = """
<div style="position: absolute; top: 10px; right: 10px; background-color: #f5f5f5; padding: 10px; border: 1px solid #ccc;">
    <h3>Legend</h3>
    <div style="background-color: """ + group_color + """; width: 20px; height: 20px; display: inline-block;"></div>
    <span>Group</span><br>
    <div style="background-color: """ + tag_color + """; width: 20px; height: 20px; display: inline-block;"></div>
    <span>Tag</span><br>
    <div style="background-color: """ + host_color + """; width: 20px; height: 20px; display: inline-block;"></div>
    <span>Host</span>
</div>
"""

# Inject the legend HTML into the network visualization
net.show_buttons()
net.write_html("network_topology.html")
with open("network_topology.html", "a") as f:
    f.write(legend_html)
