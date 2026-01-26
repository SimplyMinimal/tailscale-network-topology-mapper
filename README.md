# Tailscale Network Topology Mapper
### A visual way to view your ACL and Grant rules for Tailscale

I occasionally find myself just wanting to get a glance of how my ACL rules look without reading through the code. This is also useful for showing how our policies are set up to people who are not devs by trade.

![Demo showing the search and filter functionality on the network topology map to narrow down nodes](./images/Demo.gif)

---

## What Is This?

The **Tailscale Network Topology Mapper** is a tool for visualizing your network access rules. It turns your Tailscale ACL and Grant configurations into a self-contained, interactive HTML map—making it easier to understand and share your network layout.

## Key Features

### Network Visualization
- **Interactive Graph**: Generates a `network_topology.html` file you can open or host anywhere.
- **Color-Coded Nodes**:
  - 🟡 Groups
  - 🟢 Tags
  - 🔴 Hosts
- **Shape-Coded Rule Types**:
  - Circles (●) - ACL-only
  - Triangles (▲) - Grant-only
  - Hexagons (⬢) - Nodes in both ACL and Grant rules

### Advanced Search & Filtering
- **Keyword Search**: Find nodes by name, port, protocol, routing, posture checks, or group membership.
- **Highlighting**: Matching nodes are visually marked and highlighted.

### Detailed Tooltips
Hover over nodes to see:
- Rule references (with line numbers)
- Protocols (e.g., `tcp:443`, `udp:53`)
- Via-routing information
- Posture check requirements
- App-level access controls
- Group memberships

### Access Relationships
- **Directional Edges**: Arrows show who can talk to whom.
- **Legacy + Modern Rule Support**: Handles ACLs and Grant rules simultaneously.
- **Protocol Display**: Shows IP protocol details for destination nodes.

### Interactive UI
- Movable search box (drag-and-drop)
- Smooth zoom controls (configurable)
- Connected node highlighting when selected

## Supported Tailscale Features

- **Policy Formats**: JSON and HuJSON (Human JSON)
- **Modern Grant Support**:
  - IP protocols (`tcp`, `udp`, `icmp`, etc.)
  - Via-routing
  - Posture checks
  - Application-level access controls
- **Legacy ACL Compatibility**: Full support for traditional ACL rules

## 🛠️ Setup Instructions

### Requirements
- Python 3.10+
- Git
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

---
### Installation Methods

#### Option 1: Using uvx (Recommended - No Installation Required!)

The fastest way to run the mapper without any installation:

```bash
# Add your policy.hujson file to current directory (see configuration section below)
# Then run directly with uvx
uvx tailscale-network-topology-mapper
```

This will run the latest version of the mapper against the policy file (`policy.hujson`). You will now have a `network_topology.html` file in the current directory that you can open in your browser.

Optionally, you can point the tool to a specific policy file:
```bash
uvx tailscale-network-topology-mapper --policy-file /path/to/your/policy.hujson
```


---
#### Option 2: Using uv (Recommended for Development)

1. Install uv if you haven't already:
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Clone and set up:
   ```bash
   git clone https://github.com/SimplyMinimal/tailscale-network-topology-mapper
   cd tailscale-network-topology-mapper

   # Install dependencies
   uv pip install -r requirements.txt
   ```

#### Option 3: Using pip (Traditional Method)

1. Clone the repo:
   ```bash
   git clone https://github.com/SimplyMinimal/tailscale-network-topology-mapper
   cd tailscale-network-topology-mapper
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

### Configuration

1. Add your policy:
   - Replace the contents of `policy.hujson` with your actual Tailscale ACL.

2. Set your company domain:
   - Edit `config.py` and change:
     ```python
     COMPANY_DOMAIN = "example.com"
     ```
   - Or set an environment variable:
     ```bash
     export TS_COMPANY_DOMAIN=yourcompany.com
     ```

---

### Generate the Map

```bash
# Using uvx (no installation needed)
uvx tailscale-network-topology-mapper

# Using uv
uv run python main.py

# Using traditional Python
python3 main.py

# Enable debug logging with any method by adding --debug
python3 main.py --debug
```

This creates (or updates) `network_topology.html`. Open it in any browser.

---

## 🐳 Running with Docker

If you prefer Docker:

### Prerequisites
- Docker
- `make`

### Run It
```bash
make build run
```

Then open [http://localhost:8080](http://localhost:8080) in your browser.

> Use the filter bar or click on any node to narrow down the view.

---

## 🔁 Automate with GitHub Actions

Want your map to update automatically when you change your ACL?

Check out this sample workflow:  
[`.github/workflows/tailscale.yml`](https://github.com/SimplyMinimal/tailscale-network-topology-mapper/blob/main/.github/workflows/tailscale.yml)

---

## ⚠️ Limitations

- Still in **alpha**—expect some rough edges.
- Only parses what’s in `policy.hujson`. It doesn’t actively discover devices.
- Currently focused only on ACL and Grant rules (other policy sections may be supported in future versions).

---

## 🧪 Experimental & TODOs

- Integrate `tailscale debug netmap` for deeper insights
- Add view toggles: ports, hosts, users/groups
- Improve the visual design and layout

---

## 📢 Disclaimer

This is an independent project and not affiliated with Tailscale.  
It’s designed as a companion tool to better understand and visualize your Tailscale network policies.

---

### 🙌 Contributions Welcome!

Pull requests, suggestions, and feedback are appreciated!
