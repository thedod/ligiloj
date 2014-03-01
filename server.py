# -*- coding: utf-8 -*-
import cherrypy, lg_authority, models, pystache, random, datetime, time
from PyRSS2Gen import RSS2, RSSItem, Guid
from cStringIO import StringIO
from appdir import APPDIR

stache = pystache.Renderer(
    search_dirs='{0}/templates'.format(APPDIR),file_encoding='utf-8',string_encoding='utf-8',file_extension='html')

### GUI helper functions
def make_csrf_token():
    """Retuns a new csrf token.
Also keeps it in a limited pool (throws away least recently used tokens if needed)."""
    token = random._urandom(42).encode('base-64').strip()
    tokens = cherrypy.session.get('csrf_tokens',[])[-23:] # drop least recently used
    tokens.append(token)
    cherrypy.session['csrf_tokens'] = tokens
    return token

def check_csrf_token(token):
    """Checks if a csrf token is in the pool.
If found, it is also removed from the pool (avoid replay attacks)."""
    tokens = cherrypy.session.get('csrf_tokens',[])
    try:
        tokens.remove(token)
    except ValueError:
        return False
    cherrypy.session['csrf_tokens'] = tokens
    return True
    
def nextprev(count,page,paginate_by):
    """Rerturns a dict that *may* contain (depending on count,page,pageinate_by):
    * 'next':next_page_nuber
    * 'previous':previous_page_number"""
    result = {}
    page = max(1,page)
    paginate_by = max(2,paginate_by)
    if (page-1)*paginate_by>count: # let's not create work for spiders ;)
        return {}
    if page>1:
        result['previous'] = page-1
    if page*paginate_by<count:
        result['next'] = page+1
    return result

def make_menu(selected=None):
    """
Returns dicts representing a menu item for "internaciaj" and an item per each language that has links.
If selected is a language code, the dict for its tab will be [the only one] with 'selected':True
"""
    menu = [{'code':'','name':cherrypy.request.app.config['ligiloj']['global_title_html'],'selected':True}]
    menu += list(models.Language.select().annotate(models.Link).dicts()) # This "inner-joins away" languages without any links
    if selected:
        for item in menu:
            if item['code']==selected:
                menu[0]['selected'] = False
                item['selected'] = True
                return menu,item
    return menu,menu[0]

def bootstrapize_form(form):
    """Mutate a WTform to fit the whims of bootsrap""" # Reminds me of Uzi's rabi joke
    return [{'label':f.label(class_='col-sm-2 control-label'),
        'widget':f(class_='form-control'+(f.errors and ' text-danget' or '')),
        'errors':f.errors} for f in form]

class FakeMultiDict(dict):
    """Mutate a dict to fit the whims of WTForm""" # Now I'll be thinking about Uzi all day
    def getlist(self,k):
        if self.has_key(k):
            return [self[k]]
        return []

### Link editor

@lg_authority.groups('auth') # any authenticated user can access all methods
class LigilojLink(object):
    """ Link editor (at /link). Get does the reading, POST does the writing. No CRUD, No JS :) """
    exposed = True
    def GET(self,link_id=None,page=1,success=False,csrf_error=False,create=False,cl='en',ct='?',cp=None,cu='http://',*args,**kwargs):
        """Can display 3 kinds of pages (depending on args):
1) If link_id is supplied (url was /link/<n>), shows the link's edit form
2) If create is not False, shows a create form with values from cl,ct,cp,cu
3) Otherwise, shows "editor view" of all links (with edit button per link, and a create button)
"""
        conf = cherrypy.request.app.config['ligiloj']
        try:
            page = max(int(page),1)
        except:
            raise cherrypy.HTTPError(404,"nevalida paĝo nombro :(")
        if not link_id and not create:
            #--- 3rd option: show a list of all links
            query = models.Link().select(models.Link,models.Language,models.Link.id).join(models.Language)
            result = {
                #'debug':[cherrypy.request.script_name,cherrypy.request.path_info],
                'user':cherrypy.serving.user.name,
                'title':'Ligilo Redaktilon',
                'url_base':cherrypy.request.base,
                'site_root':cherrypy.request.base+cherrypy.request.script_name+'/',
                'here':cherrypy.request.base+cherrypy.request.script_name+cherrypy.request.path_info+'/',
                'success':success,
                'links':query.paginate(page,cherrypy.request.config['paginate_by']).dicts()
            }
            result.update(nextprev(query.count(),page,cherrypy.request.config['paginate_by']))
            return stache.render(stache.load_template('edit_links'),result)
        elif create:
            #--- 2nd option: show a creation form
            try: # I'm sure there's a simpler way :)
                cp = datetime.date.fromtimestamp(time.mktime(time.strptime(cp,'%Y-%m-%d')))
            except:
                cp = datetime.date.today()
            l = models.Link(
                published=cp, title=ct, url=cu,
                language=models.get_language(cl) or models.get_language('eo'))
            title = u'Aldoni ligilo'
            fancy_title =u'<i class="glyphicon glyphicon-plus"></i> Aldoni ligilo'
        else:
            #--- 1st option: show edit form for an existing link
            try: # get link to edit
                l = models.Link.get(id=link_id)
            except ValueError,models.DoesNotExist:
                raise cherrypy.HTTPError(404,"Ligilo ne estas trovita :(")
            title = u'Redaktado ligilo: {0}'.format(l.__unicode__())
            fancy_title =u'<i class="glyphicon glyphicon-edit"></i> Redaktado ligilo'
        return stache.render(stache.load_template('edit_link'),l,
            user=cherrypy.serving.user.name,
            create=create,
            csrf_error=csrf_error,
            site_title=conf['site_title'],
            title=title,
            fancy_title=fancy_title,
            site_root=cherrypy.request.base+cherrypy.request.script_name+'/',
            here=cherrypy.request.base+cherrypy.request.script_name+cherrypy.request.path_info+'/',
            csrf_token=make_csrf_token(),
            form=bootstrapize_form(models.LinkForm(obj=l)))
    def POST(self,link_id=None,srsly_delete=False,*args,**kwargs):
        """Try to update the Link at link_id (or create one if it's None).
If srsly_delete, will [SRSLY] delete the link"""
        conf = cherrypy.request.app.config['ligiloj']
        if not check_csrf_token(cherrypy.request.params.get('csrf_token','')):
            raise cherrypy.HTTPRedirect('?csrf_error=Vera',303)
        here = cherrypy.request.base+cherrypy.request.script_name+cherrypy.request.path_info+'/'
        if link_id: # edit existing link
            try: # get link to save
                l=models.Link.get(id=link_id)
            except ValueError,models.DoesNotExist:
                raise cherrypy.HTTPError(404,"Ligilo ne estas trovita :(")
            if srsly_delete:
                l.delete_instance()
                raise cherrypy.HTTPRedirect('.?success=Vera',303)
            form = models.LinkForm(FakeMultiDict(cherrypy.request.body_params),obj=l)
        else: # create a new link
            l = models.Link()
            form = models.LinkForm(FakeMultiDict(cherrypy.request.params))
        if form.validate():
            form.populate_obj(l)
            l.save()
            raise cherrypy.HTTPRedirect('{0}?success=Vera'.format(link_id and '.' or ''),303)
        return stache.render(stache.load_template('edit_link'),l,
            user=cherrypy.serving.user.name,
            title=u'Redaktado ligilo: {0}'.format(l.__unicode__()), site_title=conf['site_title'],
            site_root=cherrypy.request.base+cherrypy.request.script_name+'/',
            here=here,
            csrf_token=make_csrf_token(),
            form=bootstrapize_form(form))

