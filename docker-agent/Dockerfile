FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod ./
COPY main.go ./
RUN CGO_ENABLED=0 go build -o /arsy-agent .

FROM alpine:3.20
RUN apk add --no-cache docker-cli postgresql15-client
COPY --from=build /arsy-agent /usr/local/bin/arsy-agent
ENV BACKUP_DIR=/backups
EXPOSE 8080
ENTRYPOINT ["arsy-agent"]
