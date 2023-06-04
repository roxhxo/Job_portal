from flask import Flask, render_template, redirect, request, session, jsonify
from nltk.tokenize import word_tokenize
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import ssl
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pymongo import MongoClient
import os
from werkzeug.utils import secure_filename
from bson import ObjectId

# Above we have written import statements for importing packages and using their functionality

# Need to give correct path for folder inside static for profile images
UPLOAD_FOLDER = '/Users/lizakukreja/PycharmProjects/JOB_RESUME_MATCHER/static/profile_images/'

# Normal Variables used in project
ALLOWED_EXTENSIONS = 'png'

# Creation of an instance/object of class Flask and initialization with values
app = Flask(__name__)
app.secret_key = "liza_kukreja"
app.config["MONGO_URI"] = "mongodb://localhost:27017/project"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Creation of an instance/object of class MongoClient and initialization with values
# This will serve as an api between backend and mongodb database server
client = MongoClient('localhost', 27017)

# Below lines of code are just written so that the nltk can download
# required things without ssl verification
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')

# Variable/Object initialization for stop_words and wordnet lemmatizer
stop_words = set(stopwords.words("english"))
wordnet_lemmatizer = WordNetLemmatizer()


# render_template renders the web page and return it properly.
# redirect redirects to any route within the code
# web page request the flask server using routes

# GET and POST requests are handled in the same route
# GET means without data and POST means with data.
# data and method is present inside the request object
# Route is defined in href of a tag and action of form tag

# There are basically four types of database queries used
# insert_one to insert json data
# update_one to update json data based on search query
# delete_one to delete json data based on search query
# find_one, find to find one or all records based on search query
# data format in all cases is mostly json

# Default route for index web page
@app.route('/')
def index():
    return render_template('index.html')


# Default route for about page
@app.route('/about')
def about():
    return render_template('about.html')


# Default route for contact page
@app.route('/contact')
def contact():
    return render_template('contact.html')


# Default route for contact message page
@app.route('/contact_message', methods=['POST'])
def contact_message():
    # Verifying request method and data values
    msg = ''
    if request.method == 'POST' and 'name' in request.form and 'email' in request.form and 'message' in request.form:
        data = dict()
        # reading data values and storing in a variable
        data['name'] = request.form['name']
        data['email'] = request.form['email']
        data['message'] = request.form['message']
        # Inserting message value in the database
        x = client.project.message.insert_one(data)
        if x:
            msg = "Data sent successfully, you will hear back shortly"
        else:
            msg = 'Some problem happened, data not send'
    return render_template('contact.html', msg=msg)


# Default route for login page
@app.route('/login', methods=['POST', 'GET'])
def login():
    msg = ''
    # print(request.method, request.form)
    # condition for post method check and all values present
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        # reading data values from request object
        email = request.form['email']
        password = request.form['password']
        # print(email, password)
        # Searching if the email and password match any record
        user = client.project.user_data.find_one({'email': email, 'password': password})
        # resp = dumps(user)
        if user:
            # setting session parameters
            session['log_status'] = True
            session['email'] = user['email']
            # Returning correct web page based on successful verification
            if user['user_type'] == 1:
                return redirect('/view_candidate')
            else:
                return redirect('/view_recruiter')
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg=msg)


# Default route for signup page
@app.route('/sign_up', methods=['POST', 'GET'])
def sign_up():
    msg = ''
    # condition for post method check and all values present
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form and \
            'hint_questions' in request.form and 'hint_answer' in request.form:
        # reading all values from request module
        email = request.form['email']
        password = request.form['password']
        hint_question = request.form['hint_questions']
        hint_answer = request.form['hint_answer']
        # Identifying the type of user
        if request.form['user_type'] == 'candidate':
            user_type = 1
        else:
            user_type = 2
        # Searching if user already exist
        user = client.project.user_data.find_one({'email': email})
        # Finding question id for selected question
        hint_question_id = client.project.hint_questions.find_one({'question': hint_question})
        if user:
            msg = 'Account already exists !'
        else:
            # Creating json template for data storage
            data = {'email': email,
                    'password': password,
                    'hint_question': hint_question_id['question_id'],
                    'hint_answer': hint_answer,
                    'user_type': user_type}
            # Storing data
            resp = client.project.user_data.insert_one(data)
            if resp:
                msg = 'You have successfully registered !'
            else:
                msg = 'Could not sign up, please try later !'
    return render_template('sign_up.html', msg=msg)


