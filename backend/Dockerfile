FROM maven:3.9-eclipse-temurin-17 AS build

WORKDIR /workspace

COPY pom.xml .
RUN mvn -B dependency:go-offline

COPY src ./src
RUN mvn -B -DskipTests package

FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

RUN apk add --no-cache wget su-exec iproute2 \
    && addgroup -g 10001 -S kinlin \
    && adduser -S -D -H -u 10001 -G kinlin kinlin \
    && mkdir -p /app/data/uploads /run/kinlin-secrets \
    && chown -R 10001:10001 /app /run/kinlin-secrets

COPY --from=build /workspace/target/federal-hub-backend-*.jar /app/app.jar
COPY docker-entrypoint.sh /usr/local/bin/kinlin-entrypoint
RUN chmod 0755 /usr/local/bin/kinlin-entrypoint

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/kinlin-entrypoint"]
CMD ["java", "-jar", "/app/app.jar"]
