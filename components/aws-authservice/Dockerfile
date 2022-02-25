FROM public.ecr.aws/docker/library/golang:1.17 as builder
ENV GOPROXY=direct
RUN apk update && apk add git
ADD *.go /go/src/aws-authservice/
WORKDIR /go/src/aws-authservice
COPY go.mod . 
COPY go.sum .
RUN go mod download
RUN go build -o /go/bin/aws-authservice
FROM public.ecr.aws/amazonlinux/amazonlinux:2022

RUN apk add --no-cache ca-certificates
RUN addgroup -S auth && adduser -S -G auth authuser
USER authuser
WORKDIR /app
COPY --from=builder /go/bin/aws-authservice /app/
ENTRYPOINT [ "./aws-authservice" ]
