{% macro create_stg_udacity_raw() %}
    CREATE or REPLACE TABLE {{ target.database }}.RAW_DATA.STG_UDACITY_RAW (RAW_CONTENT VARIANT);
{% endmacro %}

{% macro copy_to_stg_udacity_raw() %}
    COPY INTO STG_UDACITY_RAW FROM @{{ target.database }}.RAW_DATA.UDACITY_SCRAPED_STAGE FILE_FORMAT = (FORMAT_NAME = {{ target.database }}.{{ target.schema }}.JSON_FORMAT) ON_ERROR = 'CONTINUE';
{% endmacro %}
