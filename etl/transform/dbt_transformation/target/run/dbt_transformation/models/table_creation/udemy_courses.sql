
  
    

        create or replace transient table SKILLPATH_DB.RAW_DATA.udemy_courses
         as
        (
 
SELECT * FROM UDEMY_COURSES
        );
      
  