# Default route for sign out page
@app.route('/sign_out')
def sign_out():
    # Overwriting session parameters
    session.pop('log_status', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('email', None)
    return render_template('login.html')


# Default route for forget password page
@app.route('/forget_password', methods=['POST', 'GET'])
def forget_password():
    msg = ''
    # condition for post method check and all values present
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form and \
            'hint_questions' in request.form and 'hint_answer' in request.form:
        # Reading values from request object
        email = request.form['email']
        password = request.form['password']
        hint_question = request.form['hint_questions']
        hint_answer = request.form['hint_answer']
        # Finding question id from hint question table based on hint question
        hint_question_id = client.project.hint_questions.find_one({'question': hint_question})
        question_id = hint_question_id['question_id']
        # Finding record where email, question id and answer matches
        user = client.project.user_data.find_one({'email': email, 'hint_question': question_id,
                                                  'hint_answer': hint_answer})
        # condition check for password check
        if user:
            search_query = {"email": email}
            update_query = {"$set": {"password": password}}
            # Updating new password
            resp = client.project.user_data.update_one(search_query, update_query)
            if resp:
                msg = 'Password Change Successfully !'
            else:
                msg = 'Could not change password, please try later !'
        else:
            msg = 'Incorrect Data, Cannot Change Password'
    return render_template('forget_password.html', msg=msg)


# Default route for error page
@app.errorhandler(404)
def not_found():
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp


# Default page for candidate profile
@app.route('/view_candidate')
def view_candidate():
    msg = ''
    if session:
        # read data from session
        email_id = session['email']
        # Fetching the data from respective candidate databases
        profile_data = client.project.candidate_profile.find_one({'candidate_email': email_id})
        work_data = client.project.candidate_experience.find({'candidate_email': email_id})
        education_data = client.project.candidate_education.find({'candidate_email': email_id})
        skills_data = client.project.candidate_skills.find({'candidate_email': email_id})
        work = []
        education = []
        skills = []
        # Creating a nested list of work, education and skills (multiple records returned)
        for data in work_data:
            work.append([data['work_company'], data['work_duration'], data['work_details']])
        for data in education_data:
            education.append([data['candidate_college'], data['candidate_degree'],
                              data['candidate_year'], data['candidate_marks']])
        for data in skills_data:
            skills.append(data['candidate_skill'])
        skills_data = ",".join(skills)
        # Safe condition because data will be empty in case of first signup
        if profile_data is None:
            profile_data = dict()
            profile_data['candidate_picture'] = ''
            msg = 'No data available'
        return render_template('candidatedefault.html', profile_data=profile_data, msg=msg, work_data=work,
                               education_data=education, skills_data=skills_data, user_name=session['email'])
    else:
        return render_template('login.html')


# Default route for edit candidate
@app.route('/edit_candidate', methods=['POST', 'GET'])
def edit_candidate():
    msg = ''
    email_id = session['email']
    if session:
        # Check for post request
        if request.method == 'POST':
            print(request.form)
            data = dict()
            # if data is coming from skill form
            if 'skills' in request.form:
                skills = request.form['skills']
                # find if skills already exist
                user = client.project.candidate_skills.find_one({'candidate_email': email_id})
                if user:
                    # update skills if skills already exist
                    x = client.project.candidate_skills.update_one(
                        {'candidate_email': email_id}, {'$set': {'candidate_skill': skills}})
                else:
                    # insert skills if not already exist
                    data['candidate_skill'] = skills
                    data['candidate_email'] = email_id
                    x = client.project.candidate_skills.insert_one(data)
                if x:
                    msg = "Skills updated successfully"
                else:
                    msg = "Skills updating failed"
            # form for profile data
            elif 'name' in request.form and 'gender' in request.form and 'dob' in request.form and \
                    'phone' in request.form and 'address' in request.form and 'experience' in request.form and \
                    'language' in request.form:
                # reading profile data
                data['candidate_email'] = email_id
                data['candidate_name'] = request.form['name']
                data['candidate_gender'] = request.form['gender']
                data['candidate_dob'] = request.form['dob']
                data['candidate_contact'] = request.form['phone']
                data['candidate_address'] = request.form['address']
                data['candidate_experience'] = request.form['experience']
                data['candidate_language'] = request.form['language']
                image = request.files['profile_pic']
                # checking if image is uploaded or not
                if image.filename != '':
                    # changing @ and . with underscore
                    name = request.form['email'].replace('.', '_').replace('@', '_') + '.png'
                    name_new = secure_filename(name)
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], name_new))
                    # saving to default path
                    # os.mkdir(f"/static/{name}")
                    # image.save(f"/static/profile_images/{name}")
                else:
                    # if candidate has uploaded picture fetch from database and show that else show default image
                    image = client.project.candidate_profile.find_one({'candidate_email': session['email']})
                    if image['candidate_picture'] not in ['default.png', None]:
                        name = image['candidate_picture']
                    else:
                        name = 'default.png'
                data['candidate_picture'] = name
                # check if record exist
                user = client.project.candidate_profile.find_one({'candidate_email': email_id})
                if user:
                    # update profile since the record exist
                    x = client.project.candidate_profile.update_one({'candidate_email': email_id}, {'$set': data})
                else:
                    # insert profile since the record does not exist
                    x = client.project.candidate_profile.insert_one(data)
                if x:
                    msg = "Profile updated successfully"
                else:
                    msg = "Profile updating failed"
            # form for education data
            if 'college' in request.form and 'degree' in request.form and 'year' in request.form and \
                    'marks' in request.form and 'add' in request.form:
                # read education
                data['candidate_college'] = request.form['college']
                data['candidate_degree'] = request.form['degree']
                data['candidate_year'] = request.form['year']
                data['candidate_marks'] = request.form['marks']
                data['candidate_email'] = session['email']
                # Insert the education data
                x = client.project.candidate_education.insert_one(data)
                if x:
                    msg = "New education details added successfully"
                else:
                    msg = "Error occurred during adding educational details"
            # form for update education data
            if 'college' in request.form and 'degree' in request.form and 'year' in request.form and \
                    'marks' in request.form and 'update' in request.form:
                # read the education data
                data['candidate_college'] = request.form['college']
                data['candidate_degree'] = request.form['degree']
                data['candidate_year'] = request.form['year']
                data['candidate_marks'] = request.form['marks']
                data['candidate_email'] = session['email']
                # updating the education data
                x = client.project.candidate_education.update_one({'_id': ObjectId(request.form['edu_id'])},
                                                                  {"$set": data})
                if x:
                    msg = "Updated education details successfully"
                else:
                    msg = "Error occurred during updating educational details"
            # form for delete data
            if 'college' in request.form and 'degree' in request.form and 'year' in request.form and \
                    'marks' in request.form and 'delete' in request.form:
                # delete the education data
                x = client.project.candidate_education.delete_one({'_id': ObjectId(request.form['edu_id'])})
                if x:
                    msg = "Education details deleted successfully"
                else:
                    msg = "Error occurred during deleting educational details"
            # form for insert work data
            if 'company' in request.form and 'duration' in request.form and 'details' in request.form and \
                    'add' in request.form:
                # read work data
                data['work_company'] = request.form['company']
                data['work_duration'] = request.form['duration']
                data['work_details'] = request.form['details']
                data['candidate_email'] = session['email']
                # insert work data
                x = client.project.candidate_experience.insert_one(data)
                if x:
                    msg = "New work details added successfully"
                else:
                    msg = "Error occurred during adding work details"
            # update work data
            if 'company' in request.form and 'duration' in request.form and 'details' in request.form and \
                    'update' in request.form:
                # read work data
                data['work_company'] = request.form['company']
                data['work_duration'] = request.form['duration']
                data['work_details'] = request.form['details']
                data['candidate_email'] = session['email']
                # update work data
                x = client.project.candidate_experience.update_one({'_id': ObjectId(request.form['work_id'])},
                                                                   {"$set": data})
                if x:
                    msg = "Updated work details successfully"
                else:
                    msg = "Error occurred during updating work details"
            # delete work data
            if 'company' in request.form and 'duration' in request.form and 'details' in request.form and \
                    'delete' in request.form:
                # delete record based on object id
                x = client.project.candidate_experience.delete_one({'_id': ObjectId(request.form['work_id'])})
                if x:
                    msg = "Work details deleted successfully"
                else:
                    msg = "Error occurred during deleting work details"
        # in case method is get on edit request
        # read data from different collections
        profile_data = client.project.candidate_profile.find_one({'candidate_email': email_id})
        work_data = client.project.candidate_experience.find({'candidate_email': email_id})
        education_data = client.project.candidate_education.find({'candidate_email': email_id})
        skills_data = client.project.candidate_skills.find({'candidate_email': email_id})
        work = []
        education = []
        skills = []
        # preparing list as the data fields are returning multiple records
        for data in work_data:
            work.append([data['_id'], data['work_company'], data['work_duration'], data['work_details']])
        for data in education_data:
            education.append([data['_id'], data['candidate_college'], data['candidate_degree'],
                              data['candidate_year'], data['candidate_marks']])
        for data in skills_data:
            skills.append(data['candidate_skill'])
        skills_data = ",".join(skills)
        # Safe condition for empty profile data
        if profile_data is None:
            profile_data = dict()
            profile_data['candidate_picture'] = ''
            msg = 'No data available'
        return render_template('edit_candidate.html', profile_data=profile_data, msg=msg, work_data=work,
                               education_data=education, skills_data=skills_data, user_name=session['email'])
    else:
        return render_template('login.html')


