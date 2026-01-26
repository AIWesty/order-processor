.PHONY: all build-grpc #показывает чему выполняться


all: build-grpc #цель


build-grpc: #программа цели, общий grpc в libs для сервисов
	mkdir -p libs/grpc

	python -m grpc_tools.protoc \
		-I services/billing/proto \
		--python_out=libs/grpc \
		--grpc_python_out=libs/grpc \
		services/billing/proto/payment.proto
