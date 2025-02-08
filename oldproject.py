import socket
import signal
import sys
import random
import datetime
import time

# Read a command line argument for the port where the server
# must run.
port = 8080
if len(sys.argv) > 1:
    port = int(sys.argv[1])
else:
    print("Using default port 8080")
hostname = socket.gethostname()

# Start a listening server socket on the port
sock = socket.socket()
sock.bind(('', port))
sock.listen(2)

### Contents of pages we will serve.
# Login form
login_form = """
   <form action = "http://%s" method = "post">
   Name: <input type = "text" name = "username">  <br/>
   Password: <input type = "text" name = "password" /> <br/>
   <input type = "submit" value = "Submit" />
   </form>
"""
# Default: Login page.
login_page = "<h1>Please login</h1>" + login_form
# Error page for bad credentials
bad_creds_page = "<h1>Bad user/pass! Try again</h1>" + login_form
# Successful logout
logout_page = "<h1>Logged out successfully</h1>" + login_form
# A part of the page that will be displayed after successful
# login or the presentation of a valid cookie
success_page = """
   <h1>Welcome!</h1>
   <form action="http://%s" method = "post">
   <input type = "hidden" name = "action" value = "logout" />
   <input type = "submit" value = "Click here to logout" />
   </form>
   <br/><br/>
   <h1>Your secret data is here:</h1>
"""

headers_to_send = ''

#### Helper functions
# Printing.
def print_value(tag, value):
    print("Here is the", tag)
    print("\"\"\"")
    print(value)
    print("\"\"\"")
    print()

# Signal handler for graceful exit
def sigint_handler(sig, frame):
    print('Finishing up by closing listening socket...')
    sock.close()
    sys.exit(0)
# Register the signal handler
signal.signal(signal.SIGINT, sigint_handler)


# TODO: put your application logic here!
# Read login credentials for all the users
# Read secret data of all the users

username_to_password = {}

with open("passwords.txt", "r") as f:
    lines = f.readlines()

    for line in lines:
        username, password = line.split()
        username_to_password[username] = password
        # print(username_to_password)     #temp

username_to_secret = {}

with open("secrets.txt", "r") as f:
    lines = f.readlines()

    for line in lines:
        username, secret = line.split()
        username_to_secret[username] = secret


### Loop to accept incoming HTTP connections and respond.
while True:
    client, addr = sock.accept()

    #receive a request from the client
    req = client.recv(1024)

    def parse_req(req):
    # Let's pick the headers and entity body apart
        header_body = req.decode().split('\r\n\r\n')
        headers = header_body[0]
        body = '' if len(header_body) == 1 else header_body[1]
        # print_value('headers', headers)
        # print_value('entity body', body)
        return headers, body

    # TODO: Put your application logic here!
    # Parse headers and body and perform various actions

    # OPTIONAL TODO:
    # Set up the port/hostname for the form's submit URL.
    # If you want POSTing to your server to
    # work even when the server and client are on different
    # machines, the form submit URL must reflect the `Host:`
    # header on the request.
    # Change the submit_hostport variable to reflect this.
    # This part is optional, and might even be fun.
    # By default, as set up below, POSTing the form will
    # always send the request to the domain name returned by
    # socket.gethostname().
    submit_hostport = "%s:%d" % (hostname, port)

    # You need to set the variables:
    # (1) `html_content_to_send` => add the HTML content you'd
    # like to send to the client.
    # Right now, we just send the default login page.
    # html_content_to_send = login_page % submit_hostport
    # But other possibilities exist, including
    # html_content_to_send = (success_page % submit_hostport) + <secret>
    # html_content_to_send = bad_creds_page % submit_hostport
    # html_content_to_send = logout_page % submit_hostport
    
        
    # parse the request into headers and body
    headers, body = parse_req(req)

    #CASE E - logout
    if "action=logout" in body:
        date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S ') + time.strftime("%Z")
        headers_to_send = 'Set-Cookie: token=' + str(rand_val) + '; expires=' + date + '\r\n'
        open('cookies.txt', 'w').close()
        html_content_to_send = logout_page % submit_hostport


    if headers_to_send:#cookie in headers:
        # validate the cookie

        with open("cookies.txt", "r") as file:
            saved_token = file.read().strip()
            valid_session = headers_to_send == "Set-Cookie: token=" + saved_token
            if saved_token and valid_session:   # CASE C - valid cookie
                if headers_to_send == saved_token:
                    html_content_to_send = success_page % submit_hostport + username_to_secret[name]
            
            
            else: # CASE D - invalid cookie
                html_content_to_send = bad_creds_page % submit_hostport
       

    if body and "action=logout" not in body: # CASE A
        names, pwd = body.split('&')    #split body into username and password
        name = names.split('=')[1]
        pwd = pwd.split('=')[1]
        print('name: {}, password: {}'.format(name, pwd))

        if name in username_to_password:# if username_to_password[word] == username:  #if the user exists in the database
            if username_to_password[name] == pwd:
                html_content_to_send = success_page % submit_hostport + username_to_secret[name]
                rand_val = random.getrandbits(64)
                headers_to_send = 'Set-Cookie: token=' + str(rand_val) + '\r\n'
                with open ('cookies.txt', 'w') as file:
                    file.write(str(rand_val))
            # CASE B
            # either username or password is absent in entity body
            # both are present but the username is not in passwords file
            # password did NOT match
            else:
                html_content_to_send = bad_creds_page % submit_hostport
        else:
            html_content_to_send = bad_creds_page % submit_hostport
    
    else:
        # if neither a valid cookie nor credentials are present
        #send a prompt for user login
        html_content_to_send = login_page % submit_hostport 

    # (2) `headers_to_send` => add any additional headers
    # you'd like to send the client?
    # Right now, we don't send any extra headers.
    # headers_to_send = ''

    # Construct and send the final response
    response  = 'HTTP/1.1 200 OK\r\n'
    response += headers_to_send
    response += 'Content-Type: text/html\r\n\r\n'
    response += html_content_to_send
    print_value('response', response)    
    client.send(response.encode())
    client.close()
    
    print("Served one request/connection!")
    print()

# We will never actually get here.
# Close the listening socket
sock.close()
