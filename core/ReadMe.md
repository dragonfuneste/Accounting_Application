# General Structure of core 

## model
It's where you put the fundamental concept of the app Here you will have : 
    - Compte.py : represent one individual account and his manipulation

## services 
It's the high level logic. It's the operation that link multiple object and rules together


## persistance 
It's the layer to acces the data from a db to something we can exploit
    - Database.py
    - Convertion.py

## Variables
It's where we store the variable that can be accessible by all of the class  
    - Variable.py