
  
    

        create or replace transient table SKILLPATH_DB.RAW_DATA.pluralsight_courses
         as
        (
 
SELECT * FROM PLURALSIGHT_COURSES
        );
      
  