# Default route for recruiter page
@app.route('/view_recruiter')
def view_recruiter():
    msg = ''
    if session:
        # Find the recruiter data and return
        user = client.project.employer.find_one({'employer_email': session['email']})
        if user:
            # Fetching User Company
            company_name = client.project.company.find_one({'company_id': user['company_id']})
            if company_name:
                user['company_name'] = company_name['company_name']
            return render_template('recruiter.html', user_name=session['email'], data=user)
        else:
            # if data not available return empty with error message
            msg = 'Error in data retrieval'
            data = dict()
            data['employer_picture'] = ''
            return render_template('recruiter.html', user_name=session['email'], msg=msg, data=data)
    else:
        return render_template('login.html', msg=msg)


# Default page for editing recuiter profile
@app.route('/edit_recruiter', methods=['POST', 'GET'])
def edit_recruiter():
    msg = ''
    if session:
        # Verify method is post and all data is present
        if request.method == 'POST' and 'company_name' in request.form and 'employer_name' in request.form and \
                'employer_contact' in request.form and 'employer_email' in request.form and \
                'employer_address' in request.form and 'employer_dob' in request.form and \
                'employer_gender' in request.form:
            data = dict()
            print(request.form)
            # Check if the company of the employer already exist or not
            company = client.project.company.find_one({'company_name': request.form['company_name']})
            if company:
                data['company_id'] = company['company_id']
            else:
                # if not exist, insert new entry
                counter = client.project.company.count_documents({})
                data['company_id'] = str(counter + 1)
                client.project.company.insert_one(
                    {'company_id': str(counter + 1), 'company_name': request.form['company_name']})
            # reading data input from the form for updating
            data['employer_name'] = request.form['employer_name']
            data['employer_contact'] = request.form['employer_contact']
            data['employer_address'] = request.form['employer_address']
            data['employer_dob'] = request.form['employer_dob']
            data['employer_gender'] = request.form['employer_gender']
            data['employer_email'] = request.form['employer_email']
            image = request.files['profile_pic']
            # Checking if image is empty or not
            if image.filename != '':
                # If not empty save it in folder
                name = request.form['employer_email'].replace('.', '_').replace('@', '_') + '.png'
                name_new = secure_filename(name)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], name_new))
                # os.mkdir(f"/static/{name}")
                # image.save(f"/static/profile_images/{name}")
            else:
                # if empty check the default value in document, if available use that else use default.png
                image = client.project.employer.find_one({'employer_email': session['email']})
                if image['employer_picture'] not in ['default.png', None]:
                    name = image['employer_picture']
                else:
                    name = 'default.png'
            data['employer_picture'] = name
            # Find if the employer data is already available
            employer = client.project.employer.find_one({'employer_email': session['email']})
            if employer:
                # if already exist update the existing one
                status = client.project.employer.update_one({'employer_email': session['email']}, {"$set": data})
            else:
                # if not exist insert the new one
                status = client.project.employer.insert_one(data)
            if status:
                msg = f"Employee Details Has Been Updated For Email : {session['email']}"
            else:
                msg = "Some problem happened, please try later"
            data['company_name'] = request.form['company_name']
            return render_template('edit_recruiter.html', msg=msg, user_name=session['email'], data=data)
        else:
            # if the method is get, find the employer data and return profile and company value
            user = client.project.employer.find_one({'employer_email': session['email']})
            if user:
                company_name = client.project.company.find_one({'company_id': user['company_id']})
                if company_name:
                    user['company_name'] = company_name['company_name']
                return render_template('edit_recruiter.html', user_name=session['email'], data=user)
            else:
                # if data not available return empty data instead of node and also default values
                msg = 'Error in data retrieval'
                user = dict()
                user['employer_email'] = session['email']
                user['employer_picture'] = ''
                return render_template('edit_recruiter.html', user_name=session['email'], data=user, msg=msg)
    else:
        # if session not existing return login page
        return render_template('login.html', msg=msg)


