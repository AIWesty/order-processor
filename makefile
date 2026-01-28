.PHONY: all build-grpc #показывает чему выполняться


all: build-grpc #цель


build-grpc: #программа цели, общий grpc в libs для сервисов
	mkdir -p libs/grpc

	python -m grpc_tools.protoc \ 
    	-I./libs/grpc/protos \
    	--python_out=./libs/grpc \
    	--grpc_python_out=./libs/grpc \
    	--pyi_out=./libs/grpc \
    	./libs/grpc/protos/payment.proto
