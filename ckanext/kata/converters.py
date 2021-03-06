import utils
import logging
from pylons.i18n import gettext as _

from ckan.logic.action.create import related_create
from ckan.model import Related, Session, Group, repo
from ckan.lib.navl.validators import not_empty

log = logging.getLogger('ckanext.kata.converters')


def pid_from_extras(key, data, errors, context):
    for k in data.keys():
        if k[0] == 'extras' and k[-1] == 'key' and data[k] == 'versionPID':
            data[('versionPID',)] = data[(k[0], k[1], 'value')]

            for _remove in data.keys():
                if _remove[0] == 'extras' and _remove[1] == k[1]:
                    del data[_remove]

    if not ('versionPID',) in data:
        data[('versionPID',)] = utils.generate_pid()


def roles_to_extras(key, data, errors, context):
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras

    extra_number = 0
    for k in data.keys():
        if k[0] == 'extras' and k[-1] == 'key':
            extra_number = max(extra_number, k[1] + 1)

    role_number = 0
    for k in data.keys():
        try:
            if k[0] == 'role' and k[-1] == 'key' and (k[0], k[1], 'value') in data \
                and len(data[(k[0], k[1], 'value')]) > 0:

                _keyval = data[('role', k[1], 'key')]
                _valval = data[('role', k[1], 'value')]

                extras.append({'key': 'role_%d_%s' % (role_number, _keyval),
                               'value': _valval})

                for _del in data.keys():
                    if _del[0] == 'role' and _del[1] == k[1] and k in data:
                        del data[k]

                role_number += 1
        except:
            pass


def roles_from_extras(key, data, errors, context):
    if not ('roles',) in data:
        data[('roles',)] = []
    roles = data[('roles',)]

    for k in data.keys():
        if k[0] == 'extras' and k[-1] == 'key':
            if 'role_' in data[k]:
                role = {}
                role['key'] = data[k]
                role['value'] = data[(k[0], k[1], 'value')]
                roles.append(role)

                if context.get('for_edit', False):
                    del data[k]
                    del data[(k[0], k[1], 'value')]


def custom_to_extras(key, data, errors, context):
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras
    for k in data.keys():
        try:
            if k[0] == 'extras' and k[-1] == 'key' and (k[0], k[1], 'value') in data:
                if type(data[(k[0], k[1], 'key')]) == unicode \
                    and len(data[(k[0], k[1], 'key')]) > 0 \
                    and type(data[(k[0], k[1], 'value')]) == unicode \
                    and len(data[(k[0], k[1], 'value')]) > 0:
                    extras.append({'key': data[(k[0], k[1], 'key')],
                               'value': data[(k[0], k[1], 'value')]})
                for _del in data.keys():
                    if len(_del) == 3 and _del[0] == 'extras' and _del[1] == k[1]:
                        del data[_del]
        except:
            pass


def org_auth_to_extras(key, data, errors, context):
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras
    if len(data[key]) > 0:
        if key[0] == 'author':
            if not ('organization', key[1], key[2]) in data:
                errors[key].append(_('This author is without organization!'))
        if key[0] == 'organization':
            if not ('author', key[1], key[2]) in data:
                errors[key].append(_('This organization is without author!'))
        extras.append({'key': "%s_%s" % (key[0], key[1]),
                  'value': data[key]})


def org_auth_from_extras(key, data, errors, context):
    if not ('orgauths',) in data:
        data[('orgauths',)] = []
    auths = []
    orgs = []
    orgauths = data[('orgauths',)]
    for k in data.keys():
        if k[0] == 'extras' and k[-1] == 'key':
            if 'author_' in data[k]:
                val = data[(k[0], k[1], 'value')]
                auth = {}
                auth['key'] = data[k]
                auth['value'] = val
                if not {'key': data[k], 'value': val} in auths:
                    auths.append(auth)

            if 'organization_' in data[k]:
                org = {}
                val = data[(k[0], k[1], 'value')]
                org['key'] = data[k]
                org['value'] = val
                if not {'key': data[k], 'value': val} in orgs:
                    orgs.append(org)

    orgs = sorted(orgs, key=lambda ke: int(ke['key'][-1]))
    auths = sorted(auths, key=lambda ke: int(ke['key'][-1]))
    zipped = zip(orgs, auths)
    if zipped:
        for org, auth in zipped:
            if not (auth, org) in orgauths:
                orgauths.append((auth, org))
    else:
        for org in orgs:
            if not ("", org) in orgauths:
                orgauths.append(("", org))
        for auth in auths:
            if not (auth, "") in orgauths:
                orgauths.append((auth, ""))


def ltitle_to_extras(key, data, errors, context):
    extras = data.get(('extras',), [])
    langs = []
    if not extras:
        data[('extras',)] = extras
    if len(data[key]) > 0:
        lval = data[(key[0], key[1], 'lang')]
        if not lval in langs:
            langs.append(lval)
        else:
            if not _("Duplicate language found.") in errors[key]:
                errors[key].append(_("Duplicate language found."))
        extras.append({'key': "title_%s" % key[1],
                      'value': data[key]})
        extras.append({'key': 'lang_title_%s' % key[1],
                       'value': lval
                       })

    if key[1] == 0 and len(data[key]) == 0 and not (key[0], key[1] + 1, 'value') in data:
        errors[key].append(_('Add at least one non-empty title!'))


