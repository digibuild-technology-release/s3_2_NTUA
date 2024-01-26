-- init.sql

-- Create a new database user with the desired username and password
CREATE USER digibuild WITH ENCRYPTED PASSWORD 'digibuild';

-- Grant necessary privileges to the user on the database (replace 'your_database_name' with your actual database name)
GRANT ALL PRIVILEGES ON DATABASE s323 TO digibuild;