# Default page for viewing job details
@app.route('/job_detail/<job_id>', methods=['GET'])
def job_detail(job_id):
    msg = ''
    if session:
        # Fetch the job data from document and send to webpage
        data = client.project.job_description.find_one({'job_id': job_id})
        if not data:
            msg = f'No data found for job id: {job_id}'
        return render_template('job_detail.html', data=data, msg=msg)
    else:
        return render_template('login.html')


# Default page for create job
@app.route('/create_job', methods=['POST', 'GET'])
def create_job():
    msg = ''
    print(request.form)
    # verify method is post and all fields are available
    if request.method == 'POST' and 'job_title' in request.form and \
            'job_location' in request.form and 'job_type' in request.form and \
            'job_duration' in request.form and 'job_salary_min' in request.form and \
            'job_salary_max' in request.form and 'job_conditions' in request.form and \
            'job_summary' in request.form and 'job_experience' in request.form and \
            'job_soft_skills' in request.form and 'job_tech_skills' in request.form and \
            'job_qualification' in request.form and 'job_certification' in request.form and \
            'job_language' in request.form and 'job_responsibilities' in request.form and \
            'job_validity' in request.form:
        data = dict()
        gender = []
        # reading the data from request input
        data['job_title'] = request.form['job_title']
        data['job_location'] = request.form['job_location']
        data['job_type'] = request.form['job_type']
        data['job_duration'] = request.form['job_duration']
        # Joining salary range as per min and max value
        data['job_salary_range'] = request.form['job_salary_min'] + '-' + request.form['job_salary_max']
        # Appending all the gender eligible for job opening
        if 'male' in request.form:
            gender.append('male')
        if 'female' in request.form:
            gender.append('female')
        if 'transgender' in request.form:
            gender.append('transgender')
        if 'not_applicable' in request.form:
            gender.append('na')
        data['job_gender'] = ', '.join(gender)
        # Collecting all information from request
        data['job_conditions'] = request.form['job_conditions']
        data['job_summary'] = request.form['job_summary']
        data['job_experience'] = request.form['job_experience']
        data['job_responsibilities'] = request.form['job_responsibilities']
        data['job_soft_skills'] = request.form['job_soft_skills'].split(',')
        data['job_tech_skills'] = request.form['job_tech_skills'].split(',')
        data['job_qualification'] = request.form['job_qualification']
        data['job_certification'] = request.form['job_certification']
        data['job_validity'] = request.form['job_validity']
        data['job_language'] = request.form['job_language']
        data['employer_email'] = session['email']
        # Default value of job id will be the mongodb object id of the document
        data['job_id'] = ''
        # Inserting new data as it is a new job addition
        x = client.project.job_description.insert_one(data)
        print(x)
        if x.inserted_id:
            # Updating job id with object id of document
            client.project.job_description.update_one({'_id': x.inserted_id}, {"$set": {'job_id': str(x.inserted_id)}})
            msg = "Job Added Successfully"
        else:
            msg = "Some problem happened, please try later"
    return render_template('create_job.html', msg=msg, user_name=session['email'])


