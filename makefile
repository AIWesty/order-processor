.PHONY: all build-grpc #показывает чему выполняться


all: build-grpc #цель


build-grpc: #программа цели
	mkdir -p services/billing/app/grpc

	python -m grpc_tools.protoc \
		-I services/billing/proto \
		--python_out=services/billing/app/grpc \
		--grpc_python_out=services/billing/app/grpc \
		services/billing/proto/payment.proto
