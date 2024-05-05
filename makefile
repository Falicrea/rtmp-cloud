.PHONY: install

n ?= 50

install:
	@make build
	@make up
	@make start-rtmp
	@make right

build:
	docker compose build

up:
	docker compose up -d

start-rtmp:
	docker exec -u root rtmp ./start-rtmp $(args)
	docker exec -u root rtmp service fcgiwrap start
	docker exec -u root rtmp bash -c "perl -MCPAN -e 'install CGI'"
	
restart-rtmp:
	docker exec -u root rtmp ./restart-rtmp $(args)
	
stop-rtmp:
	docker exec -u root rtmp ./stop-rtmp $(args)
	
logs:
	docker logs -n $(n) rtmp
	docker logs -n $(n) auth_rtmp

right:
	docker exec -u root rtmp bash -c "chown -R www-data:www-data /mnt && chmod -R 777 /mnt"
	docker exec -u root rtmp bash -c "chown -R www-data:www-data /cgi-bin"
	
prune:
	@make stop-rtmp
	docker compose down