# Default page for edit job
@app.route('/edit_job/<job_id>', methods=['POST', 'GET'])
def edit_job(job_id):
    msg = ''
    # Checking method is post and all field are filled
    if request.method == 'POST' and 'job_title' in request.form and \
            'job_location' in request.form and 'job_type' in request.form and \
            'job_duration' in request.form and 'job_salary_min' in request.form and \
            'job_salary_max' in request.form and 'job_conditions' in request.form and \
            'job_summary' in request.form and 'job_experience' in request.form and \
            'job_soft_skills' in request.form and 'job_tech_skills' in request.form and \
            'job_qualification' in request.form and 'job_certification' in request.form and \
            'job_language' in request.form and 'job_responsibilities' in request.form and \
            'job_validity' in request.form:
        print(request.form)
        data = dict()
        # Collecting data from request and filing in data variable
        gender = []
        data['job_id'] = job_id
        data['job_title'] = request.form['job_title']
        data['job_location'] = request.form['job_location']
        data['job_type'] = request.form['job_type']
        data['job_duration'] = request.form['job_duration']
        # Combining job salary range
        data['job_salary_range'] = request.form['job_salary_min'] + '-' + request.form['job_salary_max']
        # Appending all variables selected
        if 'male' in request.form:
            gender.append('male')
        if 'female' in request.form:
            gender.append('female')
        if 'transgender' in request.form:
            gender.append('transgender')
        if 'not_applicable' in request.form:
            gender.append('na')
        data['job_gender'] = ', '.join(gender)
        data['job_conditions'] = request.form['job_conditions']
        data['job_summary'] = request.form['job_summary']
        data['job_experience'] = request.form['job_experience']
        data['job_responsibilities'] = request.form['job_responsibilities']
        data['job_soft_skills'] = request.form['job_soft_skills'].split(',')
        data['job_tech_skills'] = request.form['job_tech_skills'].split(',')
        data['job_qualification'] = request.form['job_qualification']
        data['job_certification'] = request.form['job_certification']
        data['job_validity'] = request.form['job_validity']
        data['job_language'] = request.form['job_language']
        data['employer_email'] = session['email']
        # Updating the data fields in the collection job description
        job = client.project.job_description.update_one({'job_id': job_id}, {"$set": data})
        if job:
            msg = f"Job Details Has Been Updated For Job id : {job_id}"
            # Fetching salary and skills in list instead of string
            data['min_salary'], data['max_salary'] = data['job_salary_range'].split('-')
            data['job_soft_skills'] = request.form['job_soft_skills']
            data['job_tech_skills'] = request.form['job_tech_skills']
            return render_template('edit_job.html', msg=msg, user_name=session['email'], data=data)
        else:
            msg = "Some problem happened, please try later"
    else:
        # if the method type is get, find the data and show it back on webpage
        data = client.project.job_description.find_one({'job_id': job_id, 'employer_email': session['email']})
        print(data)
        if data:
            # Getting data in a specific manner
            data['min_salary'], data['max_salary'] = data['job_salary_range'].split('-')
            data['job_soft_skills'] = ", ".join(data['job_soft_skills'])
            data['job_tech_skills'] = ", ".join(data['job_tech_skills'])
        else:
            data = None
    return render_template('edit_job.html', msg=msg, user_name=session['email'], data=data)


