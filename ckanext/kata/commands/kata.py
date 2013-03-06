import logging
import sys
import re
from pprint import pprint
import datetime
from datetime import timedelta

from ckan import model
from ckan.model import Group, repo, Member
from ckan.logic import get_action, ValidationError

from ckan.lib.cli import CkanCommand
import ckanext.kata.tieteet as tieteet
from ckanext.harvest.model import HarvestSource
from ckanext.kata.model import setup, KataAccessRequest
from ckanext.kata.utils import send_email

import pylons
from pylons import config, g


class Kata(CkanCommand):
    '''
    Usage:

      kata initdb
        - Creates the necessary tables in the database
      kata send_request_emails
        - Sends edit request messages
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 6
    min_args = 0

    def __init__(self,name):

        super(Kata,self).__init__(name)

    def command(self):
        global req_log
        self._load_config()
        # if a logger is created before _load_config is called it will be in
        # disabled [1] state after _load_config has been called. This happens
        # indepently whether it's a logger that is configured in the ini file
        # (e.g. kataext), a child thereof (e.g. kataext.foo) or something
        # completely disjoint (foo). So creating a logger called ckanext.kata
        # globally in this file (which is before _load_config is called) will
        # break even existing logging using name ckanext.kata in other source
        # files.  (Because loggers with the same name exist only once,
        # regardless how often getLogger is called. The same instance is
        # returned everywhere)
        #
        # [1] I didn't see a member variable disabled documented. But it
        # exists and it does what you would expect from its name.  Actually
        # documentation of function logging.config.fileConfig mentions
        # disabling existing loggers. According to the documentation disabling
        # should not affect if the loggers or their ancestors are mentioned in
        # the config file. This restriction did not seem to be true in my
        # testing, however.
        req_log = logging.getLogger('ckanext.kata.request_emails')

        if len(self.args) == 0:
            self.parser.print_usage()
            sys.exit(1)
        cmd = self.args[0]
        
        if cmd == 'initdb':
            self.initdb()
        elif cmd == 'harvest_sources':
            self.harvest_sources()
        elif cmd == 'send_request_emails':
            req_log.debug("calling send_emails")
            self.send_emails()
        else:
            print 'Command %s not recognized' % cmd

    def _load_config(self):
        super(Kata, self)._load_config()

    def initdb(self):
        kata = Group.get('KATA')
        if not kata:
            repo.new_revision()
            kata = Group(name="KATA", title="Tieteenalat")
            kata.save()
            for tiede in tieteet.tieteet:
                t = Group(description=tiede['description'],
                          name=tiede['name'],
                          title=tiede['title'])
                t.save()
                m = Member(group=kata, table_id=t.id, table_name="group")
                m.save()
        setup()

    def harvest_sources(self):
        ddi = HarvestSource(url='http://www.fsd.uta.fi/fi/aineistot/luettelo/fsd-ddi-records-uris-fi.txt',
                            type='DDI')
        ddi.save()
        oai = HarvestSource(url='http://helda.helsinki.fi/oai/request',
                            type='OAI-PMH')
        oai.save()

    def send_emails(self):
        all_reqs = model.Session.query(KataAccessRequest).all()
        req_log.debug( "access requests: {0:d}".format(len(all_reqs)))
        curdate = datetime.datetime.utcnow()
        for req in all_reqs:
            try:
                req_log.debug( "curdate {0}, created {1}".format(str(curdate),
                                                          str(req.created)))
                if (curdate - req.created) > timedelta(days=1):
                    req_log.debug("send_email")
                    send_email(req)
                else:
                    req_log.debug("delete")
                    req.delete()
            except Exception, me:
                print "Couldn't send email! Details:\n%s" % me
