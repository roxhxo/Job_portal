# JOB_RESUME_MATCHER
This repository handles all the code files related to project entitled to show the match percentage of a candidate profile with a job description and vice versa

Tools Needed
1. Pycharm IDE Community Edition 
2. Python Interpreter 3.10.10
3. Git Client 2.40.0
4. MongoDB Database Community Edition 6.0.5
5. MongoDB Compass Edition 1.36.4



Download Links 
1. Pycharm IDE Community Edition can be downloaded here as per respective operating system - https://www.jetbrains.com/pycharm/download/
2. Python interpreter 3.10.10 can be downloaded here as per respective operating system - https://www.python.org/downloads/
3. Git Client 2.40.0 can be downloaded here as per respective operating system - https://git-scm.com/downloads
4. MongoDB Database Community Edition 6.0.5 can be downloaded as per respective operating system - https://www.mongodb.com/try/download/community
4. MongoDB Compass 1.36.4 can be downloaded as per respective operating system - https://www.mongodb.com/try/download/compass

Important Reference Links
1. https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-os-x/
2. https://linuxhint.com/start-mongodb-server-windows/
3. https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-windows/

Important Terminal Commands
1. pip install -r requirements.txt (Install python packages using requirements.txt file)
2. pip freeze (View package installed in virtual environment)
3. pip install virtualenv (Installing virtual environment)
4. virtualenv --version (Testing virtual environment)
5. virtualenv my_name (Creating virtual environment)
6. cd virenv_name -> Scripts\activate.bat (To activate virtual environment on windows)
7. source virtualenv_name/bin/activate (To activate virtual environment on linux/mac)
8. cd virenv_name -> Scripts\deactivate.bat (To deactivate virtual environment on windows)
9. deactivate (To deactivate virtual environment on linux/mac)
10. pip install package_name==version (To install any particular python package with version)
11. pip install package_name (To install latest python package)

MongoDB Server (Need to run as a service on any operating system)
1. To start mongod on mac os, open terminal and execute brew services start mongodb-community@6.0
2. To stop mongod on mac os, open terminal and execute brew services stop mongodb-community@6.0
3. C:\data\db needs to be present in windows system to make mongodb work and also the mongodb download path needs to be added in path variable of environment. 
4. "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe" --dbpath="c:\data\db"
5. For using any other ip and port bind ip property can be used.
 

# Running Flask Server as command line
### For Linux/Unix/MacOS :-
export FLASK_APP = sample.py
flask run

### For Windows :-
python sample.py
OR
set FLASK_APP = sample.py
flask run

Debugging
1. Please make sure flask code is running in background and mongodb server is also running. 
2. In case code sometimes does not work in chrome or give 403 forbidden error, please try clearing cache and try again. 
3. Make sure all the routes defined in the webpage are present in the flask server.
