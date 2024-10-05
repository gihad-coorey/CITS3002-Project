from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from user import QBConnectionError, User
from utils import letter_to_qb_url, parse_attempts
from vessel import route, load_html, redirect, WebRequest
import json
import traceback


@route("/")
@route("/index")
def index_page(request: WebRequest):
    return load_html("index.html")


@route("/login")
def login_page(request: WebRequest):
    # POST - Login button
    if request.request_type == 'POST':
        username = request.json['username']
        password = request.json['password']
        # check if user is pre-registered
        user: User = User.from_credentials(username, password)
        if not user:
            return json.dumps({'status': 'FAIL', 'message': 'Invalid username or password'})

        # initialise users questions if they need it
        if not user.initialised:
            try:
                user.initialise()
            except QBConnectionError:
                return json.dumps({'status': 'FAIL', 'message': 'Our question banks are having problems, please try again later'})

        return json.dumps({'status': 'SUCCESS'}), {'cookies': {'login': User.encode_login_cookie(username, password)}}
    # GET - Load page
    else:
        # check if user is logged in with valid credentials
        if 'login' in request.cookies:
            user = User.from_cookie(request.cookies['login'].value)
            if not user:
                 return load_html("login.html")
            # initialise if needed
            if not user.initialised:
                try:
                    user.initialise()
                    return redirect('/test')
                except QBConnectionError:
                    pass
            elif user.initialised:
                return redirect('/test')
        return load_html("login.html")


@route("/test")
def test_page(request: WebRequest):
    # not logged in
    if 'login' not in request.cookies:
        return redirect('/login')

    # invalid cookie or uninitialised user
    user = User.from_cookie(request.cookies['login'].value)
    if not user or not user.initialised:
        return redirect('/login')
    
    # if test is finished
    if user.finished:
        return load_html("results.html")
    
    return load_html("test.html")

@route("/results")
def test_page(request: WebRequest):
    # not logged in
    if 'login' not in request.cookies:
        return redirect('/login')

    # invalid cookie
    user = User.from_cookie(request.cookies['login'].value)
    if not user:
        return redirect('/login')
    
    # test not finished
    if not user.finished:
        return redirect('/test')
    
    return load_html("results.html")

@route("/api/submit-question")
def submit_question(request: WebRequest):
    # the question number in the student's test
    index = request.json['question']
    student_attempt = request.json['attempt']   # the student's attempt string

    if not isinstance(index, int):
        return 'Question must be an integer', {'code': 400}
    index = int(index) - 1
    if (index < 0 or index > 9):
        return 'Question index out of range', {'code': 400}

    if not 'login' in request.cookies:
        return 'You must be logged in to submit a question', {'code': 401}

    username, password = User.decode_login_cookie(request.cookies['login'].value)
    user = User.from_credentials(username, password)
    if not user or not user.initialised:
        return 'Invalid log in session - please re log in', {'code': 401}

    questions = user.questions
    qb_lang_code = questions[index][0]  # J, P, C
    qb_api_url = letter_to_qb_url(qb_lang_code)

    response = {'status': 'SUCCESS', 
                'message': 'Submitted question and updated user',
                'type': None, 
                'correct': None, 
                'expected_output': None, 
                'student_output': None}

    # Determine the port based on the request type
    # Send attempt to question bank API for marking
    try:
        print(f'QB: {qb_api_url} | lang: {qb_lang_code} | index {questions[index][1:]}')

        # The first word is the question number
        payload: str = str(questions[index][1:]) + " " + student_attempt
        req = Request(qb_api_url+"/api/submit-question",
                      data=payload.encode("utf-8"), method='POST')
        with urlopen(req) as http_response:
            result = http_response.read().decode("utf-8")
            response_json = json.loads(result)

            print('Recieved response from question bank: ')
            print(response_json)

            response['type'] = response_json.get("type")
            response['correct'] = response_json.get("correct")
            response['expected_output'] = response_json.get("expected_output")
            response['student_output'] = response_json.get("student_output")
    except URLError:
        print('Could not connect to ' + qb_api_url)
        return 'Error connecting to the question bank API', {'code': 500}
    except Exception:
        traceback.print_exc()

    print(response['correct'])

    attempt = user.save_answer(index, response['student_output'], response['correct'] == 'true')
    response.update(parse_attempts(attempt))

    if attempt < 3:
        response.pop('expected_output')

    # check if the user is done
    response['finished'] = user.finished
    response['score'] = user.total_score

    return json.dumps(response)


@route("/api/get-question")
def get_question(request: WebRequest):
    try:
        # check the validity of the request & users login
        if "question" not in request.query:
            return "Question parameter not included request", {'code': 400}

        if 'login' not in request.cookies:
            return json.dumps({'status': 'FAIL', 'message': 'Invalid login session'}) , {'code': 401}

        question_index = request.query['question']
        if not question_index.isdigit():
            return 'Question must be an integer', {'code': 400}
        question_index = int(question_index) - 1 
        if (question_index < 0 or question_index > 9):
            return 'Question index out of range', {'code': 400}

        user = User.from_cookie(request.cookies['login'].value)
        if not user.initialised:
            return 'User not initialised - please re-log in', {'code': 401}


        print(f'Getting question {question_index + 1} for user {user.username}')

        question = user.questions[question_index]

        qb_lang_code = question[0]
        qb_api_url = letter_to_qb_url(qb_lang_code)  # get the url of the right QB

        httpRequest = Request(
            f"{qb_api_url}/api/question?index={question[1::]}")

        out = ""
        try:
            with urlopen(httpRequest) as response:
                out = response.read().decode()
        except HTTPError as e:
            print(f'Question {question} not found in {qb_api_url}')
            return 'Question not found', {'code': 404}

        response: dict = json.loads(out)

        print(f"\tRecieved question info for {question} from {qb_api_url}: ")
        print(f'\t{response}')

        # get users current attempts
        attempt = user.attempts[question_index]
        answer = user.answers[question_index]

        response.update(parse_attempts(attempt))
        response['language'] = qb_lang_code
        response['student_output'] = answer
        response['finished'] = user.finished
        response['score'] = user.total_score

        # only send answer if user has finished
        if attempt < 3:
            response.pop('expected_output')

        return json.dumps(response)
    except:
        traceback.print_exc()
        return "An error occured", {'code': 500}

@route("/api/get-results")
def submit_question(request: WebRequest):
    # not logged in
    if 'login' not in request.cookies:
        return 'Not logged in', {'code': 401}

    # invalid cookie or uninitialised user
    user = User.from_cookie(request.cookies['login'].value)
    if not user or not user.initialised:
        return 'Invalid log in session - please re log in', {'code': 401}

    return json.dumps({'score': user.total_score, 'username':user.username}) 
    
