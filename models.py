from peewee import *
from wtfpeewee.orm import model_form
import json,datetime

import logging
logger = logging.getLogger('peewee')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

from appdir import APPDIR
db = SqliteDatabase('{0}/db/ligiloj.db'.format(APPDIR), threadlocals=True)

class BaseModel(Model):
    class Meta:
        database = db

class Language(BaseModel):
    code = CharField(verbose_name='Kodo',primary_key=True)
    is_rtl = BooleanField(default=False,verbose_name='RTL')
    name = CharField(verbose_name='Loka nomo',default='???')
    english_name = CharField(verbose_name='Angla nomo',default='???')
    class Meta:
        indexes = (
            (('name',),True),
            (('english_name',),True),
        )
        order_by = ('code',)
    def __unicode__(self):
        if self.name == self.english_name: # Happens in English ;)
            return u"{0}: {1}".format(self.code,self.name)
        return u"{0}: {1} ({2})".format(self.code,self.name,self.english_name)

class Link(BaseModel):
    language = ForeignKeyField(Language, related_name='links',verbose_name='Lingvo')
    published = DateField(verbose_name='Dato')
    url = CharField(verbose_name='URL')
    title = CharField(verbose_name='Titolo')
    class Meta:
        indexes = (
            (('url',),True),
            (('language',),False),
        )
        order_by = ('-published','language','title')
    def __unicode__(self):
        return u"{0}@{1}: {2}".format(self.language.code,self.published,self.url)

### Forms

LanguageForm = model_form(Language)
LinkForm = model_form(Link)

### Access functions
def get_language(code):
    try:
        return Language.get(Language.code==code)
    except:
        return None

### One-time db initialization
@db.commit_on_success
def _db_init_language(filename='metadata/languages.json'):
    "create language table and import data from JSON"
    db.create_table(Language)
    j=json.load(file(filename))
    for l in j['languages']:
        code,name,english_name,is_rtl = (
            l['code'],
            l['name'].split(',')[0],
            l['english_name'].split(';')[0],
            l.get('is_rtl',False))
        l = Language.get_or_create(code=code)
        l.name = name
        l.english_name = english_name
        l.is_rtl = is_rtl
        l.save()
        logger.info(u'saving {0},{1}'.format(l,l.is_rtl))

@db.commit_on_success
def _db_init_link():
    "create link table"
    db.create_table(Link)

@db.commit_on_success
def db_init_all():
    "Run once on an empty database"
    db.drop_table(Link,cascade=False,fail_silently=True)
    db.drop_table(Language,cascade=False,fail_silently=True)
    _db_init_language()
    _db_init_link()

if __name__=='__main__':
    if raw_input('Really initialize the database? (y/n) ')[0].lower()=='y':
        db_init_all()
