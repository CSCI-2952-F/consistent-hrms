module github.com/irvinlim/cs2952f-hrms/src/loadtesting

go 1.14

replace go.etcd.io/etcd => go.etcd.io/etcd v0.5.0-alpha.5.0.20200329194405-dd816f0735f8

require (
	github.com/irvinlim/cs2952f-hrms/src/discovery v0.0.0-20200430223517-7f6c286b4981
	github.com/irvinlim/cs2952f-hrms/src/golang-lib v0.0.0-20200512184823-73fcc292eb7f
	go.etcd.io/etcd v3.3.20+incompatible // indirect
	go.uber.org/zap v1.15.0 // indirect
	golang.org/x/net v0.0.0-20200425230154-ff2c4b7c35a0 // indirect
	golang.org/x/sys v0.0.0-20200430202703-d923437fa56d // indirect
	google.golang.org/genproto v0.0.0-20200430143042-b979b6f78d84 // indirect
	google.golang.org/grpc v1.29.1 // indirect
)
