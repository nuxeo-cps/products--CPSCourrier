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
    "Jules Gr�vy",
    "Sadi Carnot",
    "Jean Casimir-Perier",
    "F�lix Faure",
    "�mile Loubet",
    "Armand Falli�res",
    "Raymond Poincar�",
    "Paul Deschanel",
    "Alexandre Millerand",
    "Gaston Doumergue",
    "Paul Doumer",
    "Albert Lebrun",
)
EMAILS = [_make_email(name) for name in USERNAMES]

TEXT = """\
Aquariophilie d'eau douce

L'aquariophilie d'eau douce est r�put�e �tre la plus simple � g�rer. Le bassin avec des poissons rouges en est l'exemple le plus simple et le plus connu.

Mais il existe des formes d'aquariophilie qui cherchent � reproduire le milieu naturel et qui sont beaucoup plus ardues � mettre en �uvre, notamment les reproductions en miniature du lac Malawi ou du lac Tanganyka.

Il est essentiel pour la survie des poissons que l'aquariophile ma�trise les param�tres de l'eau et le Cycle de l'azote. En effet, les d�chets organiques (excr�ments des poissons, restes de nourriture etc.) se d�composent en produisant de l'ammoniac qui est hautement toxique pour les poissons. Cet ammoniaque est transform� en nitrites par une premi�re famille de bact�ries, mais les nitrites sont �galement hautement toxiques.

Les nitrites sont alors transform�s en nitrates par une seconde famille de bact�ries. Les nitrates ne sont pas toxiques � faible dose. Ces nitrates seront �limin�s de l'aquarium lors des changements d'eau, ou bien consomm�s par les plantes qui s'y trouvent.

Afin que les populations de bact�ries se constituent, il est indispensable d'attendre vingt � trente jours apr�s la constitution de l'aquarium avant d'y mettre les premiers poissons. De m�me, il est indispensable de pr�server ces populations de bact�ries lors de l'entretien du bac.

Aquariophilie d'eau de mer

Celle-ci est r�put�e �tre plus difficile, et surtout r�clame un mat�riel plus imposant. L'esp�ce la plus souvent montr�e et reproduite en aquarium d'eau de mer est le poisson clown avec son an�mone que l'on peut voir notamment dans le dessin anim� de Walt Disney Le Monde de N�mo. Les aquariums marins r�cifaux reproduisent les �cosyst�mes coralliens, alors que les bacs dits fish only se consacrent exclusivement � l'h�bergement des poissons.

Comment devenir aquariophile ?

L'aquariophilie est un loisir passionnant et enrichissant, et de nombreux bienfaits d�coulent de cette passion. En plus d'acqu�rir le sens de responsabilit�s des enfants comme les adultes, l'aquariophilie apporte des notions pluridisciplinaires (notamment telles la biologie), des �tudes tendent � d�montrer que cet hobby contribue � diminuer le stress, ce qui explique que de nombreux centres m�dicaux ou maisons de repos, poss�dent des aquariums.

Avant de commencer cette passion, il y a cependant des pr�cautions � prendre.

Se renseigner avant de commencer

Sous peine de faire beaucoup d'erreurs en s'y lan�ant � l'aveuglette... et d'abandonner par d�ception.

En effet l'aquariophilie peut �tre un hobby tr�s co�teux, quand on est d�butant. Vous pourrez aussi remarquer qu'aucun vendeur ne r�pondra la m�me chose � la m�me question (ou presque). Certains sont s�rieux, mais ils sont bien difficiles � distinguer des autres, au d�but.

Si vous avez besoin de conseils, reportez vous surtout aux livres, et aux forums de discussion aquariophiles, o� les gens vous aideront � bien d�buter. Petit � petit vous saurez sur quels mat�riels il vaut mieux mettre le prix, et sur quels autres vous pouvez faire bien des �conomies.

Quels poissons ?

L'aquariophilie d'eau de mer : elle n�cessite des connaissances particuli�res, un gros investissement, et forc�ment un gros aquarium. N�anmoins les poissons d'eau douce sont eux aussi tr�s beaux, et vous pourrez passer de longues heures � les regarder b�atement.

Il faut bien choisir la population de poissons que vous voulez avoir : ils ont tous des besoins vari�s qu'il est important de respecter pour leur bonne sant�. Il faut aussi veiller � associer des poissons compatibles entre eux : par exemple il vaudra mieux �viter de mettre ensemble des Archocentrus nigrofasciatus (couramment appel�s nigros), qui sont des poissons tr�s territoriaux et relativement agressifs, ou des oscars, avec de petits et calmes guppys (Poecilia reticulata) : ils ne feraient pas long feu avec les premiers.

Il faut aussi choisir la taille de l'aquarium en fonction des poissons que vous allez mettre dedans : il est d'usage de compter qu'un litre d'eau est n�cessaire par cm de poisson � l'�ge adulte (ce qui veut dire qu'un guppy adulte a besoin de 4 litres qui lui soient d�di�s pour vivre, par exemple. Cependant, cela ne veut pas dire qu'on peut maintenir un guppy dans un volume de 4l - 60litres est un minimum pour la maintenance de ce poisson). Mais il faut aussi respecter leurs besoins � sociaux � : certains poissons vivent par couples, d'autres en bancs, d'autres en groupes de taille variable... Le non-respect des besoins de vos pensionnaires entra�ne un stress, ce qui n'est pas vraiment visible, mais entra�ne � la longue les maladies, car le poisson est affaibli. La r�gle du litre d'eau par cm de poisson est donc un premier rep�re, mais doit �tre adapt�e aux autres besoins des poissons (pour des poissons comme les cichlid�s par exemple il faut compter beaucoup plus d'eau par poisson). Une surpopulation du bac entra�ne un surplus de pollution, donc plus de changements d'eau n�cessaires.

Enfin, il faut veiller � mettre le poisson dans une qualit� d'eau qui lui convienne. En effet selon la r�gion o� ils vivent, les poissons sont adapt�s � vivre dans une eau dont les param�tres sont bien pr�cis : pH, duret�... Vous avez ensuite le choix de vous servir de l'eau du robinet, ou de l'eau osmos�e (une eau purifi�e tr�s peu min�ralis�e). L'eau osmos�e s'ach�te en animalerie, ou se fabrique par osmoseur ; c'est donc un co�t de plus : r�fl�chissez-y tout de suite. Vous pouvez aussi bien avoir des poissons en eau du robinet ; dans ce cas il vaut mieux tester d'abord son eau, pour savoir quels poissons s'y trouveront bien.

Les poissons d'eau douce vendus dans le commerce sont pour la plupart tropicaux : il va donc aussi leur falloir un combin� chauffant... toujours � associer � un thermom�tre car leur r�gulation n'est pas toujours tr�s fiable.

Si vous voulez rester en eau froide, il y a toutes sortes de poissons rouges : ils peuvent aussi �tre tr�s beaux dans un aquarium plant�, plut�t que dans une boule.

Il va donc falloir faire le point sur ce que vous pouvez fournir � vos futurs pensionnaires, puis les s�lectionner selon ces param�tres. En g�n�ral on commence par faire l'inverse, et... �a se passe mal !"""

PARAGRAPHS = TEXT.split('\n\n')
SENTENCES = []
for p in PARAGRAPHS:
    SENTENCES += p.split('. ')
SENTENCES = cycle(SENTENCES)
# source: http://fr.wikipedia.org/wiki/Aquariophilie

