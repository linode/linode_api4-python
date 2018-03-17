OAuth Intgration
================

Overview
--------

OAuth 2 is an open authentication protocol that describes how users can safely
grant third-party applications access to some or all of their accounts with
service providers.  Linode implements OAuth 2 with https://login.linode.com_,
allowing third-party developers worlds of possibilities when integrating with
Linode's service.  By making an OAuth application, you can allow users to
grant your app access to create, install, configure, and manage infrastructure
on their behalf.

.. note::
   If you are simply trying out the API, or if you're writing a command line
   tool that accepts a Personal Access Token, you can safely skip this guide.

The OAuth 2 workflow has three actors:

.. glossary:: 
    
   end user
      The acting user who will log in to the application.

   authentication server
      The server who authorizes logins and issues tokens.  In this case, it will
      be login.linode.com

   client application
      The application you are writing, that Linode users will login to through
      Linode's OAuth server.  You must register OAuth clients at
      cloud.linode.com or through :any:`create_oauth_client` to generate a
      client ID and client secret (used in the exchange detailed below).

The OAuth 2 exchange works as follows:

#. The end user visits the client application's website and attempt to login
   using OAuth.
#. The client application redirects the end user to the authentication server
   with the client application's client ID and requested OAuth scopes in the
   query string.
#. The end user inputs their credentials to the authorization server and
   authorizes the login.
#. The authorization server redirects the end user to the client application
   with a temporary exchange code in the query string.
#. The client application issues a request to the authentication server
   containing the exchange code and the client application's client secret.
#. The authentication server responds to the client application with a newly
   issued OAuth token.

A working example of completing an OAuth exchange using this library is
available in the example project `Install on Linode`_

.. _Install on Linode: https://github.com/linode/python-linode-api/tree/master/examples/install-on-linode

OAuth Scopes
------------

OAuth scopes define the level of access your client application has to the
accounts of users who authorize against it.  While it may be easier to always
request the broadest scopes, this is discouraged as it is more dangerous for
the end user.  The end user is presented with the requested scopes during the
authorization process and may choose to abort authorization of your application
based on the scopes requested.

OAuth scopes are represented by the :any:`OAuthScopes` class, which can be
used to construct lists of scopes to request.  OAuth scopes are divided into
"superscopes," broad categories of entities/actions that may be requested access
to, and "subscopes," the level of access requested to a particular entity class.
For example, if you are writing a frontend to manage NodeBalancers, you may
need access to create and modify NodeBalancers, and also to list Linodes (to
display more information about the individual backends).  In this hypothetical
case, you would likely want to construct your requested scopes like this::

   requested_scopes = [OAuthScopes.NodeBalancer.all, OAuthScopes.Linodes.view]

Performing an OAuth Login
-------------------------

The :any:`LinodeLoginClient` class managed all aspects of the OAuth exchange
in this library.  To create a :any:`LinodeLoginClient`, you must use your
client ID and client secret (generated on registering a client application with
Linode - see above).::

   login_client = LinodeLoginClient(my_client_id, my_client_secret)

When a user attempts to login to your application using OAuth, you must issue
a redirect to our authentication server (step 2 above).  The
:any:`LinodeLoginClient` handles most of the details of this for you, returning
the complete URL to redirect the end user to::

   def begin_oauth_login():
       """
       An example function called when a user attempts to login user OAuth.
       """
       # generate a URL to redirect the user to, requested full access to their
       # account
       redirect_to = login_client.generate_login_url(scopes=OAuthScopes.all)

       # use your web framework to redirect the user to the generated URL
       return redirect(redirect_to)

Once the user has authenticated and approved this login, they will be redirected
to the URL configured when your client application was registered.  Your web
application must accept this request, and should use it to complete the OAuth
exchange (step 5 above)::

   def oauth_redirect(code=None):
       """
       An example callback function when a user authorizes this application.

       :param code: The exchange code provided by the authentication server,
                    present in the query string of the request.
       :type code: str
       """
       token, scopes = login_client.finish_oauth(code)

       # token is a valid OAuth token that may be used to construct a
       # LinodeClient and access the API on behalf of this user.
       
Now that you have been issued a token, be sure to keep it secret and specific
to this user - it should be tied to their session if possible.
