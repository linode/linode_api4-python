import re
from flask import Flask, redirect, request, render_template, session, send_from_directory
from linode_api4 import (LinodeClient, LinodeLoginClient, StackScript, Image, Region,
                         Type, OAuthScopes)
import config

app=Flask(__name__)
app.config['SECRET_KEY'] = config.secret_key

def get_login_client():
    """
    Returns a client object.

    Args:
    """
    return LinodeLoginClient(config.client_id, config.client_secret)

@app.route('/')
def index():
    """
    List all index.

    Args:
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
    Authenticate to authenticate session.

    Args:
    """
    login_client = get_login_client()
    session['dc'] = request.form['region']
    session['distro'] = request.form['distribution']
    session['type'] = request.form['type']
    return redirect(login_client.generate_login_url(scopes=OAuthScopes.Linodes.create))

@app.route('/auth_callback')
def auth_callback():
    """
    View function for oauth2 authorization.

    Args:
    """
    code = request.args.get('code')
    login_client = get_login_client()
    token, scopes, _, _ = login_client.finish_oauth(code)

    # ensure we have sufficient scopes
    if not OAuthScopes.Linodes.create in scopes:
        return render_template('error.html', error='Insufficient scopes granted to deploy {}'\
                .format(config.application_name))

    (linode, password) = make_instance(token, session['type'], session['dc'], session['distro'])

    get_login_client().expire_token(token)
    return render_template('success.html',
        password=password,
        linode=linode,
        application_name=config.application_name
    )

def make_instance(token, type_id, region_id, distribution_id):
    """
    Creates an instance of an instance.

    Args:
        token: (str): write your description
        type_id: (str): write your description
        region_id: (str): write your description
        distribution_id: (str): write your description
    """
    client = LinodeClient('{}'.format(token))
    stackscript = StackScript(client, config.stackscript_id)
    (linode, password) = client.linode.instance_create(type_id, region_id,
            group=config.application_name,
            image=distribution_id, stackscript=stackscript.id)
    
    if not linode:
        raise RuntimeError("it didn't work")
    return linode, password

if __name__ == '__main__':
    app.debug=True
    app.run()
