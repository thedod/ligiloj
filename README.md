"Ligiloj" means "links" in Esperanto.

Sometimes, there are issues of interest affecting loosely-related communities of people speaking several languages:

* A global event (e.g. "buy nothing day").
* A local crisis (e.g. earthquake) where people speaking several languages are involved (tourists, border areas).
* An artist who has fans worldwide (this is what Ligiloj was written for originally :) ).

Ligiloj assumes the admins have to deal with items in a language they don't understand:

  * "Posts" don't have bodies, only titles (similar to tweets).
  * Admins have a bookmarklet that copies the page title (and in some cases - the language) into a link form they can manually edit and post.

In order to equally share that special "surfing while foreigner" feeling English speakers are deprived of,
the language of the user interface is Esperanto (had to pick *some* language ;) ).
Fear not. There are icons, and worst case there are online translation services, so deal with it like most of the world does ;)

### Install/config:

* To install the `lg_authority` submodule: `git submodule update --init`
* To install other dependencies: `pip install -r requirements.txt`
* To create an initial `cherrypy.config`: `./makeconfig`.
* To initialize the db: `python models.py` (say `y` at the prompt).

### Run:

* `python server.py`

### Manage users:

Authentication is done via `lg_authority`. It can do a lot, but here's what it does
"out of the box":

* Go to `/login` and login as `admin/admin` (lame).
* Change password (of course).
* Create some other user. The password will be `password` (lamer)
  and admin can't change it - you have to login as that user for that (lameroo galore).

At the moment, the app ignores groups and allows all authenticated users to edit the db
(the `admin` group is significant, though: `lg_authority` allows `admin` members to manage users).
