# -*- coding: iso-8859-15 -*-
"""Utility script to inject random mails in the instance

This is for developpers / testers only.

Add this as External Method to populate portal with sample mails:

    id: populate
    title: whatever
    module: CPSCourrier.inject_random_mails
    function: inject

"""

from Products.CMFCore.utils import getToolByName
from Products.CPSUtil.text import toAscii
from DateTime import DateTime
from copy import deepcopy
from itertools import cycle
from pprint import pformat
import transaction
from random import randint, sample, choice

EMAIL_PATTERN = "ogrisel-%s@nuxeo.com"
IN_MAILS_PER_MAILBOX = 20
OUT_MAILS_PER_MAILBOX = 20
COMMENT_PATTER = "Test comment for transition %s"

def _buid_tree():
    return  {
        'test-group-1': {
            'Title': 'Test Group 1',
            'portal_type': 'Mailbox Group',
            'subobjects': {
                'test-mailbox-1-1': {
                    'Title': 'Test Mailbox 1 1',
                    'portal_type': 'Mailbox',
                    'from': 'ogrisel-mb11@nuxeo.com',
                    'mailbox_addresses': sample(EMAILS, 3),
                    'allowed_reply_time': randint(1, 15),
                },
                'test-mailbox-1-2': {
                    'Title': 'Test Mailbox 1 2',
                    'portal_type': 'Mailbox',
                    'from': 'ogrisel-mb12@nuxeo.com',
                    'mailbox_addresses': sample(EMAILS, 3),
                    'allowed_reply_time': randint(1, 15),
                },
            },
        },
        'test-group-2': {
            'Title': 'Test Group 2',
            'portal_type': 'Mailbox Group',
            'subobjects': {
                'test-mailbox-2-1': {
                    'Title': 'Test Mailbox 2 1',
                    'portal_type': 'Mailbox',
                    'from': 'ogrisel-mb21@nuxeo.com',
                    'mailbox_addresses': sample(EMAILS, 3),
                    'allowed_reply_time': randint(1, 15),
                },
                'test-mailbox-2-2': {
                    'Title': 'Test Mailbox 2 2',
                    'portal_type': 'Mailbox',
                    'from': 'ogrisel-mb22@nuxeo.com',
                    'mailbox_addresses': sample(EMAILS, 3),
                    'allowed_reply_time': randint(1, 15),
                },
            },
        },
    }

def _random_paragrah(n=5):
    return '. '.join(SENTENCES.next() for _ in xrange(n))

def _random_text(n=3):
    return '\n\n'.join(_random_paragrah(randint(3, 6)) for _ in xrange(n))

def _make_email(name):
    email = EMAIL_PATTERN % '-'.join(toAscii(name).lower().split())
    return "%s <%s>" % (name, email)

def _populate(where, wftool):
    for i in range(IN_MAILS_PER_MAILBOX):
        mail_to = where.getContent()['from']
        info = {
            'Title': ' '.join(SENTENCES.next().split()[:5]),
            'content': _random_text(randint(1, 3)),
            'mail_from': choice(EMAILS),
            'mail_to': [mail_to],
            'deadline': DateTime() + randint(-2, 15),
        }
        id = where.computeId(info['Title'])
        wftool.invokeFactoryFor(where, 'Incoming Mail', id, **info)
        if i % 100 == 0:
            transaction.commit()


def _rec_build_tree(where, tree, wftool):
    existing_ids = set(where.objectIds())
    for id, info in tree.items():
        portal_type = info.pop('portal_type')
        subobjects = info.pop('subobjects', ())
        if id not in existing_ids:
            wftool.invokeFactoryFor(where, portal_type, id, **info)
        if subobjects:
            _rec_build_tree(where[id], subobjects, wftool)
        if portal_type == 'Mailbox':
            _populate(where[id], wftool)

def inject(self):
    wftool = getToolByName(self, 'portal_workflow')
    portal = getToolByName(self, 'portal_url').getPortalObject()
    tree = _buid_tree()
    _rec_build_tree(portal.mailboxes, deepcopy(tree), wftool)
    return "populated tree:\n%s" % pformat(tree)

#
# Data source to inject content
#

USERNAMES = (
    "Adolphe Thiers",
    "Patrice de Mac-Mahon",
    "Jules Grévy",
    "Sadi Carnot",
    "Jean Casimir-Perier",
    "Félix Faure",
    "Émile Loubet",
    "Armand Fallières",
    "Raymond Poincaré",
    "Paul Deschanel",
    "Alexandre Millerand",
    "Gaston Doumergue",
    "Paul Doumer",
    "Albert Lebrun",
)
EMAILS = [_make_email(name) for name in USERNAMES]

