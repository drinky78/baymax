build:
	docker-compose build

up:
	docker-compose up -d

stop:
	docker-compose stop

ssh:
	docker exec -it baymax bash

go:
	docker-compose exec baymax python quickstart/$(filter-out $@,$(MAKECMDGOALS))

go3:
	docker-compose exec baymax python3 quickstart/$(filter-out $@,$(MAKECMDGOALS))

logs:
	open http://localhost:6006
