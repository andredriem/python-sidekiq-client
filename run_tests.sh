#!/bin/bash
docker-compose -f docker-compose-test.yml up --build -d redis
docker-compose -f docker-compose-test.yml run --rm sidekiq-client-test
TEST_EXIT_CODE=$?
docker-compose down
exit $TEST_EXIT_CODE
