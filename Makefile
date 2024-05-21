build:
	docker image build -t tailscale_visualizer .

push:
	docker push tailscale_visualizer

run: 
	docker run --name tailscale_visualizer -d -p 8080:8080 tailscale_visualizer

clean:
	docker rm -f tailscale_visualizer

