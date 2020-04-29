module github.com/irvinlim/cs2952f-hrms/src/centraldb

go 1.14

// Temporary fix: https://github.com/etcd-io/etcd/issues/11563#issuecomment-620474246
replace go.etcd.io/etcd => go.etcd.io/etcd v0.5.0-alpha.5.0.20200329194405-dd816f0735f8

require (
	github.com/go-sql-driver/mysql v1.5.0
	github.com/golang/protobuf v1.4.0
	github.com/irvinlim/cs2952f-hrms/src/discovery v0.0.0-20200429215057-ea64aaa5e756
	github.com/irvinlim/cs2952f-hrms/src/golang-lib v0.0.0-20200429214447-9aefaee7bd86 // indirect
	go.uber.org/zap v1.15.0 // indirect
	golang.org/x/net v0.0.0-20200425230154-ff2c4b7c35a0 // indirect
	golang.org/x/sys v0.0.0-20200428200454-593003d681fa // indirect
	google.golang.org/genproto v0.0.0-20200429120912-1f37eeb960b2 // indirect
	google.golang.org/grpc v1.29.1
)
