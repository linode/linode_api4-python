# Install on Linode

A sample application for the official [linode python library](https://github.com/linode/python-linode-api).

**Install on Linode** demonstrates a multi-user application developed with
the Linode API V4 - users arrive at a third-party application, and are asked
to authorize the application to make changes to their account, which are then
executed and reported to the user.  In this example, the third-party application
uses the `linodes:*` oauth scope to deploy a stackscript to a new linode.

### How to Use

This project is very bare-bones to keep it simple and focused on the core
concepts being demonstrated.  It relies on Flask and Flask-Login, as well
as the `linode-api` package, and does not require any external services. All
of the logic lives in app.py, with all configuration in config.py (not
included in the repository, see instructions below).

To set up:
 * Install the required packages (see requirements.txt)
 * Copy config.py.example to config.py and populate values
   * You will need to go to [login.linode.com](http://login.linode.com)
        and create a new oauth client to get your client ID and client secret - when
        registering your application, if running this locally, set the redirect uri
        to `localhost:5000/auth_callback`.
   * You will need to create a public stackscript to use for this application,
        or else pick an existing public stackscript.  You will need to take its
        stackscript ID in the linode Linode API V4 ID format: `stackscript_123` for example.
        You can run the utility script `./create_stackscript.py` to make a (blank)
        stackscript suitable for running this.
 * Run the application with `python3 app.py`

### Concepts Demonstrated

**OAuth Workflow** - This application demonstrates how to use the `LinodeLoginClient`
to authenticate a user and check the oauth scopes the user granted to your application.
Please note that in the future, users may be able to select what scopes they grant to
an application, so you should always check to make sure you are granted what your
application needs in order to run.

**Linode Creation** - This application creates a linode for the user with a specific
setup, configured in part by the user and in part by the program.  In this case, the
application will install the owner's application on the new linode and provide information
on how to access the newly-created server.

**Unauthenticated Services** - This application accesses several public endpoints of the
Linode API V4, includes `/kernels`, `/regions`, and a single public stackscript
(presumably controlled by the application's author).  The stackscript needs to be public
so that the authenticated user's account can access it in order to install it on the linode.

**Object Retreival** - This application retrieves objects from the Linode API V4 in two ways:
both as a list, and as a single requested object.  Lists are retrieved by asking the
`LinodeClient` for a list of related objects, like `client.get_regions()`, while
individual objects that we already know the ID for and will not change can be accessed by
creating a new instace of the correct type with the known ID.  For this to work, the
user whose token is being used must have access to the contstruted object.

### Disclaimer

This application is **NOT** production-ready, and is intended as an example only.  While
you might want to base your application off of it, please do not deploy this to a server
and expect it to hold up in the wild.