def ltitle_from_extras(key, data, errors, context):
    if not ('langtitles',) in data:
        data[('langtitles',)] = []
    auths = []
    orgs = []
    orgauths = data[('langtitles',)]
    for k in data.keys():
        if k[0] == 'extras' and k[-1] == 'key':
            if data[k].startswith(('title_', 'ltitle')):
                val = data[(k[0], k[1], 'value')]
                auth = {}
                auth['key'] = data[k]
                auth['value'] = val
                if not {'key': data[k], 'value': val} in auths:
                    auths.append(auth)

            if data[k].startswith(('lsel', 'lang_title_')):
                org = {}
                val = data[(k[0], k[1], 'value')]
                org['key'] = data[k]
                org['value'] = val
                if not {'key': data[k], 'value': val} in orgs:
                    orgs.append(org)
    orgs = sorted(orgs, key=lambda ke: int(ke['key'][-1]))
    auths = sorted(auths, key=lambda ke: int(ke['key'][-1]))
    for org, auth in zip(orgs, auths):
        if not (auth, org) in orgauths:
            orgauths.append((auth, org))


def event_to_extras(key, data, errors, context):
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras
    typenum = 1
    whonum = 1
    whennum = 1
    descrnum = 1
    for k in data.keys():
        try:
            if k[0] == 'evtype' \
            and (k[0], k[1], 'value') in data \
            and len(data[(k[0], k[1], 'value')]) > 0 \
            and type(data[(k[0], k[1], 'value')]) == unicode:
                extras.append({'key': "%s_%d" % (k[0], typenum),
                               'value': data[(k[0], k[1], 'value')]
                            })
                typenum += 1
            if k[0] == 'evwho' \
            and (k[0], k[1], 'value') in data \
            and len(data[(k[0], k[1], 'value')]) > 0 \
            and type(data[(k[0], k[1], 'value')]) == unicode:
                extras.append({'key': "%s_%d" % (k[0], whonum),
                               'value': data[(k[0], k[1], 'value')]
                            })
                whonum += 1
            if k[0] == 'evwhen' \
            and (k[0], k[1], 'value') in data \
            and len(data[(k[0], k[1], 'value')]) > 0 \
            and type(data[(k[0], k[1], 'value')]) == unicode:
                extras.append({'key': "%s_%d" % (k[0], whennum),
                               'value': data[(k[0], k[1], 'value')]
                            })
                whennum += 1
            if k[0] == 'evdescr' \
            and (k[0], k[1], 'value') in data \
            and len(data[(k[0], k[1], 'value')]) > 0 \
            and type(data[(k[0], k[1], 'value')]) == unicode:
                extras.append({'key': "%s_%d" % (k[0], descrnum),
                               'value': data[(k[0], k[1], 'value')]
                            })
                descrnum += 1
        except:
            pass


def event_from_extras(key, data, errors, context):
    if not ('events',) in data:
        data[('events',)] = []
    types = []
    whos = []
    whens = []
    descrs = []
    events = data[('events',)]

    for k in data.keys():
        if k[0] == 'extras' and k[-1] == 'key':
            if 'evtype' in data[k]:
                val = data[(k[0], k[1], 'value')]
                type = {}
                type['key'] = data[k]
                type['value'] = val
                if not {'key': data[k], 'value': val} in types:
                    types.append(type)
            if 'evwho' in data[k]:
                val = data[(k[0], k[1], 'value')]
                who = {}
                who['key'] = data[k]
                who['value'] = val
                if not {'key': data[k], 'value': val} in whos:
                    whos.append(who)
            if 'evwhen' in data[k]:
                val = data[(k[0], k[1], 'value')]
                when = {}
                when['key'] = data[k]
                when['value'] = val
                if not {'key': data[k], 'value': val} in whens:
                    whens.append(when)
            if 'evdescr' in data[k]:
                val = data[(k[0], k[1], 'value')]
                descr = {}
                descr['key'] = data[k]
                descr['value'] = val
                if not {'key': data[k], 'value': val} in descrs:
                    descrs.append(descr)

    types = sorted(types, key=lambda ke: int(ke['key'][-1]))
    whos = sorted(whos, key=lambda ke: int(ke['key'][-1]))
    whens = sorted(whens, key=lambda ke: int(ke['key'][-1]))
    descrs = sorted(descrs, key=lambda ke: int(ke['key'][-1]))

    for etype, ewho, ewhen, edescr in zip(types, whos, whens, descrs):
        if not (etype, ewho, ewhen, edescr) in events:
            events.append((etype, ewho, ewhen, edescr))


def copy_from_titles(key, data, errors, context):
    for k in data.keys():
        try:
            if k[0] == 'extras' and k[-1] == 'key':
                if 'ltitle' in data[k] and not data[key]:
                    data[key] = data[(k[0], k[1], 'value')]
                    break
        except:
            pass


def export_as_related(key, data, errors, context):
    if 'id' in data[('__extras',)]:
        for value in data[key].split(';'):
            if value != '':
                if len(Session.query(Related).filter(Related.title == value).all()) == 0:
                    data_dict = {'title': value,
                                 'type': _("Paper"),
                                 'dataset_id': data[('__extras',)]['id']}
                    related_create(context, data_dict)


def add_to_group(key, data, errors, context):
    val = data.get(key)
    if val:
        repo.new_revision()
        grp = Group.get(val)
        grp.add_package_by_name(data[('name',)])
        grp.save()
