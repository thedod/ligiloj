"Ligiloj" means "links" in Esperanto. It's a simple tool to collect links in various languages
concerning a loosely-related "global community" such as:

* A global event (e.g. "buy nothing day").
* A local crisis (e.g. earthquake) where people speaking several languages are involved (tourists, border area).
* An artist who has fans worldwide (this is what Ligiloj was developed for originally :) ).

Since Ligiloj assumes admins would have to deal with items in languages they don't understand, it is deliberately dumbed-down to the minimum:

  * "Posts" don't have bodies, only titles (similar to tweets).
  * Admins can use a bookmarklet that copies the page title into a form they can manually edit [if needed] and post.

### Language barriers can be fun

In order to equally share that special "surfing while foreigner" feeling English speakers are usually deprived of,
the language of the user interface is Esperanto (It's OK. I don't understand it either ;) ).
Fear not. There are icons, and worst case you can use online translation services and deal with it like most of the world does ;)

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
