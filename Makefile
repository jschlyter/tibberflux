SOURCE=	tibberflux.py

all: reformat lint
	
reformat:
	isort $(SOURCE)
	black $(SOURCE)

lint:
	pylama $(SOURCE)

build:
	poetry build

container: build
	docker build -t tibberflux .

clean:
	rm -fr dist