# Default route for delete webpage
@app.route('/delete_job/<job_id>', methods=['GET'])
def delete_job(job_id):
    if session:
        # Delete the job based on job id provided
        client.project.job_description.delete_one({'job_id': job_id})
        return redirect('/job_page')
    else:
        return render_template('login.html')


# Default page for read job
@app.route('/read_job/<job_id>', methods=['GET'])
def read_job(job_id):
    msg = ''
    if session:
        # Check if the job exist, then return the data otherwise error message
        data = client.project.job_description.find_one({'job_id': job_id})
        if not data:
            msg = f'No data found for job id: {job_id}'
        return render_template('read_job.html', data=data, msg=msg, user_name=session['email'])
    else:
        return render_template('login.html')


# Default page for showing job added by a particular employer
@app.route('/job_page', methods=['GET'])
def job_page():
    msg = ''
    result = []
    if session:
        # Fetching the current user
        email = session['email']
        # Finding jobs list posted by the user
        data = client.project.job_description.find({'employer_email': email})
        if not data:
            msg = f'No job data available for user: {email}'
            return render_template('job_page.html', user_name=session['email'], msg=msg)
        # In case of multiple jobs posted creating a list based on job id and job summary
        for job in data:
            print(data)
            result.append([
                job['job_id'],
                job['job_summary'],
            ])
        return render_template('job_page.html', results=result, user_name=session['email'], msg=msg)
    else:
        return render_template('login.html')


# Default page for viewing candidate profile
@app.route('/candidate_profile/<email_id>', methods=['GET'])
def candidate_profile(email_id):
    msg = ''
    if session:
        # Fetching the data of candidate from different collections based on his email
        profile_data = client.project.candidate_profile.find_one({'candidate_email': email_id})
        work_data = client.project.candidate_experience.find({'candidate_email': email_id})
        education_data = client.project.candidate_education.find({'candidate_email': email_id})
        skills_data = client.project.candidate_skills.find({'candidate_email': email_id})
        work = []
        education = []
        skills = []
        # Appending data to list in case of multiple records returned for work, education and skills
        for data in work_data:
            work.append([data['work_company'], data['work_duration'], data['work_details']])
        for data in education_data:
            education.append([data['candidate_college'], data['candidate_degree'],
                              data['candidate_year'], data['candidate_marks']])
        for data in skills_data:
            skills.append(data['candidate_skill'])
        skills_data = ",".join(skills)
        # returning webpage with data variables
        return render_template('candidate_profile.html', profile_data=profile_data, msg=msg, work_data=work,
                               education_data=education, skills_data=skills_data)
    else:
        return render_template('login.html')


# Default route for change password
@app.route('/change_password', methods=['POST', 'GET'])
def change_password():
    msg = ''
    # if the request is post and all fields are present
    if request.method == 'POST' and 'old_password' in request.form and 'new_password' in request.form and \
            'confirm_password' in request.form:
        # read the three values
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        # find the existing password of the user
        user = client.project.user_data.find_one({'email': session['email'],
                                                  'password': old_password})
        # condition for old password verification
        if user:
            # condition that new password and confirm password match
            if new_password == confirm_password:
                # update the password
                search_query = {"email": session['email']}
                update_query = {"$set": {"password": new_password}}
                resp = client.project.user_data.update_one(search_query, update_query)
                if resp:
                    msg = 'Password Change Successfully !'
                else:
                    msg = 'Could not change password, please try later !'
            else:
                msg = 'New Password and confirm password do not match'
        else:
            msg = 'Incorrect Password, Cannot Change Password'
    # if the request is get, find the user type and return that change password page
    user = client.project.user_data.find_one({'email': session['email']})
    if user['user_type'] == 2:
        return render_template('change_password_recruiter.html', user_name=session['email'], msg=msg)
    else:
        return render_template('change_password_candidate.html', user_name=session['email'], msg=msg)


