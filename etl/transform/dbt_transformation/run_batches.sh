#!/bin/bash

max_course_id=4582612
batch_size=100000

for (( lower=0; lower<=max_course_id; lower+=batch_size )); do
  upper=$(( lower + batch_size ))
  echo "Processing course_id range: $lower to $upper"
  dbt run --models stg_udemy_course_prerequisites --vars "{ \"course_id_lower\": $lower, \"course_id_upper\": $upper }"
done
