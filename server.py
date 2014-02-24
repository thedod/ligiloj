import cherrypy, models, pystache

stache = pystache.Renderer(
    search_dirs='templates',file_encoding='utf-8',string_encoding='utf-8',file_extension='html')

PAGINATE_BY = 5 # Used in many places. Yes. It's ugly. I should start reading this from config.
def nextprev(count,page,paginate_by=PAGINATE_BY):
    result = {}
    page = max(1,page)
    paginate_by = max(2,paginate_by)
    if page>1:
        result['previous'] = page-1
    if page*paginate_by<count:
        result['next'] = page+1
    return result

class LigilojApp(object):
    def _make_menu(self,selected=None):
        menu = [{'code':'','name':'*','selected':True}]
        menu += list(models.Language.select().annotate(models.Link).dicts())
        if selected:
            for item in menu:
                if item['code']==selected:
                    menu[0]['selected'] = False
                    item['selected'] = True
                    return menu,item
        return menu,menu[0]
    @cherrypy.expose
    def link(self,link_id,*args,**kwargs):
        try:
            l=models.Link.get(id=link_id)
        except models.DoesNotExist:
            raise cherrypy.HTTPError(404)
        menu,active_language = self._make_menu(l.language.code)
        return stache.render(stache.load_template('item'),l,
            static_root='/assets/',
            menu=menu, active_language=active_language)
    @cherrypy.expose
    def default(self,*args,**kwargs):
        args = list(args)
        if not args or not args[-1].isdigit():
            args.append('1')
        if len(args)<2:
            args.insert(0,None)
        page = max(1,int(args[1]))
        lang = args and args[0] or None
        language = None
        if lang:
            try:
                language = models.get_language(lang)
            except:
                pass
        page_title = language and language.__unicode__() or 'Internaciaj Ligiloj'
        menu,active_item = self._make_menu(lang)
        query = models.Link().select()
        if language:
            query = query.where(models.Link.language == language)
        result = {
            'title':u'Etgar Keret - {0}'.format(page_title),
            'static_root':'/assets/',
            'lang':lang or 'en',
            'menu':menu,
            'active_language':active_item,
            'count':query.count(),
            'links':query.paginate(page,paginate_by=PAGINATE_BY).dicts()
        }
        result.update(nextprev(query.count(),page,paginate_by=PAGINATE_BY))
        return stache.render(stache.load_template('index'),result)

cherrypy.quickstart(LigilojApp(),"/","cherrypy.config")
