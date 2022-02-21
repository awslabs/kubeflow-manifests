FROM golang:1.17.7-alpine3.15 as builder
ENV GOPROXY=direct
RUN apk update && apk add git
ADD *.go /go/src/aws-authservice/
WORKDIR /go/src/aws-authservice
COPY go.mod . 
COPY go.sum .
RUN go mod download
RUN go build -o /go/bin/aws-authservice
FROM alpine:3.15

RUN apk add --no-cache ca-certificates
RUN addgroup -S auth && adduser -S -G auth authuser
USER authuser
WORKDIR /app
COPY --from=builder /go/bin/aws-authservice /app/
ENTRYPOINT [ "./aws-authservice" ]
