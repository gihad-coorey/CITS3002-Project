# CITS3002-Project-2023

## Project Members
- Alex Barker (23152009)
- Gihad Coorey (23091788)
- Michael Hodgson (23093691)
- Muslim Gilani (23065598)

## QuestionBank
Java using com.sun.net.httpserver

A combination of written and multi-choice questions and answers are stored in txt files only available to the QB.

Can recieve requests for
- One question
  - Gives details of the question
- Question list
  - Chooses X questions randomly from its bank
- Mark a question
  - Executes the students code, or compares the multi choice response and sends back whether it is correct, its type and the expected answer + students answer

## TestManager
Python using BaseHTTPRequestHandler

- Holds the IPs of all QBs in config.py.
- Assumes that the QB connection will be maintained after the user has logged in and started the test
- Will not allow the user to start their test 
### TM → QB Protocol - HTTP
Sends requests using GET or POST requests 
- question - GET
    - Parameters: index=int
- question-list - GET
    - Parameters: count=int
- ping - GET
    - Checks if the QB is up
- submit-question - POST
    - Sends the users code and question index as the body
    - Returns JSON including question type, correctness, student output & expected output

### Client → TM - HTTP
- Student logs in, or is automatically redirected from login page to test page if they have the cookie
- The student loads the test page - each question is loaded via HTTP calls when needed
- The student can submit questions - where the TM speaks to the QB and recieves marking back

### Vessel
Implements routes similar to Flask for readability & scalability.  
