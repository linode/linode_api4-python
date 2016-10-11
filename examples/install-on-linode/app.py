import re
from flask import Flask, redirect, request, render_template, session, send_from_directory
from flask.ext.session import Session
from linode import LinodeClient, LinodeLoginClient, StackScript, Distribution, Datacenter
from linode import Service, OAuthScopes
import config

app=Flask(__name__)
app.config['SECRET_KEY'] = config.secret_key

def get_login_client():
    return LinodeLoginClient(config.client_id, config.client_secret, base_url=config.login_base_url)

@app.route('/')
def index():
    client = LinodeClient('no-token', base_url=config.api_base_url)
    types = client.linode.get_types(Service.label.contains("Linode"))
    datacenters = client.get_datacenters()
    stackscript = StackScript(client, config.stackscript_id)
    return render_template('configure.html',  
        types=types,
        datacenters=datacenters,
        application_name=config.application_name,
        stackscript=stackscript
    )

@app.route('/', methods=["POST"])
def start_auth():
    login_client = get_login_client()
    session['dc'] = request.form['datacenter']
    session['distro'] = request.form['distribution']
    session['type'] = request.form['type']
    return redirect(login_client.generate_login_url(scopes=OAuthScopes.Linodes.all))

@app.route('/auth_callback')
def auth_callback():
    code = request.args.get('code')
    login_client = get_login_client()
    token, scopes = login_client.finish_oauth(code)

    # ensure we have sufficient scopes
    if not OAuthScopes.Linodes.delete in scopes:
        return render_template('error.html', error='Insufficient scopes granted to deploy {}'\
                .format(config.application_name))

    (linode, password) = create_linode(token, session['type'], session['dc'], session['distro'])

    get_login_client().expire_token(token)
    return render_template('success.html',
        password=password,
        linode=linode,
        application_name=config.application_name
    )

def create_linode(token, type_id, datacenter_id, distribution_id):
    client = LinodeClient('{}'.format(token), base_url=config.api_base_url)
    stackscript = StackScript(client, config.stackscript_id)
    (linode, password) = client.linode.create_instance(type_id, datacenter_id,
            group=config.application_name,
            distribution=distribution_id, stackscript=stackscript.id)
    
    if not linode:
        raise RuntimeError("it didn't work")

    linode.boot()
    return linode, password

if __name__ == '__main__':
    app.debug=True
    app.run()