class LigilojApp(object):
    """The end user app at /[language/][page]"""
    auth = lg_authority.AuthRoot()
    @cherrypy.expose
    @lg_authority.groups('auth') # any authenticated user
    def login(self,*args,**kargs):
        """Just a dummy mountpoint that requires auth."""
        raise cherrypy.HTTPRedirect(cherrypy.request.base+cherrypy.request.script_name+'/')
    @cherrypy.expose
    def rss(self,language=None,*args,**kwargs):
        if language:
            l = models.get_language(language)
        conf = cherrypy.request.app.config['ligiloj']
        query = models.Link().select(models.Link,models.Language).join(models.Language)
        if language:
            query = query.where(models.Link.language == l)
        cherrypy.response.headers['Content-Type'] = 'application/xml'
        return RSS2(title=u'{0} - {1}'.format(conf['site_title'],language and l.name or conf['global_title_text']),
            link=conf['rss_site_url'],
            description=conf['rss_description'],
            generator='ye-odlde-we-do-not-forget-code-poole',
            docs='http://www.aaronsw.com/weblog/000574',
            language=language or conf['rss_default_language'],
            items=[RSSItem(title=language and link.title or u"{0}: {1}".format(link.language.name,link.title),
                link=link.url,
                guid=Guid(link.url,str(link.id))) for link in query]).to_xml('utf-8')
        
    @cherrypy.expose
    def default(self,*args,**kwargs):
        """The end user method at /[language/][page]"""
        arglist = list(args)
        if not arglist or not arglist[-1].isdigit():
            arglist.append('1')
        if len(arglist)<2:
            arglist.insert(0,None)
        try:
            page = max(1,int(arglist[1]))
        except:
            raise cherrypy.HTTPError(404,"nevalida nombro :(")
        lang = arglist and arglist[0] or None
        language = None
        if lang is not None:
            language = models.get_language(lang)
            if language is None:
                raise cherrypy.HTTPError(404,"Nekonata lingvo")
        conf = cherrypy.request.app.config['ligiloj']
        page_title = language and language.__unicode__().split(':')[-1].strip() or conf['global_title_text']
        menu,active_language = make_menu(lang)
        query = models.Link().select(models.Link,models.Language).join(models.Language)
        if language:
            query = query.where(models.Link.language == language)
        try:
            user = cherrypy.serving.user and cherrypy.serving.user.name
        except:
            user = None
        result = {
            #'debug':[cherrypy.request.base,cherrypy.request.script_name,cherrypy.request.path_info],
            'user':user,
            'title':u'{0} - {1}'.format(conf['site_title'],page_title),
            'fancy_title':u'{0} <small>{1}</small>'.format(
                conf['site_title'],
                language and page_title or conf['global_title_html']),
            'site_root':cherrypy.request.base+cherrypy.request.script_name+'/',
            'lang':lang or 'en',
            'menu':menu,
            'active_language':active_language,
            'is_international':lang is None,
            'count':query.count(),
            'links':query.paginate(page,cherrypy.request.config['paginate_by']).dicts()
        }
        result.update(nextprev(query.count(),page,cherrypy.request.config['paginate_by']))
        return stache.render(stache.load_template('index'),result)

if __name__ == '__main__':
    cherrypy.config.update('{0}/cherrypy.config'.format(APPDIR))
    app = LigilojApp()
    app.link = LigilojLink()
    cherrypy.tree.mount(app,'/',config='{0}/cherrypy.config'.format(APPDIR))
    cherrypy.engine.start()
    cherrypy.engine.block()
