
  create or replace   view SKILLPATH_DB.RAW_DATA.my_second_dbt_model
  
   as (
    -- Use the `ref` function to select from other models

select *
from SKILLPATH_DB.RAW_DATA.my_first_dbt_model
where id = 1
  );

