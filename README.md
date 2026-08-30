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

### Device Mapping (optional)
With `--with-devices`, the map also answers *which machine is that?*:
- **Counts on every tag node**: `tag:production (3)` — a tag nothing carries reads `(0)`
- **Names in the tooltip**: the devices carrying the tag
- **Click a tag** to show exactly the devices carrying it
- **A "Show devices" button** to draw all of them at once
- **A note** listing devices whose tags appear in no rule

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

To use Tailscale's API for validation instead of the built-in offline sanity checks, see the [Using Tailscale's API for Validation](#using-tailscales-api-for-validation) section below.

View all the available commands

`uvx tailscale-network-topology-mapper --help`

---
#### Option 2: Using uv (Recommended for Development)
<details close>
<summary><b>Show uv installation</b></summary>

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
   </details>


#### Option 3: Using pip (Traditional Method)
   <details close>
   <summary><b>Show Traditional pip installation</b></summary>

1. Clone the repo:
   ```bash
   git clone https://github.com/SimplyMinimal/tailscale-network-topology-mapper
   cd tailscale-network-topology-mapper
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   </details>

---

### Configuration
   <details close>
   <summary><b>Click to show Optional configuration</b></summary>

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

   3. Set your Tailscale API key and tailnet environment variables for Tailscale API validation:
      ```bash
      export TAILSCALE_API_KEY=your-api-key
      export TAILSCALE_TAILNET=your-tailnet
      ```
   </details>

---

### Using Tailscale's API for Validation
<details close>
<summary><b>Click to show setup for Tailscale API Validation</b></summary>

By default, the tool validates your policy using local structure validation without an API key as a best-effort validation. However, you can optionally configure the tool to use Tailscale's API for validation. This provides a more accurate validation but requires setting up environment variables for your Tailscale API key and tailnet. It's recommended to protect the environment variables which is out of the scope of this tool for now.

#### Setup

1. **Get your Tailscale API Key**:
   - Go to the [Tailscale Admin Console](https://login.tailscale.com/admin/settings/keys)
   - Create a new API access token

2. **Get your Tailnet Name**:
   - This is typically your organization name (e.g., `example.com` in `https://login.tailscale.com/admin/settings/general`). You can use either Tailnet ID or Legacy ID. 

3. **Set Environment Variables** (or use command line flags):

   macOS/Linux
   ```bash
   # Set your API key
   export TAILSCALE_API_KEY=tskey-api-xxxxx

   # Set your tailnet
   export TAILSCALE_TAILNET=yourcompany.com
   ```

   Windows
   ```bash
   # Set your API key
   set TAILSCALE_API_KEY=tskey-api-xxxxx

   # Set your tailnet
   set TAILSCALE_TAILNET=yourcompany.com
   ```

   <!-- Alternatively, you can set these variables using the OS native credential manager
   <details close>
   <summary><b>Show me how to set secure environment variables on my OS</b></summary>

   ### macOS
   Set the environment variables:
   ```bash
   security add-generic-password -a "tailscale" -s "api_key" -w "tskey-api-xxxxx"
   security add-generic-password -a "tailscale" -s "tailnet" -w "yourcompany.com"
   ```

   Retrieve the environment variables:
 
   ```bash
   export TAILSCALE_API_KEY=$(security find-generic-password -a "tailscale" -s "api_key" -w)
   export TAILSCALE_TAILNET=$(security find-generic-password -a "tailscale" -s "tailnet" -w)
   ```
   </details> 
   
   TODO: Add instructions on managing environment variables for Windows and Linux
   -->
#### Command Line Flags

You can also use command line flags to control validation and provide credentials:

- `--validate-with-tailscale-api` / `--tv`: Enable using Tailscale API for validation. If not used, falls back to local offline validation.
- `--tailscale-api-key`: Provide API key via command line (overrides environment variable `TAILSCALE_API_KEY`).
- `--tailscale-tailnet`: Provide tailnet via command line (overrides environment variable `TAILSCALE_TAILNET`).

Example:
```bash
python3 main.py --validate-with-tailscale-api --tailscale-api-key tskey-api-xxxxx --tailscale-tailnet yourcompany.com
```

#### Usage

Once the environment variables (or command line flags) are set, the tool will automatically use Tailscale's API for validation:
```bash
# The tool will now validate via Tailscale's API
uvx tailscale-network-topology-mapper
# or
python3 main.py
```

If the environment variables are not set and no command line flags are provided, the tool falls back to internal sanity checks for policy validation.
</details>

### Fetching Policy File from Tailscale API
<details close>
<summary><b>Click to show remote policy file setup</b></summary>

Instead of using a local policy file, you can fetch the policy file directly from the Tailscale API. This requires the same API credentials as validation.

#### Command Line Flags

- `--use-remote-tailscale-policy-file` / `--tpf`: Fetch policy file via Tailscale API (default: false). Cannot be used together with `--policy-file`.

#### Usage

```bash
# Fetch policy from Tailscale API and generate map
python3 main.py --use-remote-tailscale-policy-file --tailscale-api-key tskey-api-xxxxx --tailscale-tailnet yourcompany.com
```

When using remote policy file, validation is skipped entirely (the policy fetched from the API is already validated by Tailscale).

Note: You cannot specify both `--use-remote-tailscale-policy-file` and `--policy-file`. The tool will exit with an error if both are provided.
</details>

---

### Mapping Tags onto Devices
<details close>
<summary><b>Click to show device mapping setup</b></summary>

The policy file states what a tag may do. It does not state which machine
carries that tag, so a tag node on the map stands for a rule rather than for
hardware. `--with-devices` reads the tailnet's devices from the Tailscale API
and draws the missing half.

#### Command Line Flags

- `--with-devices` / `--wd`: Read tag membership from the Tailscale API (default: false).

It uses the same credentials as validation and the remote policy file, and
fails with a clear message when they are absent.

#### Usage

```bash
# Local policy file, device membership from the API
python3 main.py --with-devices --tailscale-api-key tskey-api-xxxxx --tailscale-tailnet yourcompany.com

# With the environment variables already set
python3 main.py --with-devices

# Both halves from the API: the live policy and its devices
python3 main.py --use-remote-tailscale-policy-file --with-devices
```

#### What you get

- Every `tag:` node carries its device count in the label and the device names
  in its tooltip. A tag named in a rule that no device carries shows `(0)`,
  which is otherwise invisible on the map.
- Clicking a tag node draws exactly the devices carrying it. The existing
  neighbourhood highlight greys the rest at the same time, so the view is one
  rule set against the machines it applies to. Clicking empty canvas clears it.
- A **Show devices** button draws every device at once. It is off on load —
  on a real tailnet the device layer is large enough to obscure the rule graph
  underneath.
- A device whose every tag is absent from the policy has nowhere to attach: no
  rule names it as a source and none as a destination. Those devices are listed
  in a note rather than dropped silently.

Devices owned by a user rather than by a tag carry no tags and do not appear;
the map is drawn from the policy, and the policy has nothing to say about them.

</details>

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

# Use Tailscale API for validation with command line credentials
python3 main.py --validate-with-tailscale-api --tailscale-api-key tskey-api-xxxxx --tailscale-tailnet yourcompany.com

# Fetch policy file directly from Tailscale API (skips local file)
python3 main.py --use-remote-tailscale-policy-file --tailscale-api-key tskey-api-xxxxx --tailscale-tailnet yourcompany.com

# Use remote policy file with debug logging
# This assumes you already have environment variables set for `TAILSCALE_API_KEY` and `TAILSCALE_TAILNET`
python3 main.py --use-remote-tailscale-policy-file --debug

# Show which devices carry which tag (needs API credentials)
python3 main.py --with-devices

# Custom output path
python3 main.py --output custom-output.html
```

This creates (or updates) `network_topology.html`. Open it in any browser.

---

## 🐳 Running with Docker
  <details close>
  <summary><b>Docker instructions</b></summary>
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

### Using Docker Compose

For easier configuration with your own policy file, use the included `docker-compose.yml`:

```bash
# Place your policy.hujson in the project directory, then run:
docker compose up
```

This will start the container with your policy file mounted. Open [http://localhost:8080](http://localhost:8080) in your browser.
</details>

---

## 🔁 Automate with GitHub Actions

Want your map to update automatically when you change your ACL?

Check out this sample workflow:  
[`.github/workflows/tailscale.yml`](https://github.com/SimplyMinimal/tailscale-network-topology-mapper/blob/main/.github/workflows/tailscale.yml)

---

## ⚠️ Limitations

- Still in **alpha**—expect some rough edges.
- Parses what’s in `policy.hujson`. Devices appear only with `--with-devices`, and that reads the device list from the API rather than probing the network.
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
