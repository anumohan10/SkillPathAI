
  
    

        create or replace transient table SKILLPATH_DB.RAW_DATA.edx_courses
         as
        (
 
SELECT * FROM EDX_COURSES
        );
      
  