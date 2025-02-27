{% macro infer_schema_file_format() %}
{% set sql %}
    CREATE OR REPLACE FILE FORMAT inferSchema TYPE = 'csv', parse_header = TRUE, FIELD_OPTIONALLY_ENCLOSED_BY = '"', COMPRESSION = 'AUTO'
{% endset %}
{{ run_query(sql) }}
{% endmacro %}
