import os
def load_html(name):
    '''
    Loads html as a string from the html file

    Example Usage:
    - load_html('index.html')
    - load_html('auth/login.html')
    '''
    file = open(os.path.join('html', name))
    return file.read()