# Default route for job resume match
@app.route('/job_resume_match', methods=['GET'])
def job_resume_match():
    if session:
        # prepare the candidate string based on candidate email
        candidate_data = []
        result = []
        education_data = client.project.candidate_education.find({'candidate_email': session['email']})
        experience_data = client.project.candidate_skills.find({'candidate_email': session['email']})
        skills_data = client.project.candidate_experience.find({'candidate_email': session['email']})
        # Iterate, but don't add unnecessary data it will reduce accuracy
        for education in education_data:
            for key in education.keys():
                if key not in ['candidate_email', '_id', 'candidate_college']:
                    candidate_data.append(education[key])
        for experience in experience_data:
            for key in experience.keys():
                if key not in ['candidate_email', '_id', 'work_company']:
                    candidate_data.append(experience[key])
        for skill in skills_data:
            for key in skill.keys():
                if key not in ['candidate_email', '_id']:
                    candidate_data.append(skill[key])
        # Creating resume based on candidate data
        resume = " ".join(candidate_data)
        # cleaning up data based on algorithm
        cleaned_resume_word_matcher = data_cleanup(resume, 'word_matching')
        cleaned_resume_cosine = data_cleanup(resume, 'cosine_similarity')
        # print(cleaned_resume_cosine)
        # print(cleaned_resume_word_matcher)
        # find all the jobs
        job_data = client.project.job_description.find({'job_validity': 'true'})
        # Iterate all the jobs
        for job in job_data:
            job_data = []
            # Generate new data for every job
            for key in job.keys():
                if key not in ['employer_email', '_id', 'job_id', 'job_validity']:
                    # tackling keys because value is a list
                    if key in ['job_soft_skills', 'job_tech_skills']:
                        job_data.append(" ".join(job[key]))
                    else:
                        job_data.append(job[key])
            # Creating job string
            job_details = " ".join(job_data)
            # Cleanup job data
            cleaned_job_word_matcher = data_cleanup(job_details, 'word_matching')
            cleaned_job_cosine = data_cleanup(job_details, 'cosine_similarity')
            # Pass the data to both algorithm and round off result
            expected = cosine_matcher(cleaned_job_cosine, cleaned_resume_cosine)
            actual = round(matcher(cleaned_job_word_matcher, cleaned_resume_word_matcher)[0], 2)
            # accuracy = round(((1 - abs(expected - actual) / expected) * 100), 2)
            # Append result to result key
            result.append([
                job['job_id'],
                job['job_summary'],
                expected,
                actual
            ])
            # print(cleaned_job_cosine)
            # print(cleaned_job_word_matcher)
        # print(result)
        # Sort the result in descending order based on cosine similarity
        result.sort(key=lambda x: x[2], reverse=True)
        return render_template('view_jobs.html', results=result, user_name=session['email'])
    else:
        return render_template('login.html')


# Default route for view candidate for a particular job
@app.route('/view_candidates/<job_id>', methods=['GET'])
def view_candidates(job_id):
    results = []
    cleaned_job_cosine = []
    cleaned_job_word_matcher = []
    if session:
        # Fetch the details of the job based on its id
        job_data = client.project.job_description.find_one({'job_id': job_id, 'job_validity': 'true'})
        if job_data:
            # Create job string and save the data in it from job description collection
            job_status = 'Active'
            job_information = []
            for key in job_data.keys():
                if key not in ['employer_email', '_id', 'job_id', 'job_validity']:
                    if key in ['job_soft_skills', 'job_tech_skills']:
                        job_information.append(" ".join(job_data[key]))
                    else:
                        job_information.append(job_data[key])
            job_details = " ".join(job_information)
            # Cleanup the job data from clean up method based on algorithm
            cleaned_job_word_matcher = data_cleanup(job_details, 'word_matching')
            cleaned_job_cosine = data_cleanup(job_details, 'cosine_similarity')
        else:
            # if job is inactive don't consider it
            job_status = 'Inactive'
        # Find all the candidates available
        users = client.project.candidate_profile.find()
        if users:
            # Iterate through all candidate one by one
            for candidate in users:
                # Prepare candidate string for every candidate based on data collected from all their collections.
                candidate_data = []
                # Fetching education, work and skill data
                education_data = client.project.candidate_education.find(
                    {'candidate_email': candidate['candidate_email']})
                experience_data = client.project.candidate_skills.find(
                    {'candidate_email': candidate['candidate_email']})
                skills_data = client.project.candidate_experience.find(
                    {'candidate_email': candidate['candidate_email']})
                # Combining all multiple records to a list of list form
                for education in education_data:
                    for key in education.keys():
                        if key not in ['candidate_email', '_id', 'candidate_college']:
                            candidate_data.append(education[key])
                for experience in experience_data:
                    for key in experience.keys():
                        if key not in ['candidate_email', '_id', 'work_company']:
                            candidate_data.append(experience[key])
                for skill in skills_data:
                    for key in skill.keys():
                        if key not in ['candidate_email', '_id']:
                            candidate_data.append(skill[key])
                # Joining all list data in string form
                resume = " ".join(candidate_data)
                # Clean up of job data based on algorithm
                cleaned_resume_word_matcher = data_cleanup(resume, 'word_matching')
                cleaned_resume_cosine = data_cleanup(resume, 'cosine_similarity')
                # Finding cosine similarity and word matcher based on job and resume data
                expected = cosine_matcher(cleaned_job_cosine, cleaned_resume_cosine)
                actual = round(matcher(cleaned_job_word_matcher, cleaned_resume_word_matcher)[1], 2)
                # accuracy = round(100 - ((abs(expected - actual) / expected) * 100), 2)
                # Adding to result variable
                results.append([
                    candidate['candidate_name'],
                    candidate['candidate_email'],
                    expected,
                    actual
                ])
        # sorting the data in descending order based on cosine values
        results.sort(key=lambda x: x[2], reverse=True)
        # returning data in view candidate webpage
        return render_template("view_candidates.html", job_id=job_id, job_status=job_status, results=results,
                               user_name=session['email'])
    else:
        return render_template('login.html')


