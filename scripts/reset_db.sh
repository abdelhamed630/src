#!/bin/sh
echo "This will DELETE all database data and start fresh."
printf "Are you sure? (yes/no): "
read confirm
if [ "$confirm" = "yes" ]; then
    docker-compose down -v
    docker-compose up -d
    echo "Done! Fresh database started."
else
    echo "Cancelled."
fi
