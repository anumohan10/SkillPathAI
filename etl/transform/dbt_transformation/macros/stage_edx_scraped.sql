{% macro create_stg_edx_raw() %}
    CREATE or REPLACE TABLE {{ target.database }}.{{ target.schema }}.STG_EDX_RAW (RAW_CONTENT VARIANT);
{% endmacro %}

{% macro copy_to_stg_edx_raw() %}
    COPY INTO STG_EDX_RAW FROM @{{ target.database }}.{{ target.schema }}.EDX_SCRAPED_STAGE FILE_FORMAT = (FORMAT_NAME = {{ target.database }}.{{ target.schema }}.JSON_FORMAT) ON_ERROR = 'CONTINUE';
{% endmacro %}