TEXT = """\
Aquariophilie d'eau douce

L'aquariophilie d'eau douce est réputée être la plus simple à gérer. Le bassin avec des poissons rouges en est l'exemple le plus simple et le plus connu.

Mais il existe des formes d'aquariophilie qui cherchent à reproduire le milieu naturel et qui sont beaucoup plus ardues à mettre en œuvre, notamment les reproductions en miniature du lac Malawi ou du lac Tanganyka.

Il est essentiel pour la survie des poissons que l'aquariophile maîtrise les paramètres de l'eau et le Cycle de l'azote. En effet, les déchets organiques (excréments des poissons, restes de nourriture etc.) se décomposent en produisant de l'ammoniac qui est hautement toxique pour les poissons. Cet ammoniaque est transformé en nitrites par une première famille de bactéries, mais les nitrites sont également hautement toxiques.

Les nitrites sont alors transformés en nitrates par une seconde famille de bactéries. Les nitrates ne sont pas toxiques à faible dose. Ces nitrates seront éliminés de l'aquarium lors des changements d'eau, ou bien consommés par les plantes qui s'y trouvent.

Afin que les populations de bactéries se constituent, il est indispensable d'attendre vingt à trente jours après la constitution de l'aquarium avant d'y mettre les premiers poissons. De même, il est indispensable de préserver ces populations de bactéries lors de l'entretien du bac.

Aquariophilie d'eau de mer

Celle-ci est réputée être plus difficile, et surtout réclame un matériel plus imposant. L'espèce la plus souvent montrée et reproduite en aquarium d'eau de mer est le poisson clown avec son anémone que l'on peut voir notamment dans le dessin animé de Walt Disney Le Monde de Némo. Les aquariums marins récifaux reproduisent les écosystèmes coralliens, alors que les bacs dits fish only se consacrent exclusivement à l'hébergement des poissons.

Comment devenir aquariophile ?

L'aquariophilie est un loisir passionnant et enrichissant, et de nombreux bienfaits découlent de cette passion. En plus d'acquérir le sens de responsabilités des enfants comme les adultes, l'aquariophilie apporte des notions pluridisciplinaires (notamment telles la biologie), des études tendent à démontrer que cet hobby contribue à diminuer le stress, ce qui explique que de nombreux centres médicaux ou maisons de repos, possèdent des aquariums.

Avant de commencer cette passion, il y a cependant des précautions à prendre.

Se renseigner avant de commencer

Sous peine de faire beaucoup d'erreurs en s'y lançant à l'aveuglette... et d'abandonner par déception.

En effet l'aquariophilie peut être un hobby très coûteux, quand on est débutant. Vous pourrez aussi remarquer qu'aucun vendeur ne répondra la même chose à la même question (ou presque). Certains sont sérieux, mais ils sont bien difficiles à distinguer des autres, au début.

Si vous avez besoin de conseils, reportez vous surtout aux livres, et aux forums de discussion aquariophiles, où les gens vous aideront à bien débuter. Petit à petit vous saurez sur quels matériels il vaut mieux mettre le prix, et sur quels autres vous pouvez faire bien des économies.

Quels poissons ?

L'aquariophilie d'eau de mer : elle nécessite des connaissances particulières, un gros investissement, et forcément un gros aquarium. Néanmoins les poissons d'eau douce sont eux aussi très beaux, et vous pourrez passer de longues heures à les regarder béatement.

Il faut bien choisir la population de poissons que vous voulez avoir : ils ont tous des besoins variés qu'il est important de respecter pour leur bonne santé. Il faut aussi veiller à associer des poissons compatibles entre eux : par exemple il vaudra mieux éviter de mettre ensemble des Archocentrus nigrofasciatus (couramment appelés nigros), qui sont des poissons très territoriaux et relativement agressifs, ou des oscars, avec de petits et calmes guppys (Poecilia reticulata) : ils ne feraient pas long feu avec les premiers.

Il faut aussi choisir la taille de l'aquarium en fonction des poissons que vous allez mettre dedans : il est d'usage de compter qu'un litre d'eau est nécessaire par cm de poisson à l'âge adulte (ce qui veut dire qu'un guppy adulte a besoin de 4 litres qui lui soient dédiés pour vivre, par exemple. Cependant, cela ne veut pas dire qu'on peut maintenir un guppy dans un volume de 4l - 60litres est un minimum pour la maintenance de ce poisson). Mais il faut aussi respecter leurs besoins « sociaux » : certains poissons vivent par couples, d'autres en bancs, d'autres en groupes de taille variable... Le non-respect des besoins de vos pensionnaires entraîne un stress, ce qui n'est pas vraiment visible, mais entraîne à la longue les maladies, car le poisson est affaibli. La règle du litre d'eau par cm de poisson est donc un premier repère, mais doit être adaptée aux autres besoins des poissons (pour des poissons comme les cichlidés par exemple il faut compter beaucoup plus d'eau par poisson). Une surpopulation du bac entraîne un surplus de pollution, donc plus de changements d'eau nécessaires.

Enfin, il faut veiller à mettre le poisson dans une qualité d'eau qui lui convienne. En effet selon la région où ils vivent, les poissons sont adaptés à vivre dans une eau dont les paramètres sont bien précis : pH, dureté... Vous avez ensuite le choix de vous servir de l'eau du robinet, ou de l'eau osmosée (une eau purifiée très peu minéralisée). L'eau osmosée s'achète en animalerie, ou se fabrique par osmoseur ; c'est donc un coût de plus : réfléchissez-y tout de suite. Vous pouvez aussi bien avoir des poissons en eau du robinet ; dans ce cas il vaut mieux tester d'abord son eau, pour savoir quels poissons s'y trouveront bien.

Les poissons d'eau douce vendus dans le commerce sont pour la plupart tropicaux : il va donc aussi leur falloir un combiné chauffant... toujours à associer à un thermomètre car leur régulation n'est pas toujours très fiable.

Si vous voulez rester en eau froide, il y a toutes sortes de poissons rouges : ils peuvent aussi être très beaux dans un aquarium planté, plutôt que dans une boule.

Il va donc falloir faire le point sur ce que vous pouvez fournir à vos futurs pensionnaires, puis les sélectionner selon ces paramètres. En général on commence par faire l'inverse, et... ça se passe mal !"""

PARAGRAPHS = TEXT.split('\n\n')
SENTENCES = []
for p in PARAGRAPHS:
    SENTENCES += p.split('. ')
SENTENCES = cycle(SENTENCES)
# source: http://fr.wikipedia.org/wiki/Aquariophilie

