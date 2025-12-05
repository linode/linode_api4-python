import re
from flask import Flask, redirect, request, render_template, session, send_from_directory
from linode_api4 import (LinodeClient, LinodeLoginClient, StackScript, Image, Region,
                         Type, OAuthScopes)
import config

# define our flask app
app=Flask(__name__)
app.config['SECRET_KEY'] = config.secret_key


def get_login_client():
    """
    Returns a LinodeLoginClient configured as per the config module in this
    example project.
    """
    return LinodeLoginClient(config.client_id, config.client_secret)


@app.route('/')
def index():
    """
    This route renders the main page, where users land when visiting the example
    site normally.  This will present a simple form to deploy a Linode and allow
    them to submit the forum.
    """
    client = LinodeClient('no-token')
    types = client.linode.types(Type.label.contains("Linode"))
    regions = client.regions()
    stackscript = StackScript(client, config.stackscript_id)
    return render_template('configure.html',  
        types=types,
        regions=regions,
        application_name=config.application_name,
        stackscript=stackscript
    )


@app.route('/', methods=["POST"])
def start_auth():
    """
    This route is called when the forum rendered by GET / is submitted.  This
    will store the selections in the Flaks session before redirecting to
    login.linode.com to log into configured OAuth Client.
    """
    login_client = get_login_client()
    session['dc'] = request.form['region']
    session['distro'] = request.form['distribution']
    session['type'] = request.form['type']
    return redirect(login_client.generate_login_url(scopes=OAuthScopes.Linodes.read_write))


@app.route('/auth_callback')
def auth_callback():
    """
    This route is where users who log in to our OAuth Client will be redirected
    from login.linode.com; it is responsible for completing the OAuth Workflow
    using the Exchange Code provided by the login server, and then proceeding with
    application logic.
    """
    # complete the OAuth flow by exchanging the Exchange Code we were given
    # with login.linode.com to get a working OAuth Token that we can use to
    # make requests on the user's behalf.
    code = request.args.get('code')
    login_client = get_login_client()
    token, scopes, _, _ = login_client.finish_oauth(code)

    # ensure we were granted sufficient scopes - this is a best practice, but
    # at present users cannot elect to give us lower scopes than what we requested.
    # In the future they may be allowed to grant partial access.
    if not OAuthScopes.Linodes.read_write in scopes:
        return render_template('error.html', error='Insufficient scopes granted to deploy {}'\
                .format(config.application_name))

    # application logic - create the linode
    (linode, password) = make_instance(token, session['type'], session['dc'], session['distro'])

    # expire the OAuth Token we were given, effectively logging the user out of
    # of our application.  While this isn't strictly required, it's a good
    # practice when the user is done (normally when clicking "log out")
    get_login_client().expire_token(token)
    return render_template('success.html',
        password=password,
        linode=linode,
        application_name=config.application_name
    )


def make_instance(token, type_id, region_id, distribution_id):
    """
    A helper function to create a Linode with the selected fields.
    """
    client = LinodeClient('{}'.format(token))
    stackscript = StackScript(client, config.stackscript_id)
    (linode, password) = client.linode.instance_create(type_id, region_id,
            group=config.application_name,
            image=distribution_id, stackscript=stackscript.id)
    
    if not linode:
        raise RuntimeError("it didn't work")
    return linode, password


# This actually starts the application when app.py is run
if __name__ == '__main__':
    app.debug=True
    app.run()
