from peewee import *
from wtfpeewee.orm import model_form
import json,datetime

#TODO this should be conf:
db = SqliteDatabase('db/ligiloj.db', threadlocals=True)
import logging
logger = logging.getLogger('peewee')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

class BaseModel(Model):
    class Meta:
        database = db

class Language(BaseModel):
    code = CharField()
    is_rtl = BooleanField(default=False)
    name = CharField()
    english_name = CharField()
    class Meta:
        indexes = (
            (('code',),True),
            (('name',),True),
            (('english_name',),True),
        )
        order_by = ('code',)
    def __unicode__(self):
        if self.name == self.english_name: # Happens in English ;)
            return self.name
        return u"{0} ({1})".format(self.name,self.english_name)

class Link(BaseModel):
    language = ForeignKeyField(Language, related_name='links')
    published = DateTimeField(default=datetime.datetime.now)
    url = CharField()
    title = CharField()
    class Meta:
        indexes = (
            (('url',),True),
            (('language',),False),
        )
        order_by = ('-published',)
    def __unicode__(self):
        return u"{0}@{1}: {2}".format(self.language.code,self.published,self.url)

### Forms

LanguageForm = model_form(Language)
LinkForm = model_form(Link)

### Access functions
def get_language(code):
    return Language.get(Language.code==code)

### One-time db initialization
@db.commit_on_success
def _db_init_language(filename='metadata/languages.json'):
    "create language table and import data from JSON"
    db.create_table(Language)
    j=json.load(file(filename))
    for l in j['languages']:
        Language(**l).save()

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