# Default function for job resume matching
def matcher(job, resume):
    # job_data = data_cleanup(job, 'word_matching')
    # print(job_data)
    # resume_data = data_cleanup(resume, 'word_matching')
    # match_data = job_data.intersection(resume_data)
    # Finding common words between job and resume set using intersection
    match_data = job.intersection(resume)
    # Calculating match percentage based on job reference
    job_match_percentage = (len(match_data) * 100) / len(job)
    try:
        # Calculating match percentage based on resume reference
        resume_match_percentage = (len(match_data) * 100) / len(resume)
    except Exception as e:
        print(e)
        resume_match_percentage = 0
    # job_match_percentage = (len(match_data) * 100) / len(job_data)
    # resume_match_percentage = (len(match_data) * 100) / len(resume_data)
    # returning both reference based values
    return job_match_percentage, resume_match_percentage


# Default route for cosine matching
def cosine_matcher(job, resume):
    # job_data = " ".join(data_cleanup(job, 'cosine_similarity'))
    # resume_data = " ".join(data_cleanup(resume, 'cosine_similarity'))
    # Converting string value of job and resume data
    job_data = " ".join(job)
    resume_data = " ".join(resume)
    # Creating object of counter vector class
    cv = CountVectorizer()
    # Combining both job and resume data as list elements
    text_list = [job_data, resume_data]
    # Using fit transform method to fit the values and return count matrix with matching results
    count_matrix = cv.fit_transform(text_list)
    # Below is default code to show the array and result
    # print(count_matrix.toarray())
    # print(cosine_similarity(count_matrix))
    # Converting result to percentage and returning in two decimal places
    match_percentage = cosine_similarity(count_matrix)[0][1] * 100
    return round(match_percentage, 2)


# Default function for data clean up based on resume/job
def data_cleanup(data, algorithm):
    data_profile = ''
    # removing numbers, special symbols
    for character in data:
        if character.isalpha() or character == ' ':
            data_profile += character.lower()
        elif character == '\n':
            data_profile += ' '

    # data tokenization
    data_tokenization = word_tokenize(data_profile)

    # data stop word removal
    data_without_stop_words = [word for word in data_tokenization if word not in stop_words]

    # data lemmatization
    for ind in range(len(data_without_stop_words)):
        data_without_stop_words[ind] = wordnet_lemmatizer.lemmatize(data_without_stop_words[ind])

    # data duplicate reduction
    if algorithm != 'cosine_similarity':
        data_reduced = set(data_without_stop_words)
    else:
        data_reduced = data_without_stop_words

    return data_reduced


if __name__ == '__main__':
    # Value of __name__ will always be __main__ for any module which is run independently
    # Value of __name__ will always be module name for any module which is called by any other module
    # Starting the flask server and setting debug = True to see output messages in terminal.
    app.run(debug=True)
    # expected = cosine_matcher('Liza is a bad engineer, but good at python', 'Python machine learning engineer')
    # actual1, actual2 = matcher('Liza is a bad engineer, but good at python', 'Python machine learning engineer')
    # accuracy = (actual1 / expected) * 100
    # print(f'Expected match = {expected}, Actual Match = {actual1}, accuracy = {accuracy}')
