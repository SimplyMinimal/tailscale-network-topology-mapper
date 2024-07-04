from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route('/')
def serve_network_topology():
    return send_from_directory('/app/tailscale-network-topology-mapper/', 'network_topology.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

