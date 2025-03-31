
  
    

        create or replace transient table SKILLPATH_DB.RAW_DATA.COURSERA_COURSES
         as
        (

-- This SELECT statement is required by dbt. It simply returns the contents of the table.
SELECT * FROM COURSERA_COURSES
        );
      
  