.PHONY: install

n ?= 50
user ?= root

install:
	@make build
	@make up
	@make run
	@make right

build:
	docker compose build

up:
	docker compose up -d

run:
	@make start-rtmp
	docker exec -u $(user) rtmp bash -c "service fcgiwrap start && perl -MCPAN -e 'install CGI'"
	
start-rtmp:
	docker exec -u $(user) rtmp ./start-rtmp
	
restart-rtmp:
	docker exec -u $(user) rtmp ./restart-rtmp
	
stop-rtmp:
	docker exec -u $(user) rtmp ./stop-rtmp
	
logs:
	docker logs -n $(n) rtmp
	docker logs -n $(n) auth_rtmp

right:
	docker exec -u $(user) rtmp bash -c "chown -R www-data:www-data /mnt && chmod -R 777 /mnt"
	docker exec -u $(user) rtmp bash -c "chown -R www-data:www-data /cgi-bin"
	
prune:
	@make stop-rtmp
	docker compose down