# -*- coding: iso-8859-15 -*-
"""Utility script to inject random mails in the instance

This is for developpers / testers only.

Add this as External Method to populate portal with sample mails:

    id: populate
    title: whatever
    module: CPSCourrier.inject_random_mails
    function: inject

Alternatively, you can run it like this (from INSTANCE_HOME):
bin/zopectl run Products/CPSCourrier/Extensions/inject_random_mails.py [portal_rpath]

The default portal_rpath is "cps"
"""

from Products.CMFCore.utils import getToolByName
from Products.CPSUtil.text import toAscii
from DateTime import DateTime
from copy import deepcopy
from pprint import pformat
import transaction
from random import randint, sample, choice

IN_MAILS_PER_MAILBOX = 20
OUT_MAILS_PER_MAILBOX = 20
EMAIL_PATTERN = "gracinet+%s@nuxeo.com"
COMMENT_PATTERN = "Test comment for transition %s"

def _buid_tree(gen):
    return  {
        'group-1': {
            'Title': 'Group 1',
            'portal_type': 'Mailbox Group',
            'subobjects': {
                'mailbox-1-1': {
                    'Title': 'Mailbox 1 1',
                    'portal_type': 'Mailbox',
                    'from': 'ogrisel+mb11@nuxeo.com',
                    'mailbox_addresses': gen.randomEmails(simple=True),
                    'allowed_reply_time': randint(1, 15),
                    'Subject': gen.sampleFromVoc('subject_voc'),
                },
                'mailbox-1-2': {
                    'Title': 'Mailbox 1 2',
                    'portal_type': 'Mailbox',
                    'from': 'ogrisel+mb12@nuxeo.com',
                    'mailbox_addresses': gen.randomEmails(simple=True),
                    'allowed_reply_time': randint(1, 15),
                    'Subject': gen.sampleFromVoc('subject_voc'),
                },
            },
        },
        'group-2': {
            'Title': 'Group 2',
            'portal_type': 'Mailbox Group',
            'subobjects': {
                'mailbox-2-1': {
                    'Title': 'Mailbox 2 1',
                    'portal_type': 'Mailbox',
                    'from': 'ogrisel+mb21@nuxeo.com',
                    'mailbox_addresses': gen.randomEmails(simple=True),
                    'allowed_reply_time': randint(1, 15),
                    'Subject': gen.sampleFromVoc('subject_voc'),
                },
                'mailbox-2-2': {
                    'Title': 'Mailbox 2 2',
                    'portal_type': 'Mailbox',
                    'from': 'ogrisel+mb22@nuxeo.com',
                    'mailbox_addresses': gen.randomEmails(simple=True),
                    'allowed_reply_time': randint(1, 15),
                    'Subject': gen.sampleFromVoc('subject_voc'),
                },
            },
        }
    }

def _populate(where, generator, wftool):
    for i in range(IN_MAILS_PER_MAILBOX):
        dm = where.getContent().getDataModel()
        corpus = generator.randomCorpus()
        mail_to = dm['from']
        info = {
            'Title': generator.randomWords(corpus=corpus),
            'content': generator.randomText(corpus=corpus),
            'mail_from': generator.randomEmail(),
            'mail_to': [mail_to],
            'deadline': DateTime() + randint(-2, 15),
            'Subject': generator.sampleFromVoc('subject_voc', corpus=corpus),
            'priority': generator.choiceFromVoc('mail_priority'),
        }
        dt = DateTime()
        m_id = where.portal_uid.getUid('cpscourrier', year=dt.year(),
                                       month=dt.month(), day=dt.day())
        m_id = wftool.invokeFactoryFor(where, 'Incoming Email', m_id,
                                       initial_transition='create')
        doc = where[m_id].getEditableContent()
        doc.edit(info, proxy=where[m_id])
        if i % 10 == 0:
            transaction.commit()
    # necessary with zopectl run:
    transaction.commit()

def _rec_build_tree(where, tree, generator, wftool):
    existing_ids = set(where.objectIds())
    for id, info in tree.items():
        portal_type = info.pop('portal_type')
        subobjects = info.pop('subobjects', ())
        if id not in existing_ids:
            wftool.invokeFactoryFor(where, portal_type, id, **info)
        if subobjects:
            _rec_build_tree(where[id], subobjects, generator, wftool)
        if portal_type == 'Mailbox':
            _populate(where[id], generator, wftool)

def inject(self):
    wftool = getToolByName(self, 'portal_workflow')
    portal = getToolByName(self, 'portal_url').getPortalObject()
    generator = RandomContentGenerator(portal=portal)
    tree = _buid_tree(generator)
    _rec_build_tree(portal.mailboxes, deepcopy(tree), generator, wftool)
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

A_TEXT = """\
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
# source: http://fr.wikipedia.org/wiki/Aquariophilie

G_TEXT = """\
�nonc�s des deux th�or�mes

Le premier th�or�me d'incompl�tude peut �tre �nonc� de la fa�on un peu approximative suivante.

    Dans n'importe quelle th�orie r�cursivement axiomatisable, coh�rente et capable de "formaliser l'arithm�tique", on peut construire un �nonc� arithm�tique qui ne peut �tre ni prouv� ni r�fut� dans cette th�orie.

De tels �nonc�s sont dits ind�cidables dans cette th�orie.

Toujours dans l'article de 1931, G�del en d�duit le second th�or�me d'incompl�tude :

    Si T est une th�orie coh�rente qui satisfait des hypoth�ses analogues, la coh�rence de T, qui peut s'exprimer dans la th�orie T, n'est pas d�montrable dans T.

Ces deux th�or�mes ont �t� prouv�s pour l'arithm�tique de Peano, et donc pour les th�ories plus fortes que celle-ci, en particulier les th�ories destin�es � fonder les math�matiques, telles que la th�orie des ensembles, ou les Principia Mathematica...

Les conditions d'application des th�or�mes

Pour fixer les id�es, on consid�re dor�navant que les th�ories en question sont des th�ories du premier ordre de la logique classique, m�me si les th�or�mes d'incompl�tude restent valides, sous les m�mes conditions, par exemple en logique intuitionniste ou en passant � l'ordre sup�rieur.

    * Par th�orie r�cursivement axiomatisable, on entend que la th�orie peut �tre axiomatis�e de fa�on qu'il soit possible de reconna�tre de fa�on purement m�canique les axiomes parmi les �nonc�s du langage de la th�orie. C'est le cas �videmment des th�ories utilis�es pour formaliser tout ou partie des math�matiques usuelles.
    * Une th�orie est coh�rente si aucune contradiction ne peut �tre prouv�e � partir de ses axiomes. On dit aussi qu'elle est consistante, ou non-contradictoire. Pour le premier th�or�me d'incompl�tude, G�del faisait une hypoth�se de coh�rence un peu plus forte. L'hypoth�se de coh�rence simple suffit de toute fa�on pour le second th�or�me, qui n'�nonce que la non-d�montrabilit� de l'�nonc� de coh�rence. J. B. Rosser a donn� en 1936 une d�monstration du premier th�or�me d'incompl�tude sous la simple hypoth�se de coh�rence. � proprement parler, l'�nonc� du premier th�or�me d'incompl�tude donn� au d�but de cet article n'est donc pas exactement celui de G�del. On le nomme souvent th�or�me de G�del-Rosser.
    * Une th�orie permet de formaliser l'arithm�tique si, d'une part il est possible de d�finir (en un sens qu'il faudrait pr�ciser) les entiers (donn�s par z�ro et la fonction successeur), avec les op�rations usuelles, au moins l'addition et la multiplication, et si d'autre part un certain nombre d'�nonc�s sur les entiers sont prouvables dans la th�orie. Les axiomes de Peano conviennent, mais, pour le premier th�or�me d'incompl�tude une th�orie arithm�tique beaucoup plus faible suffit (la r�currence n'est essentiellement pas utile). Pour le second il faut un minimum de r�currence.
      Il est remarquable que pour formaliser l'arithm�tique, l'addition et la multiplication suffisent (en plus de z�ro et du successeur). C'est le tout premier pas vers la solution du dixi�me probl�me de Hilbert (voir th�or�me de Matiyasevich). L'addition seule ne suffit pas : l'arithm�tique de Presburger, qui est la th�orie obtenue en restreignant l'arithm�tique de Peano au langage de l'addition (en plus de z�ro et du successeur), est compl�te.

Cons�quences imm�diates du premier th�or�me d'incompl�tude

On peut reformuler le premier th�or�me d'incompl�tude en disant que si une th�orie T satisfait les hypoth�ses utiles, il existe un �nonc� tel que chacune des deux th�ories obtenues l'une en ajoutant � T cet �nonc� comme axiome, l'autre en ajoutant la n�gation de cet �nonc�, sont coh�rentes.

�tant donn� un �nonc� G, notons non G sa n�gation. On montre facilement qu'un �nonc� G n'est pas d�montrable dans T si et seulement si la th�orie T + non G (la th�orie T � laquelle on ajoute l'axiome non G) est coh�rente. En effet, si G est d�montrable dans T, T + non G est �videmment contradictoire, et, r�ciproquement, de T + non G est contradictoire, on d�duit que G est cons�quence de T (c'est le raisonnement par l'absurde).

Il est donc �quivalent de dire qu'un �nonc� G est ind�cidable dans une th�orie coh�rente T, et de dire que les deux th�ories T + non G et T + G sont coh�rentes. L'�nonc� G n'�tant �videmment pas ind�cidable dans chacune de ces deux th�ories, on voit que la notion d'�nonc� ind�cidable est par nature relative � une th�orie donn�e.

Ainsi, si G est l'�nonc� ind�cidable donn� pour T par le premier th�or�me d'incompl�tude, on aura, en appliquant � nouveau ce th�or�me, un nouvel �nonc� ind�cidable dans la th�orie T + G (et donc d'ailleurs ind�cidable aussi dans la th�orie T).

De fait, quand le th�or�me d'incompl�tude s'applique � une th�orie T, il s'applique � toutes les extensions coh�rentes de cette th�orie, tant qu'elles restent r�cursivement axiomatisables : il n'y a aucun moyen effectif de compl�ter une telle th�orie.

Il faut �galement noter que, quelle que soit la th�orie en jeu, l'�nonc� obtenu est arithm�tique, c'est � dire qu'on peut l'exprimer dans le langage de l'arithm�tique. Il s'agit m�me d'un �nonc� de l'arithm�tique logiquement assez simple (en un sens pr�cis). Par exemple, on obtiendra par le th�or�me de G�del appliqu� � la th�orie des ensembles de Zermelo-Fraenkel un �nonc� arithm�tique mais qui sera ind�cidable dans celle-ci.

Cons�quences imm�diates du second th�or�me d'incompl�tude

Il peut �tre utile pour comprendre l'�nonc� du second th�or�me d'incompl�tude, de le reformuler par contrapos�e :

    Si T est une th�orie r�cursivement axiomatisable qui permet de formaliser "suffisamment d'arithm�tique", et si T prouve un �nonc� exprimant qu'elle est coh�rente, alors T est contradictoire.

Par contre une th�orie qui d�montre un �nonc� exprimant qu'elle n'est pas coh�rente, peut tr�s bien ne pas �tre contradictoire, comme on le d�duit du second th�or�me d'incompl�tude lui-m�me !

Esquissons la preuve. Appelons cohT un �nonc� qui exprime la coh�rence de T dans la th�orie T. D'apr�s ce qui pr�c�de, le second th�or�me d'incompl�tude affirme que, sous les hypoth�ses utiles sur T, si la th�orie T est coh�rente, la th�orie T'=T + non cohT est encore coh�rente. Rappelons que " T n'est pas coh�rente ", signifie qu'il existe une preuve d'une contradiction dans T. Une preuve dans T est aussi une preuve dans T' , qui a juste un axiome suppl�mentaire. Il est donc simple de montrer dans une th�orie telle que T, qui satisfait les hypoth�ses du th�or�me de G�del, que non cohT a pour cons�quence non cohT'. On a donc d�duit du second th�or�me de compl�tude, et de l'existence d'une th�orie coh�rente T qui satisfait les hypoth�ses de ce th�or�me -- prenons par exemple l'arithm�tique de Peano -- l'existence d'une th�orie T' coh�rente qui d�montre non cohT', � savoir un �nonc� exprimant qu'elle n'est pas coh�rente.

A contrario une th�orie incoh�rente, dans laquelle tous les �nonc�s sont prouvables, d�montrera �videmment un �nonc� exprimant qu'elle est coh�rente.

On voit par ces diverses remarques que le second th�or�me d'incompl�tude ne dit rien en d�faveur de la coh�rence d'une th�orie � laquelle il s'applique, par exemple la coh�rence de l'arithm�tique de Peano. Tout ce qu'il dit de cette derni�re, c'est qu'elle ne peut se prouver que dans une th�orie logiquement plus forte.

V�rit� et d�montrabilit�

La notion de v�rit� est parfois m�connue en dehors de la logique math�matique. Le th�or�me de G�del �tablit justement qu'un �nonc� arithm�tique peut �tre vrai (pour les entiers) sans �tre d�montrable. On d�finit la v�rit� relativement � un mod�le, et nous allons dans la suite nous int�resser � la v�rit� dans le mod�le standard de l'arithm�tique, les entiers que "tout le monde connait", que l'on note N. Rappelons que si l'on d�montre un �nonc� � partir d'�nonc�s vrais dans un mod�le, l'�nonc� obtenu est vrai dans ce mod�le, et que dans un mod�le un �nonc� (une formule close) est soit vrai soit faux, pas d'autre alternative. Par cons�quent la th�orie des �nonc�s vrais dans N est close par d�duction et compl�te. On d�duit imm�diatement du premier th�or�me d'incompl�tude que

    La th�orie des �nonc�s vrais dans N n'est pas r�cursivement axiomatisable.

et donc

    Si T est une th�orie r�cursivement axiomatisable qui permet de formaliser "suffisamment d'arithm�tique", et dont tous les axiomes sont vrais dans N, il existe un �nonc� vrai dans N qui n'est pas d�montrable dans T.

C'est un th�or�me d'incompl�tude, plus faible cependant que le premier th�or�me d'incompl�tude de G�del (il s'applique � moins de th�ories, on ne peut le formaliser dans l'arithm�tique, pour en d�duire le second th�or�me d'incompl�tude). Tel quel il se d�duit d'ailleurs du Th�or�me de Tarski (1933), qui est plus facile � d�montrer que celui de G�del. Comme l'�nonc� non d�montrable est vrai dans N et que la th�orie ne d�montre que des �nonc�s vrais dans N, la n�gation de cet �nonc� n'est pas non plus d�montrable. Par ailleurs comme la th�orie T a un mod�le, elle est coh�rente. En pr�cisant comme il faut la complexit� logique de l'�nonc� vrai non d�montrable, on pourra ne supposer que la v�rit� dans N des th�or�mes de cette complexit� logique, et on obtiendra un th�or�me �quivalent au premier th�or�me d'incompl�tude (celui d�montr� par G�del).

La notion de v�rit� utilis�e se d�finit math�matiquement, mais, par exemple, la v�rit� d'une formule du premier ordre de l'arithm�tique ne se d�finit pas dans l'arithm�tique de Peano. Le vocabulaire utilis� correspond � l'intuition, la notion est tr�s commode. Mais il n'est pas besoin d'attribuer une valeur excessive � cette notion pour l'utiliser. Par exemple, G�del construit effectivement un �nonc� dont il montre qu'il est vrai dans N, ce qui veut dire qu'on sait le prouver dans une th�orie plus forte que celle de d�part. La notion de v�rit� dans un mod�le s'est pr�cis�e au cours de la premi�re moiti� du vingti�me si�cle. � l'�poque o� G�del d�montre son th�or�me, elle n'est pas vraiment formalis�e, m�me s'il a d�montr� en 1929 le th�or�me de compl�tude et donc connait bien entendu cette notion. La d�finition utilis�e actuellement est due � Alfred Tarski, on la trouve dans un article publi� en 1956.

D�finissons la v�rit� dans N. Le langage a pour seul symbole de constante 0, pour seuls symboles de fonction s (la fonction successeur, qui ajoute 1), + et �, pour seul symbole de relation en plus de l'�galit�, le symbole d'in�galit� �.

Le mod�le standard se d�finit simplement : les seuls �l�ments de l'ensemble de base du mod�le sont les entiers usuels, tous d�crits par les termes du langage de la forme s ... s 0 (o� s est le signe pour la fonction successeur, "ajouter 1"), c'est � dire la notation unaire bien connue qui correspond � l'id�e primitive d'entier. Dans la vie courante on utilise plut�t un petit b�ton que la lettre s, et on n'�prouve pas le besoin de noter le z�ro. Les termes du langage sont essentiellement des polyn�mes, les formules atomiques des �galit�s ou in�galit�s polyn�miales. Pour d�finir le mod�le il reste � d�crire les formules atomiques closes, c'est � dire sans variable, vraies et fausses.

On d�finit facilement la v�rit� dans N des �galit�s et in�galit�s polyn�miales sur les entiers (pas de variable !) not�s de cette fa�on, et on peut m�me le faire m�caniquement, c'est � dire que la v�rit� des �nonc�s atomiques (�galit�s et in�galit�s polyn�miales closes) est d�cidable au sens algorithmique. Les algorithmes en jeu sont essentiellement ceux de l'addition et de la multiplication en base 1 (des suites de "b�tons"), conceptuellement plus simples que ceux que l'on enseigne � l'�cole primaire pour la base 10 (mais plus fastidieux � utiliser).

A partir de l�, on a d�fini le mod�le, et donc on a la d�finition par induction de la v�rit� d'une formule quelconque dans ce mod�le. Sans rentrer dans la d�finition formelle, observons quelques cas particuliers. Tout d'abord la v�rit� des formules closes sans quantificateurs reste d�cidable : on peut se ramener � des conjonctions et disjonctions d'�galit�s et d'in�galit�s (� et �) polyn�miales. Passons aux quantificateurs, un �nonc� du genre �x(P(x)=Q(x)) o� P et Q sont des polyn�mes � une seule variable, est vrai quand on peut trouver un entier n tel que P(n)=Q(n). Remarquez que s'il existe un tel entier, une machine pourra le trouver, en essayant les entiers les uns apr�s les autres par ordre croissant. Mais la machine ne s'arr�tera pas s'il n'existe pas de tel entier. Il n'y a pas d'�vidence que la v�rification de telles formules est algorithmiquement d�cidable (et elle ne l'est pas).

La situation est "pire" pour le quantificateur universel : un �nonc� du genre � x(P(x)=Q(x)) est vrai si pour chaque entier n, l'�galit� P(n)=Q(n) est vraie : c'est bien d�fini, mais, si l'on suit la d�finition, cela demande une infinit� de v�rifications ! On voit bien la diff�rence entre v�rit� et d�montrabilit�. Une preuve est n�cessairement finie, et de plus on doit pouvoir reconna�tre m�caniquement une preuve formelle. Pour d�montrer un �nonc� universel tel que celui-ci, habituellement on fait une r�currence. Sommairement, une preuve par r�currence est une fa�on finie de repr�senter une infinit� de v�rifications. Au passage on a perdu quelque chose, comme l'�nonce pr�cis�ment le th�or�me de G�del.

Quand on a un moyen m�canique de d�cider la v�rit� de certaines classes d'�nonc�s, par exemple les �nonc�s sans quantificateurs, on a une preuve de ces �nonc�s, ou de leurs n�gations, au sens informel de cette notion. Dans les cas abord�s ci-dessus, ces preuves sont effectivement formalisables dans les th�ories pour lesquelles on d�montre les th�or�mes de G�del.

Des exemples de syst�mes incomplets et d'�nonc�s ind�cidables

L'existence de th�ories incompl�tes est banale. Beaucoup de th�ories, comme la th�orie des groupes, des anneaux, des corps, ne sont pas compl�tes : par exemple on peut dire au premier ordre qu'un groupe ou un corps a 2 �l�ments, ou 3 �l�ments. C'est diff�rent pour l'arithm�tique, on aurait souhait� capturer par une axiomatique toutes les propri�t�s des entiers naturels. Pour les th�ories destin�es � fonder les math�matiques, Principia Mathematica ou th�orie axiomatique des ensembles, on peut s'attendre � ne pas avoir encore d�couvert tous les axiomes. Mais le th�or�me de G�del affirme qu'il restera toujours des �nonc�s ind�cidables (tant que la th�orie reste r�cursivement axiomatisable).

Il existe �galement des th�ories compl�tes int�ressantes, comme l'arithm�tique de Presburger d�j� �voqu�e, la th�orie des corps alg�briquement clos d'une caract�ristique donn�e, la th�orie des corps r�els clos, et la g�om�trie �l�mentaire qui lui est associ�e.

�nonc�s ind�cidables dans l'arithm�tique de Peano

Appliqu�s � l'arithm�tique, les th�or�mes de G�del fournissent des �nonc�s dont la signification est tout � fait int�ressante, puisqu'il s'agit de la coh�rence de la th�orie. Cependant ces �nonc�s d�pendent du codage choisi. Ils sont p�nibles � �crire explicitement.

Paris et Harrington ont montr� en 1977 qu'un renforcement du th�or�me de Ramsey fini, vrai dans N, n'est pas d�montrable dans l'arithm�tique de Peano. Il s'agit du premier exemple d'�nonc� ind�cidable dans l'arithm�tique qui n'utilise pas de codage du langage. Depuis, on en a d�couvert d'autres. Le th�or�me de Goodstein est un tel �nonc� ; sa preuve est particuli�rement simple (quand on conna�t les ordinaux), mais utilise une induction jusqu'� l'ordinal d�nombrable �0. Kirby et Paris ont d�montr� en 1982 que l'on ne peut pas prouver ce th�or�me dans l'arithm�tique de Peano.

Les �nonc�s de ce genre qui ont �t� d�couverts sont des r�sultats de combinatoire. Leur preuve n'est pas n�cessairement tr�s compliqu�e, et en fait il n'y a aucune raison de penser qu'il y a un lien entre complexit� technique d'une preuve et possibilit� de formaliser celle-ci dans l'arithm�tique de Peano.

�nonc�s ind�cidables en th�orie des ensembles

En th�orie des ensembles, on a d'autres �nonc�s ind�cidables que ceux fournis par le th�or�me de G�del qui peuvent �tre de nature diff�rente. Ainsi, d'apr�s des travaux de G�del, puis de Paul Cohen, l'axiome du choix et l'hypoth�se du continu sont des �nonc�s ind�cidables dans ZF la th�orie des ensemble de Zermelo et Fraenkel, le second �tant d'ailleurs ind�cidable dans ZFC (ZF plus l'axiome du choix). Mais d'une part, ce ne sont pas des �nonc�s arithm�tiques. D'autre part, la th�orie obtenue en ajoutant � ZF l'axiome du choix ou sa n�gation est �qui-coh�rente � ZF : la coh�rence de l'une entra�ne la coh�rence de l'autre et r�ciproquement. De m�me pour l'hypoth�se du continu. Ce n'est pas le cas pour un �nonc� exprimant la coh�rence de ZF, d'apr�s justement le second th�or�me d'incompl�tude. De m�me pour l'un des deux �nonc�s obtenus par les preuves usuelles du premier th�or�me d'incompl�tude (il est �quivalent � un �nonc� de coh�rence).

D�s que l'on peut montrer dans une th�orie des ensembles T+A, qu'un ensemble (un objet de la th�orie) est mod�le de la th�orie des ensembles T, c'est � dire la coh�rence de T, on d�duit par le second th�or�me d'incompl�tude que, si T est coh�rente, A n'est pas d�montrable dans T. On montre ainsi que certains axiomes qui affirment l'existence de "grands" cardinaux, ne sont pas d�montrables dans ZFC.

Th�or�mes d'incompl�tude et calculabilit�

La notion de calculabilit� intervient a divers titres � propos des th�or�mes d'incompl�tude. On l'a utilis� pour en d�finir les hypoth�ses. Elle intervient dans la preuve du premier th�or�me d'incompl�tude (G�del utilise les fonctions r�cursives primitives). Enfin incompl�tude et ind�cidabilit� de l'arithm�tique sont li�es.

Ind�cidabilit� algorithmique

Il y a un lien �troit entre d�cidabilit� algorithmique d'une th�orie, l'existence d'une m�thode m�canique pour tester si un �nonc� est ou non un th�or�me, et compl�tude de cette th�orie. Une th�orie r�cursivement axiomatisable et compl�te est d�cidable. On peut donc prouver le premier th�or�me d'incompl�tude en montrant qu'une th�orie qui satisfait les hypoth�ses utiles est ind�cidable. Ce r�sultat, l'ind�cidabilit� algorithmique des th�ories qui satisfont les hypoth�ses du premier th�or�me d'incompl�tude, a �t� d�montr� ind�pendemment par Turing et Church en 1936 (voir probl�me de la d�cision), en utilisant les m�thodes d�velopp�es par G�del pour son premier th�or�me d'incompl�tude. Pour un r�sultat d'ind�cidabilit�, qui est un r�sultat n�gatif, il faut avoir formalis� la calculabilit�, et �tre convaincu que cette formalisation est correcte, conviction qui ne peut reposer seulement sur des bases math�matiques. En 1931, G�del conna�t un mod�le de calcul que l'on dirait maintenant Turing-complet, les fonctions r�cursives g�n�rales, d�crit dans une lettre que Jacques Herbrand lui a adress�e, et qu'il a lui-m�me pr�cis� et expos� en 1934. Cependant il n'est pas convaincu � l'�poque d'avoir d�crit ainsi toutes les fonctions calculables. � la suite de travaux de Kleene, Church, et Turing, ces deux derniers ont �nonc� ind�pendemment en 1936 la th�se de Church-Turing : les fonctions calculables sont les fonctions r�cursives g�n�rales.

On peut �tre plus pr�cis en donnant une classe restreinte d'�nonc�s pour laquelle la prouvabilit� est ind�cidable. Si on reprend les arguments d�velopp�s dans le paragraphe V�rit� et d�montrabilit� ci-dessus, on voit par exemple que la classe des �nonc�s sans quantificateurs (et sans variables) est, elle, d�cidable.

En utilisant les arguments d�velopp�s par G�del, on montre que la prouvabilit� des �nonc�s �1 est ind�cidable. Sans entrer dans le d�tail de la d�finition des formules �1 (faite ci-dessous), cela ne semble pas si loin d'une solution n�gative au dixi�me probl�me de Hilbert : l'existence d'un algorithme de d�cision pour la r�solution des �quations diophantiennes. Mais il fallu plusieurs dizaines d'ann�es et les efforts successifs de plusieurs math�maticiens dont Martin Davis, Hilary Putnam, Julia Robinson et finalement Youri Matiiassevitch pour y arriver en 1970 (voir th�or�me de Matiiassevitch).

On peut tout � fait d�duire le premier th�or�me de G�del du th�or�me de Matiiassevitch. Cela peut para�tre artificiel, puiqu'un r�sultat d'ind�cidabilit� beaucoup plus facile � d�montrer suffit. Mais on peut en d�duire des �nonc�s ind�cidables d'une forme particuli�rement simple. En effet, le th�or�me de Matiiassevitch �quivaut � dire que la v�rit� des �nonc�s (formules closes) qui s'�crivent comme des �galit�s polynomiales quantifi�es existentiellement, n'est pas d�cidable. Or :

    * on peut reconna�tre m�caniquement de tels �nonc�s, et donc leurs n�gations ;

    * L'ensemble des tels �nonc�s vrais est r�cursivement �num�rable, et donc, d'apr�s le th�or�me de Matiiassevitch, l'ensemble des tels �nonc�s faux n'est pas r�cursivement �num�rable ;

    * l'ensemble des th�or�mes d'une th�orie r�cursivement axiomatisable est r�cursivement �num�rable (voir Th�orie r�cursivement axiomatisable), et donc l'ensemble des th�or�mes qui s'�crivent comme la n�gation d'une �galit� polyn�miale quantifi�e existentiellement �galement ;

    * l'hypoth�se de coh�rence que fait G�del pour son premier th�or�me d'incompl�tude a pour cons�quence directe que des �galit�s quantifi�s existentiellement et fausses ne peuvent �tre d�montrables.

On en d�duit qu'il existe des �nonc�s vrais non d�montrables, qui s'�crivent comme la n�gation d'une �galit� polyn�miale quantifi�e existentiellement, ou plus simplement comme une in�galit� polyn�miale quantifi�e universellement.

La mise en cause du mouvement formaliste

Pour r�pondre aux probl�mes de la crise des fondements des math�matiques, Hilbert et ses �l�ves avaient d�velopp� un programme qui devait apporter une r�ponse d�finitive aux probl�mes des fondements des math�matiques. Le programme de Hilbert reposait de fa�on essentielle sur la possibilit� de prouver la coh�rence des th�ories math�matiques par des m�thodes finitaires : sans plus pr�ciser, des m�thodes qui devaient pouvoir se formaliser dans une th�orie probablement plus faible que l'arithm�tique de Peano. On d�duit imm�diatement du second th�or�me d'incompl�tude que ce n'est pas possible pour toute th�orie r�cursivement axiomatisable permettant de formaliser les math�matiques, et donc de d�finir l'arithm�tique de Peano elle-m�me.

Il y eu des tentatives pour rem�dier � cette situation en pr�cisant et en �tendant la notion de m�thode finitaire, m�me si, d'apr�s le second th�or�me de G�del, on ne peut esp�rer d�finir une fois pour toutes une th�orie (r�cursivement axiomatisable) pour de telles m�thodes finitaires. Ainsi Gentzen a prouv� en 1936 la coh�rence de l'arithm�tique en utilisant un principe de r�currence jusqu'� l'ordinal d�nombrable �0, mais pour des formules de complexit� logique tr�s simple. Cette preuve d�veloppe des outils qui se sont r�v�l�s fondamentaux en th�orie de la d�monstration. Elle est indubitablement une preuve de coh�rence relative. On l'interpr�tera plus volontiers aujourd'hui comme une fa�on de mesurer la "force" de l'arithm�tique de Peano (par un ordinal).

Une preuve partielle du premier th�or�me d'incompl�tude

La preuve par G�del de son premier th�or�me d'incompl�tude utilise essentiellement deux ingr�dients :

    * le codage par des nombres entiers du langage et des fonctions qui permettent de le manipuler, ce que l'on appelle l'arithm�tisation de la syntaxe ;

    * un argument diagonal qui fait appara�tre un �nonc� similaire au paradoxe du menteur : l'�nonc� de G�del est �quivalent, via codage, � un �nonc� affirmant sa propre non prouvabilit� dans la th�orie consid�r�e.

L'�nonc� de G�del n'est pas paradoxal. Il est vrai dans N, car s'il �tait faux, il serait prouvable. Or cet �nonc� est de complexit� logique suffisamment simple pour que sa prouvabilit� dans une th�orie coh�rente capable de coder l'arithm�tique entra�ne sa v�rit� dans N (on n'a pas besoin de supposer que N est mod�le de la th�orie). Il est donc vrai dans N. il n'est donc pas prouvable.

Pour montrer que la n�gation de l'�nonc� de G�del n'est pas non plus prouvable, il faut une hypoth�se de coh�rence plus forte, comme celle qu'a faite G�del. Rosser a modifi� astucieusement l'�nonc� pour pouvoir utiliser simplement la coh�rence. En ce qui concerne la preuve de G�del l'argument est le suivant : l'�nonc� �tant vrai, sa n�gation est fausse. Si on supposait que N est mod�le de la th�orie, cela suffirait pour qu'elle ne soit pas d�montrable. Mais G�del a construit un �nonc� d'une complexit� logique suffisamment faible pour qu'une hypoth�se beaucoup moins forte suffise : il s'agit essentiellement de dire que de tels �nonc�s faux ne peuvent �tre d�montrables, et il peut l'exprimer de fa�on syntaxique.

Arithm�tisation de la syntaxe

� l'�poque actuelle, quiconque connait un peu d'informatique n'a aucun mal � imaginer que l'on puisse repr�senter les �nonc�s d'une th�orie par des nombres. Cependant il faut �galement manipuler ces codages dans la th�orie. La difficult� r�side dans les restrictions du langage : une th�orie du premier ordre avec essentiellement l'addition et la multiplication comme symboles de fonction. C'est la difficult� que G�del r�sout pour montrer que la prouvabilit� peut �tre repr�sent�e par une formule dans la th�orie.

La suite est un peu technique. On peut simplifier l'argumentation en supposant que N est mod�le de T, auquel cas on n'a pas besoin d'�tre attentif � la complexit� logique de l'�nonc�. La partie sur la fonction � et la repr�sentation de la r�currence reste utile. On pr�cise �galement des notions, et des r�sultats qui ont �t� �voqu�s ou r�dig�s de fa�on approximative ci-dessus.

Codes

Il peut �tre amusant d'�crire soi m�me les codages, il l'est certainement beaucoup moins de lire ceux des autres. On trouve donc beaucoup de vari�t� dans la litt�rature. Le choix du codage n'a pas grande importance, en soi. �ventuellement certains se "manieront" plus facilement dans la th�orie. Comme les formules et les d�monstrations peuvent �tre vues comme des suites finies de caract�res, lettres, espace, ponctuation, et ceux-ci en nombre fini, on peut les coder par un nombre, celui �tant �crit dans une base de la taille nombre de caract�re n�cessaire, ou par tout autre moyen qui permet de coder des suites finies d'entier. On peut �galement utiliser un codage des couples (voir ci-dessous) pour repr�senter, suites finies, arbres, et donc les structures syntaxiques utiles ...

Formules �0

Un probl�me plus important est d'avoir des fonctions pour manipuler ces structures, l'�quivalent des programmes en informatique : il est � peu pr�s clair que l'on ne peut se contenter de compositions de fonctions constantes, d'additions et de multiplications, c'est � dire de polyn�mes � coefficients entiers positifs. On va repr�senter les fonctions utiles par des formules. Voyons un exemple, par ailleurs fort utile pour les codages. La bijection de Cantor entre N�N et N est bien connue et tout � fait calculable : on �num�re les couples d'entiers diagonale par diagonale (somme constante), par exemple en faisant cro�tre la seconde composante :

Cette fonction n'est d�j� plus repr�sent�e par un terme du langage, � cause de la division par 2, mais elle est repr�sent�e par la formule (on utilise "�" pour la relation d'�quivalence) :

Passons maintenant aux fonctions de d�codage, c'est � dire � un couple de fonctions inverses. On aura besoin de quantificateurs :

On a donc repr�sent� une fonction, plus exactement son graphe (la formule soulign�e) par une formule du langage de l'arithm�tique. Les formules ci-dessus sont bien particuli�res : la premi�re est une �galit� polyn�miale, si on remplace les trois variables libres par des termes clos du langage, repr�sentant des entiers (s�s0), elle devient d�cidable. Les deux suivantes utilisent un quantificateur born� : "�x�z A" signifie "il existe un x plus petit ou �gal � z tel que A". L� encore si on remplace les deux variables libres par des entiers cette formule devient d�cidable : pour v�rifier une quantification existentielle born�e, il suffit de chercher jusqu'� la borne, soit on a trouv�, et l'�nonc� est v�rifi�, soit on n'a pas trouv� et il ne l'est pas. Ce n'est plus le cas (pour la seconde partie de l'assertion) si la quantification existentielle n'est pas born�e. On pourra conserver cette propri�t� de d�cidabilit� en ajoutant des quantifications universelles born�es, not�e "� x� p A" ("pour tout x plus petit ou �gal � p, A"). Les formules construites � partir des �galit�s polyn�miales en utilisant les connecteurs bool�ens usuels, et des quantifications uniquement born�es sont appel�es formules �0. Remarquez que la n�gation d'une formule �0 est �0.

On se convainc facilement, des arguments sont donn�s juste ci-dessus et au paragraphe v�rit� et d�montrabilit�, que la v�rit� dans N des formules closes �0 est d�cidable : on a un moyen m�canique de savoir si elles sont vraies ou fausses. Pour d�montrer le premier th�or�me d'incompl�tude de G�del (il faut un peu plus pour G�del-Rosser, de la r�currence pour le second), la condition minimale sur la th�orie, en plus d'�tre r�cursivement axiomatisable et d'une hypoth�se de coh�rence, est de d�montrer toutes les formules �0 vraies dans N, et donc, par stabilit� par n�gation des �0 et coh�rence, de n'en d�montrer aucune fausse. C'est ce que l'on a entendu par "formaliser suffisamment d'arithm�tique". Remarquez que c'est une hypoth�se sur les axiomes de la th�orie. Par exemple l'ensemble des formules �0 vraies dans N �tant d�cidable, on peut le choisir comme syst�me d'axiomes pour une th�orie qui sera bien r�cursivement axiomatisable (on peut �videmment le simplifier). En particulier on peut d�montrer :

    Dans l'arithm�tique de Peano, les formules closes �0 sont vraies dans N si et seulement si elles sont d�montrables.

R�sultat qui se d�montre d'ailleurs sans v�ritablement utiliser de r�currence (ce qui est naturel puisqu'il n'y a pas v�ritablement de quantification universelle dans ces �nonc�s).

Il serait bien commode de se contenter de manipuler des fonctions repr�sentables par des formules �0 : v�rit� et d�montrabilit� sont confondues, ces formules sont d�cidables, donc les fonctions repr�sent�es par des formules �0 sont calculables. Mais le "langage de programmation" induit n'est pas assez riche. On doit introduire les formules �1, qui sont les formules obtenues en pla�ant un quantificateur existentiel en t�te d'une formule �0. En g�n�ral la n�gation d'une formule �1 n'est pas �quivalente � une formule �1. On a la propri�t� suivante :

    Dans une th�orie qui prouve toutes les formules �0 vraies dans N, les formules �1 vraies dans N sont prouvables.

En effet une formule �1 "� x A x" est vraie dans N signifie que pour un certain entier, que l'on peut �crire "s�s0", la formule "A s�s0" est vraie, or cette formule est �0.

Il existe de th�ories arithm�tiques coh�rentes, qui d�montrent des formules closes �1 fausses, contrairement � ce qui se passe pour les �0. Il faut pr�ciser que de telles th�ories arithm�tiques sont assez pathologiques, comme celles qui d�montrent un �nonc� exprimant leur propre contradiction (voir d�but de l'article). L'hypoth�se de coh�rence suppl�mentaire utile pour le premier th�or�me d'incompl�tude, que l'on va appeler �-coh�rence, c'est justement de supposer que la th�orie ne d�montre aucune formule close �1 fausse. On suppose que certaines formules ne sont pas d�montrables, donc la contradiction ne l'est pas : c'est bien une hypoth�se de coh�rence au moins aussi forte que la coh�rence simple. Elle est vraiment plus forte : on peut exprimer la n�gation de la coh�rence d'une th�orie par une formule �1[1].

Fonctions d�finissables, fonctions repr�sentables

Un sous-ensemble E de N, ou plus g�n�ralement de Np est d�finissable dans l'arithm�tique s'il existe une formule F de l'arithm�tique avec p variables libres telle que :

Un sous-ensemble E de Np est repr�sentable dans une th�orie T s'il existe une formule s'il existe une formule F de l'arithm�tique avec p variables libres telle que :

Une fonction f � plusieurs variables sur N est d�finissable dans N si son graphe est d�fini dans N, repr�sentable dans une th�orie T' si son graphe est repr�sentable dans T. Un ensemble, ou une fonction est d�finissable par une formule �1 si et seulement si il, ou elle, est repr�sentable par cette formule dans une th�orie �-coh�rente o� tous les �nonc�s �0 sont d�montrables.

Il existe d'autres notions de repr�sentabilit� plus fortes, pour les ensembles comme pour les fonctions. Pour celle introduite ici on dit souvent faiblement repr�sentable.

On notera y=f(x) une formule �1 d�finissant ou repr�sentant f. Pour le th�or�me de G�del c'est la notion de fonction ou d'ensemble repr�sentable qui est utile, mais la notion de fonction ou d'ensemble d�finissable est plus simple � manipuler, et comme on s'int�resse aux cas o� elles sont �quivalentes, on va dans la suite parler de d�finissabilit� par une formule �1.

On peut remarquer que la conjonction, la disjonction de deux formules �1, la quantification existentielle d'une formule �1, la quantification universelle born�e d'une formule �1, sont �quivalentes dans N (on note �N) � une formule �1 :

L'ensemble de fonctions � notre disposition est donc stable par composition (on donne l'exemple pour une variable, on g�n�ralise sans peine � des fonctions de plusieurs variables) :

On d�finit �galement de fa�on naturelle :

Cependant, pour pouvoir avoir un langage suffisamment expressif pour d�finir les fonctions utiles sur la syntaxe, il manque une notion tr�s utile : la d�finition par r�currence. L'id�e pour l'obtenir est d'utiliser un codage des suites finies (les listes de l'informatique). Supposons que nous ayons un tel codage, notons l=[n0;�;np] l'entier qui code la suite finie n0,�,np. Il faut pouvoir d�coder : notons �(l,i)=ni l'�l�ment en place i de la suite cod�e par l (la valeur n'a pas d'importance si i est trop grand). Supposons que nous ayons une fonction g � valeur et image enti�re (une suite infinie d'entiers) d�finie par :

et que f soit d�finissable dans N. Alors on pourra d�finir la fonction g par :

formule qui est �quivalente dans N � une formule �1 d�s que le graphe de � est �1. Ceci se g�n�ralise au sch�ma de r�currence utilis� pour les fonctions r�cursives primitives. Il suffit donc trouver une formule �1 qui d�finit une fonction � : c'est la principale difficult� � r�soudre pour le codage de la syntaxe.

Le nom de fonction � est repris de l'article original de G�del. Pour la d�finir, il a eu l'id�e d'utiliser le th�or�me des restes chinois : pour coder n1,�,np on va donner p entiers premiers entre eux eux � deux, engendr�s � partir d'un seul entier d, et un entier a dont les restes des divisions par chacun de ces entiers sont n1,�,np. La suite n1,�,np sera donc cod�e par les deux entiers a et d, l'entier <a,d> si on en veut un seul. Plusieurs (une infinit� !) entiers coderont la m�me suite, ce qui n'est pas g�nant si on pense � l'objectif (coder les d�finitions par r�currence). Le principal est que l'on assure que toute suite finie a au moins un code.

�tant donn�s les entiers n1,�,np, on choisi un entier s, tel que s � p et pour tout ni, s�ni. Les entiers

sont alors premiers entre eux deux � deux. De plus ni < di. Par le th�or�me chinois on d�duit l'existence d'un entier a tel que pour chaque entier ni de la suite finie, le reste de la division de a par di soit ni. On a donc, en posant d = s! :

On a bien une fonction � d�finie par une formule �0.

On en d�duit que :

    si une fonction se d�finit par r�currence primitive � partir de fonctions d�finissables par des formules �1, elle est d�finissable par une formule �1.

On peut faire beaucoup de choses avec les fonctions r�cursives primitives. Une fois ce r�sultat obtenu, le reste n'est plus qu'affaire de soin. On peut utiliser des m�thodes plus ou moins astucieuses pour g�rer les probl�mes de liaison de variables. On montre que la fonction qui code la substitution d'un terme � une variable dans une formule est r�cursive primitive, que l'ensemble des (codes de) preuves d'une th�orie T r�cursivement axiomatisable est r�cursif primitif, et enfin que la fonction qui extrait d'une preuve la conclusion de celle-ci est r�cursive primitive. Dire qu'une formule est prouvable dans T, c'est dire qu'il existe une preuve de cette formule dans T, ce qui, cod� dans la th�orie, reste �1 (bien que le pr�dicat "�tre d�montrable" ne soit pas lui r�cursif primitif, ni m�me r�cursif).

En conclusion, pour une th�orie r�cursivement axiomatisable T, on a deux formules �1, DemT(x) et z=sub(x,y), telles que :

    DemT(�F�) est vraie dans N si et seulement si F est prouvable dans T ;  pour une formule Fx, �Fn�=sub(�F�,n).

On a not� �F� l'entier qui code la formule F.

Du fait que les formules sont �1, on peut remplacer "vrai" par "d�montrable dans T" sous les hypoth�ses suffisantes.

Diagonalisation

La construction de l'�nonc� de G�del repose sur un argument diagonal. On construit tout d'abord la formule � une variable libre �(x) :

qui peut s'interpr�ter dans N par la formule de code x appliqu�e � son propre code n'est pas d�montrable dans T, et on applique cette formule � l'entier ���. On obtient G=�(���) , une formule qui dit bien d'elle m�me qu'elle n'est pas d�montrable dans T. On reprend en la pr�cisant l'argumentation d�j� donn�e au dessus. On suppose que T est r�cursivement axiomatisable, d�montre toutes les formules �0 vraies dans N, donc toutes les formules �1 vraies dans N, et qu'elle est �-coh�rente.

    * G=�(���) est une formule close, �quivalente � la n�gation d'une formule �1 ;

    * si la formule G �tait d�montrable, la n�gation de G �tant �1 ne pourrait �tre vraie car alors elle serait d�montrable, et donc cela contredirait la coh�rence de T. La formule G serait donc vraie dans N, ce qui voudrait dire, par construction de G, que la formule G ne serait pas d�montrable, contradiction. Donc G n'est pas d�montrable.

    * si la n�gation de la formule G �tait d�montrable dans T, par �-coh�rence elle serait vraie, or elle est fausse d'apr�s ce qui pr�c�de. Donc la n�gation de G n'est pas d�montrable.

On voit donc bien, le dernier argument �tant assez tautologique, que le premier th�or�me d'incompl�tude de G�del s'�nonce aussi bien par :

    Si T est une th�orie r�cursivement axiomatisable, coh�rente, et qui d�montre toutes les formules �0 vraies dans N, alors il existe une formule G, n�gation d'une formule �1, qui est vraie dans N, mais non d�montrable dans T.

Argument de la preuve du second th�or�me d'incompl�tude

Le second th�or�me d'incompl�tude se prouve essentiellement en formalisant la preuve du premier th�or�me d'incompl�tude pour une th�orie T dans cette m�me th�orie T. En effet, on a montr� ci-dessus que, si la th�orie �tait coh�rente la formule G de G�del (qui d�pend de T), n'est pas prouvable. Mais la formule de G�del est �quivalente � sa non prouvabilit�. On a donc montr� que la coh�rence de la th�orie T entra�ne G : si T est suffisante pour formaliser cette preuve, on a alors montr� dans la th�orie T que la coh�rence de la th�orie T entra�ne G, formule qui n'est pas prouvable dans T, donc n'est pas prouvable dans T.

On utilise simplement la non-d�montrabilit� de G, donc l'hypoth�se de coh�rence simple suffit. Par contre la th�orie T doit forc�ment �tre plus expressive que pour le premier th�or�me d'incompl�tude. En particulier on a besoin de r�currence.

Les conditions que doivent v�rifier la th�orie T pour d�montrer le second th�or�me d'incompl�tude ont �t� pr�cis�es tout d'abord par Paul Bernays dans les Grundlagen der Mathematik (1939) co-�crit avec David Hilbert, puis par Martin L�b, pour la d�monstration de son th�or�me, une variante du second th�or�me d'incompl�tude. Les conditions de d�montrabilit� de L�b portent sur le pr�dicat de prouvabilit� dans la th�orie T, que l'on nomme comme ci-dessus DemT :

On s'est a de fait d�montr� la condition D1 pour d�montrer le premier th�or�me d'incompl�tude. La seconde condition D2 est une formalisation dans la th�orie de D1. Enfin la derni�re, D3, est une formalisation de la r�gle logique primitive dite de Modus Ponens. Notons cohT la formule qui exprime la coh�rence de T, c'est � dire que l'absurde, que l'on note �, n'est pas d�montrable :

Comme la n�gation d'une formule F, �F, �quivaut � F entra�ne l'absurde, F��, on d�duit de la condition D3 que

Pour d�duire le second th�or�me d'incompl�tude des trois conditions de L�b, il suffit de reprendre le raisonnement d�j� fait ci-dessus. Soit G la formule de G�del, qui, sous hypoth�se de coh�rence simple, entra�ne �DemT(�G�). D'apr�s D1 et la coh�rence de la th�orie T, G n'est pas d�montrable dans T (premier th�or�me). On formalise maintenant ce raisonnement dans T. Supposons que dans T, DemT(�G�). Comme d'autre part on d�montre dans T que DemT(�G � �DemT(�G�)�), on d�duit par D3 dans T, DemT(��DemT(�G�)�). Finalement par D'3 on a montr� �cohT dans T. R�capitulons : on a montr� dans T que DemT(�G�) � �cohT, c'est � dire par d�finition de G, �G � �cohT, et par contrapos�e cohT � G. Or on a vu que G n'est pas d�montrable dans T, donc cohT n'est pas d�montrable dans T.

La preuve de D1 a �t� d�j� �t� esquiss�e � propos du premier th�or�me d'incompl�tude : il s'agit de formaliser proprement la d�montrabilit�, et on utilise que les formules closes �1 vraies sont d�montrables.

La condition D3 formalise la r�gle de modus ponens, une r�gle que l'on a tout int�r�t � avoir dans les syst�me formel pour les d�monstrations que l'on a choisi. Il faudrait rentrer dans le d�tail du codage pour donner la preuve de D3, mais elle ne sera pas bien difficile. Il faut faire attention � bien formaliser le r�sultat indiqu� dans la th�orie choisie : les variables en jeu (par exemple il existe un x qui est le code d'une preuve de F) sont les variables de la th�orie. Il faudra quelques r�sultats sur l'ordre, savoir d�montrer quelques r�sultats �l�mentaires sur les preuves dans la th�orie.

C'est la condition D2 qui s'av�re la plus d�licate a d�montrer. C'est un cas particulier de la propri�t�

qui formalise (dans T) que toute formule close �1 vraie est d�montrable dans T. On n'a donn� ci-dessus aucun d�tail sur la preuve de ce dernier r�sultat, T �tant par exemple l'arithm�tique de Peano. Si on en donnait, on se rendrait compte que l'on n'a pas besoin de l'axiome de r�currence de la th�orie, mais que, par contre, l'on raisonne par r�currence sur la longueur des termes, la complexit� des formules ... Comme il faut maintenant formaliser cette preuve dans la th�orie, il faut de la r�currence. Pour r�sumer la situation : quand on a d�montr� s�rieusement le premier th�or�me d'incompl�tude pour l'arithm�tique de Peano, on a fait cette preuve, qui est un peu longue, mais ne pr�sente pas de difficult�. Pour le second th�or�me, la seule chose � faire consiste maintenant � montrer que cette preuve se formalise dans l'arithm�tique de Peano elle-m�me, ce qui est intuitivement relativement clair (quand on a fait la preuve), mais tr�s p�nible � expliciter compl�tement.

On peut en fait d�montrer le second th�or�me d'incompl�tude pour une th�orie plus faible que l'arithm�tique de Peano, l'arithm�tique primitive r�cursive. On �tend le langage de fa�on � avoir des symboles de fonction pour toutes les fonctions primitives r�cursives, et on ajoute � la th�orie les axiomes qui d�finissent ces fonctions. On restreint la r�currence aux formules sans quantificateurs, ce qui fait que celles-ci sont "imm�diates". L'arithm�tique primitive r�cursive est souvent consid�r�e comme la formalisation des math�matiques finitaires, avec lesquelles Hilbert esp�rait pouvoir prouver la coh�rence des th�ories math�matiques.
"""
# source: http://fr.wikipedia.org/wiki/Th%C3%A9or%C3%A8me_de_G%C3%B6del

GG_TEXT = """\
La Gaule et ses habitants

    Toute la Gaule est divis�e en trois parties, dont l'une est habit�e par les Belges, l'autre par les Aquitains, la troisi�me par ceux qui, dans leur langue, se nomment Celtes, et dans la n�tre, Gaulois. Ces nations diff�rent entre elles par le langage, les institutions et les lois. Les Gaulois sont s�par�s des Aquitains par la Garonne, des Belges par la Marne et la Seine. Les Belges sont les plus braves de tous ces peuples, parce qu'ils restent tout � fait �trangers � la politesse et � la civilisation de la province romaine, et que les marchands, allant rarement chez eux, ne leur portent point ce qui contribue � �nerver le courage : d'ailleurs, voisins des Germains qui habitent au-del� du Rhin, ils sont continuellement en guerre avec eux. Par la m�me raison, les Helv�tes surpassent aussi en valeur les autres Gaulois ; car ils engagent contre les Germains des luttes presque journali�res, soit qu'ils les repoussent de leur propre territoire, soit qu'ils envahissent celui de leurs ennemis. Le pays habit�, comme nous l'avons dit, par les Gaulois, commence au Rh�ne, et est born� par la Garonne, l'Oc�an et les fronti�res des Belges ; du c�t� des S�quanes et des Helv�tes, il va jusqu'au Rhin ; il est situ� au nord. Celui des Belges commence � l'extr�me fronti�re de la Gaule, et est born� par la partie inf�rieure du Rhin ; il regarde le nord et l'orient. L'Aquitaine s'�tend de la Garonne aux Pyr�n�es, et � cette partie de l'Oc�an qui baigne les c�tes d'Espagne ; elle est entre le couchant et le nord.

Les Helv�tes. Plans ambitieux d'Org�torix. Sa mort

    Org�torix �tait, chez les Helv�tes, le premier par sa naissance et par ses richesses. Sous le consulat de M. Messala et de M. Pison, cet homme, pouss� par l'ambition, conjura avec la noblesse et engagea les habitants � sortir du pays avec toutes leurs forces ; il leur dit que, l'emportant par le courage sur tous les peuples de la Gaule, ils la soumettraient ais�ment tout enti�re � leur empire. Il eut d'autant moins de peine � les persuader que les Helv�tes sont de toutes parts resserr�s par la nature des lieux ; d'un c�t� par le Rhin, fleuve tr�s large et tr�s profond, qui s�pare leur territoire de la Germanie, d'un autre par le Jura, haute montagne qui s'�l�ve entre la S�quanie et l'Helv�tie ; d'un troisi�me c�t�, par le lac L�man et le Rh�ne qui s�pare cette derni�re de notre Province. Il r�sultait de cette position qu'ils ne pouvaient ni s'�tendre au loin, ni porter facilement la guerre chez leurs voisins ; et c'�tait une cause de vive affliction pour des hommes belliqueux. Leur population nombreuse, et la gloire qu'ils acqu�raient dans la guerre par leur courage, leur faisaient regarder comme �troites des limites qui avaient deux cent quarante milles de long sur cent quatre-vingts milles de large.

    Pouss�s par ces motifs et entra�n�s par l'ascendant d'Org�torix, ils commencent � tout disposer pour le d�part, rassemblent un grand nombre de b�tes de somme et de chariots, ensemencent toutes leurs terres, afin de s'assurer des vivres dans leur marche et renouvellent avec leurs voisins les trait�s de paix et d'alliance. Ils pens�rent que deux ans leur suffiraient pour ces pr�paratifs ; et une loi fixa le d�part � la troisi�me ann�e. Org�torix est choisi pour pr�sider � l'entreprise. Envoy� en qualit� de d�put� vers les cit�s voisines, sur sa route, il engage le S�quanais Casticos, fils de Catamantalo�dis, et dont le p�re avait longtemps r�gn� en S�quanie et avait re�u du peuple romain le titre d'ami, � reprendre sur ses concitoyens l'autorit� supr�me, pr�c�demment exerc�e par son p�re. Il inspire le m�me dessein � l'H�duen Dumnorix, fr�re de Diviciacos, qui tenait alors le premier rang dans la cit� et �tait tr�s aim� du peuple ; il lui donne sa fille en mariage. Il leur d�montre la facilit� du succ�s de leurs efforts ; devant lui-m�me s'emparer du pouvoir chez les Helv�tes, et ce peuple �tant le plus consid�rable de toute la Gaule, il les aidera de ses forces et de son arm�e pour leur assurer l'autorit� souveraine. Persuad�s par ces discours, ils se lient sous la foi du serment. : ils esp�raient qu'une fois ma�tres du pouvoir, au moyen de cette ligue des trois peuples les plus puissants et les plus braves, ils soumettraient la Gaule enti�re.

    Ce projet fut d�nonc� aux Helv�tes ; et, selon leurs coutumes, Org�torix fut mis dans les fers pour r�pondre � l'accusation. Le supplice du condamn� devait �tre celui du feu. Au jour fix� pour le proc�s, Org�torix fit para�tre au tribunal tous ceux qui lui �taient attach�s, au nombre de dix mille hommes ; il y r�unit aussi tous ses clients et ses d�biteurs dont la foule �tait grande : second� par eux, il put se soustraire au jugement. Les citoyens, indign�s de cette conduite, voulaient maintenir leur droit par les armes, et les magistrats rassemblaient la population des campagnes, lorsque Org�torix mourut. Il y a lieu de penser, selon l'opinion des Helv�tes, qu'il se donna lui-m�me la mort.

Pr�paratifs d'�migration des Helv�tes

    Cet �v�nement ne ralentit pas l'ardeur des Helv�tes pour l'ex�cution de leur projet d'invasion. Lorsqu'ils se croient suffisamment pr�par�s, ils incendient toutes leurs villes au nombre de douze, leurs bourgs au nombre de quatre cents et toutes les habitations particuli�res ; ils br�lent tout le bl� qu'ils ne peuvent emporter, afin que, ne conservant aucun espoir de retour, ils s'offrent plus hardiment aux p�rils. Chacun re�oit l'ordre de se pourvoir de vivres pour trois mois. Ils persuadent aux Rauraques, aux Tulinges et aux Latobices, leurs voisins, de livrer aux flammes leurs villes et leurs bourgs, et de partir avec eux. Ils associent � leur projet et s'adjoignent les Bo�ens qui s'�taient �tablis au-del� du Rhin, dans le Norique, apr�s avoir pris Nor�ia.

    Il n'y avait absolument que deux chemins par lesquels ils pussent sortir de leur pays : l'un par la S�quanie, �troit et difficile, entre le Jura et le Rh�ne, o� pouvait � peine passer un chariot ; il �tait domin� par une haute montagne, et une faible troupe suffisait pour en d�fendre l'entr�e ; l'autre, � travers notre Province, plus ais� et plus court, en ce que le Rh�ne, qui s�pare les terres des Helv�tes de celles des Allobroges, nouvellement soumis, est gu�able en plusieurs endroits, et que la derni�re ville des Allobroges. Gen�ve, est la plus rapproch�e de l'Helv�tie, avec laquelle elle communique par un pont. Ils crurent qu'ils persuaderaient facilement aux Allobroges, qui ne paraissaient pas encore bien fermement attach�s au peuple romain, de leur permettre de traverser leur territoire, ou qu'ils les y contraindraient par la force. Tout �tant pr�t pour le d�part, ils fixent le jour o� l'on doit se r�unir sur la rive du Rh�ne. Ce jour �tait le 5 avant les calendes d'avril, sous le consulat de L. Pison et de A. Gabinius.

C�sar s'appr�te � leur barrer le passage

    C�sar, apprenant qu'ils se disposent � passer par notre Province, part aussit�t de Rome, se rend � grandes journ�es dans la Gaule ult�rieure et arrive � Gen�ve. Il ordonne de lever dans toute la province le plus de soldats qu'elle peut fournir (il n'y avait qu'une l�gion dans la Gaule ult�rieure), et fait rompre le pont de Gen�ve. Les Helv�tes, avertis de son arriv�e, d�putent vers lui les plus nobles de leur cit�, � la t�te desquels �taient Namm�ios et Veruclo�tios, pour dire qu'ils avaient l'intention de traverser la province, sans y commettre le moindre dommage, n'y ayant pour eux aucun autre chemin, qu'ils le priaient d'y donner son consentement. C�sar, se rappelant que les Helv�tes avaient tu� le consul L. Cassius et repouss� son arm�e qu'ils avaient fait passer sous le joug, ne crut pas devoir leur accorder cette demande. Il ne pensait pas que des hommes pleins d'inimiti� pussent, s'ils obtenaient la permission de traverser la province, s'abstenir de violences et de d�sordres. Cependant, pour laisser aux troupes qu'il avait. command�es le temps de se r�unir, il r�pondit aux d�put�s qu'il y r�fl�chirait, et que, s'ils voulaient conna�tre sa r�solution, ils eussent � revenir aux ides d'avril.

    Dans cet intervalle, C�sar, avec la l�gion qu'il avait avec lui et les troupes qui arrivaient de la Province, �leva, depuis le lac L�man, que traverse le Rh�ne, jusqu'au mont Jura, qui s�pare la S�quanie de l'Helv�tie, un rempart de dix- neuf mille pas de longueur et de seize pieds de haut : un foss� y fut joint. Ce travail achev�, il �tablit des postes, fortifie des positions, pour repousser plus facilement les Helv�tes, s'ils voulaient passer contre son gr�. D�s que le jour qu'il avait assign� � leurs d�put�s fut arriv�, ceux-ci revinrent aupr�s de lui. Il leur d�clara que les usages et l'exemple du peuple romain lui d�fendaient d'accorder le passage � travers la Province, et que, s'ils tentaient de le forcer, il s'y opposerait. Les Helv�tes, d��us dans cette esp�rance, essaient de passer le Rh�ne, les uns sur des barques jointes ensemble et sur des radeaux faits dans ce dessein, les autres � gu�, � l'endroit o� le fleuve a le moins de profondeur, quelquefois le jour, plus souvent la nuit. Arr�t�s par le rempart, par le nombre et par les armes de nos soldats, ils renoncent � cette tentative.

Ils traversent le pays des S�quanes. Mesures de C�sar

    Il leur restait un chemin par la S�quanie, mais si �troit qu'ils ne pouvaient le traverser malgr� les habitants. N'esp�rant pas en obtenir la permission par eux-m�mes, ils envoient des d�put�s � l'H�duen Dumnorix, pour le prier de la demander aux S�quanes. Dumnorix, puissant chez eux par son cr�dit et par ses largesses, �tait en outre l'ami des Helv�tes, � cause de son mariage avec la fille de leur concitoyen Org�torix. Excit� d'ailleurs par le d�sir de r�gner, il aimait les innovations, et voulait s'attacher par des services un grand nombre de cit�s. Il consentit donc � ce qu'on lui demandait, et obtint des S�quanes que les Helv�tes traverseraient leur territoire : on se donna mutuellement des otages ; les S�quanes s'engag�rent � ne point s'opposer au passage des Helv�tes, et ceux-ci � l'effectuer sans violences ni d�g�ts.

    On rapporte � C�sar que les Helv�tes ont le projet de traverser les terres des S�quanes et des H�duens, pour se diriger vers celles des Santons, peu distantes de Toulouse, ville situ�e dans la province romaine. II comprit que, si cela arrivait, cette province serait expos�e � un grand p�ril, ayant pour voisins, dans un pays fertile et d�couvert, des hommes belliqueux, ennemis du peuple romain. Il confie donc � son lieutenant T. Labi�nus la garde du retranchement qu'il avait �lev�. Pour lui, il va en Italie � grandes journ�es, y l�ve deux l�gions, en tire trois de leurs quartiers d'hiver, aux environs d'Aquil�e, et prend par les Alpes le plus court chemin de 1a Gaule ult�rieure, � la t�te de ces cinq l�gions. L�, les Ceutrons, les Gra�oc�les et les Caturiges, qui s'�taient empar�s des hauteurs, veulent arr�ter la marche de son arm�e. II les repousse dans plusieurs combats, et se rend, en sept journ�es, d'Oc�lum, derni�re place de la province cit�rieure, au territoire des Voconces, dans la province ult�rieure ; de l� il conduit ses troupes dans le pays des Allobroges, puis chez les S�gusiaves. C'est le premier peuple hors de la province, au-del� du Rh�ne.

    D�j� les Helv�tes avaient franchi les d�fil�s et le pays des S�quanes ; et, arriv�s dans celui des H�duens, ils en ravageaient les terres. Ceux-ci, trop faibles pour d�fendre contre eux leurs personnes et leurs biens, d�putent vers C�sar, pour lui demander du secours : "Dans toutes les circonstances, ils avaient trop bien m�rit� du peuple romain pour qu'on laiss�t, presque � la vue de notre arm�e, d�vaster leurs champs, emmener leurs enfants en servitude, prendre leurs villes. Dans le m�me temps, les Ambarres, amis et alli�s des H�duens, informent �galement C�sar que leur territoire est ravag� et qu'ils peuvent � peine garantir leurs villes de la fureur de leurs ennemis. Enfin les Allobroges, qui avaient des bourgs et des terres au-del� du Rh�ne, viennent se r�fugier aupr�s de lui, et lui d�clarent qu'il ne leur reste rien que le sol de leurs champs. C�sar, d�termin� par ce concours de plaintes, crut ne devoir pas attendre que tous les pays des alli�s fussent ruin�s, et les Helv�tes arriv�s jusque dans celui des Santons.

Les Helv�tes passent la Sa�ne. D�faite des Tigurins

    La Sa�ne est une rivi�re dont le cours, entre les terres des H�duens et celles des S�quanes et jusqu'au Rh�ne, est si paisible que l'oeil ne peut en distinguer la direction. Les Helv�tes la passaient sur des radeaux et des barques jointes ensemble. C�sar, averti par ses �claireurs que les trois quarts de l'arm�e helv�te avaient d�j� travers� la Sa�ne, et que le reste �tait sur l'autre rive, part de son camp, � la troisi�me veille, avec trois l�gions, et atteint ceux qui n'avaient pas encore effectu� leur passage. Il les surprend en d�sordre, les attaque � l'improviste et en tue un grand nombre. Les autres prennent la fuite, et vont se cacher dans les for�ts voisines. Ils appartenaient au canton des Tigurins ; car tout le territoire de l'Helv�tie est divis� en quatre cantons. C'�taient ceux de ce canton qui, dans une excursion du temps de nos p�res, avaient tu� le consul L. Cassius et fait passer son arm�e sous le joug. Ainsi, soit effet du hasard, soit par la volont� des dieux immortels, cette partie des citoyens de l'Helv�tie, qui avait fait �prouver une si grande perte au peuple romain, fut la premi�re � en porter la peine. C�sar trouva aussi dans cette vengeance publique l'occasion d'une vengeance personnelle ; car l'a�eul de son beau-p�re, L. Pison, lieutenant de Cassius, avait �t� tu� avec lui par les Tigurins, dans la m�me bataille.

Ambassade de Divico

    Apr�s ce combat, C�sar, afin de poursuivre le reste des Helv�tes, fait jeter un pont sur la Sa�ne et la traverse avec son arm�e. Ceux-ci, effray�s de son arriv�e soudaine, et voyant qu'il lui avait suffi d'un seul jour pour ce passage qu'ils avaient eu beaucoup de peine � effectuer en vingt jours, lui envoient des d�put�s ; � la t�te de cette d�putation �tait Divico, qui commandait les Helv�tes � la d�faite de Cassius. Il dit � C�sar que, "si le peuple romain faisait la paix avec eux, ils se rendraient et s'�tabliraient dans les lieux que leur aurait assign�s sa volont� ; mais que, s'il persistait � leur faire la guerre, il e�t � se rappeler l'�chec pass� de l'arm�e romaine et l'antique valeur des Helv�tes ; que pour s'�tre jet� � l'improviste sur un seul canton, lorsque leurs compagnons, qui avaient pass� la rivi�re, ne pouvaient lui porter secours, il ne devait nullement attribuer cet avantage � son courage, ni concevoir du m�pris pour eux ; qu'ils avaient appris de leurs p�res et de leurs anc�tres � se fier � leur valeur plut�t qu'� la ruse et que d'avoir recours aux embuscades ; qu'il pr�t donc garde que ce lieu o� ils se trouvaient, marqu� par le d�sastre des Romains et la destruction de leur arm�e, n'en tir�t son nom et n'en transmit le souvenir � la post�rit�."

    � ce discours C�sar r�pondit "qu'il �tait loin d'avoir oubli� les choses que lui rappelaient les d�put�s helv�tes, et que son ressentiment en �tait d'autant plus vif que les Romains avaient moins m�rit� leur malheur ; que s'ils eussent pu se douter de quelque injure, il leur �tait facile de se tenir sur leurs gardes ; mais qu'ils avaient �t� surpris parce que, n'ayant rien fait qui d�t leur inspirer des craintes, ils ne pouvaient en concevoir sans motif. Quand m�me C�sar voudrait bien oublier cette ancienne injure, pourrait-il aussi effacer de son souvenir celles qui �taient r�centes ; les efforts qu'ils avaient faits pour traverser malgr� lui la province romaine, et leurs ravages chez les H�duens, chez les Ambarres, chez les Allobroges ? L'insolente vanit� qu'ils tiraient de leur victoire, et leur �tonnement de voir leurs outrages si longtemps impunis, lui d�montraient que les dieux immortels, afin de rendre, par un revers subit, un ch�timent plus terrible, accordent souvent � ceux-l� m�me qu'ils veulent punir des succ�s passagers et une plus longue impunit�. Quoi qu'il en soit, s'ils lui livrent des otages comme garants de leurs promesses, et s'ils donnent aux H�duens, � leurs alli�s et aux Allobroges, satisfaction du tort qu'ils leur ont fait, il consent � conclure avec eux la paix." Divico r�pondit "qu'ils tenaient de leurs p�res la coutume de recevoir des otages, et de n'en point donner ; que le peuple romain devait le savoir."

C�sar suit les Helv�tes. Combats d'arri�re-garde

    Apr�s cette r�ponse, il se retira. Le lendemain, ils l�vent leur camp ; C�sar en fait autant, et envoie en avant toute sa cavalerie, au nombre de quatre mille hommes, qu'il avait lev�s dans la province enti�re, chez les H�duens et chez leurs alli�s. Elle devait observer la direction que prendraient les ennemis. Cette cavalerie, ayant poursuivi leur arri�re-garde avec trop d'ardeur, en vint aux mains avec la cavalerie helv�te dans un lieu d�savantageux et �prouva quelque perte. Les Helv�tes, fiers d'avoir dans cette rencontre repouss� avec cinq cents chevaux un si grand nombre de cavaliers, nous attendirent plus hardiment, et nous inqui�t�rent quelquefois avec leur arri�re-garde. C�sar retenait l'ardeur de ses soldats, et se contentait pour le moment de s'opposer aux rapines, au pillage et aux d�vastations de l'ennemi. On fit route ainsi durant quinze jours, sans que l'arri�re-garde des Helv�tes f�t s�par�e de notre avant-garde de plus de cinq ou six mille pas.

Mauvaise volont� des H�duens. Diviciacos et Liscos d�noncent Dumnotrix

Cependant C�sar pressait chaque jour les H�duens de lui livrer le bl� qu'ils lui avaient promis ; car le climat froid de la Gaule, situ�e au nord, comme il a �t� dit pr�c�demment, faisait non seulement que la moisson n'�tait pas parvenue, dans les campagnes, � sa maturit�, mais que le fourrage m�me y �tait insuffisant ; quant au bl� qu'il avait fait charger sur la Sa�ne, il pouvait d'autant moins lui servir, que les Helv�tes s'�taient �loign�s de cette rivi�re, et il ne voulait pas les perdre de vue. Les H�duens diff�raient de jour en jour, disant qu'on le rassemblait, qu'on le transportait, qu'il �tait arriv�. Voyant que ces divers discours se prolongeaient trop, et touchant au jour o� il fallait faire aux soldats la distribution des vivres, C�sar convoqua les principaux H�duens, qui �taient en grand nombre dans le camp, entre autres Diviciacos et Liscos. Ce dernier occupait la magistrature supr�me que les H�duens appellent vergobret, fonctions annuelles et qui conf�rent le droit de vie et de mort. C�sar se plaint vivement � eux de ce que, ne pouvant acheter des vivres ni en prendre dans les campagnes, il ne trouve, dans un besoin si pressant et presque en pr�sence de l'ennemi, aucun secours dans des alli�s ; l'abandon o� ils le laissaient �tait d'autant plus coupable, que c'�tait en grande partie � leur pri�re qu'il avait entrepris la guerre.
"""


# building the corpus

RAW_TEXTS = (
    ('aquariophilie', A_TEXT),
    ('godel', G_TEXT),
    ('guerre', GG_TEXT),
)
CORPUS = ()
for corpus_name, text in RAW_TEXTS:
    paragraphs = text.split('\n\n')
    sentences = []
    for p in paragraphs:
        sentences += p.split('. ')
    sentences = tuple(sentences)
    CORPUS += ((corpus_name, sentences),)

class RandomContentGenerator(object):

    def __init__(self, usernames=USERNAMES, corpus=CORPUS,
                 email_pattern=EMAIL_PATTERN, portal=None):
        self._email_pattern = email_pattern
        self._usernames = usernames
        self._emails = tuple(self.makeEmail(name) for name in usernames)
        self._simple_emails = tuple(self.makeEmail(name, simple=True)
                                    for name in usernames)
        self._corpus = dict(corpus)
        self._corpus_indexes = dict((name, i )
                                    for i, (name, _) in enumerate(corpus))
        self._portal = portal

    def randomEmail(self, simple=False):
        if simple:
            return choice(self._simple_emails)
        else:
            return choice(self._emails)

    def randomEmails(self, n=None, simple=False):
        if n is None:
            n = randint(2, 5)
        if simple:
            return sample(self._simple_emails, n)
        else:
            return sample(self._emails, n)

    def randomSentence(self, corpus=None):
        if corpus is None:
            corpus = choice(corpus.keys())
        return choice(self._corpus[corpus])

    def randomWords(self, n=None, corpus=None):
        if n is None:
            n = randint(3, 10)
        return ' '.join(self.randomSentence(corpus=corpus).split()[:n])

    def randomParagrah(self, n=None, corpus=None):
        if n is None:
            n = randint(3, 10)
        return '. '.join(self.randomSentence(corpus=corpus) for _ in xrange(n))

    def randomText(self, n=3, corpus=None):
        return '\n\n'.join(self.randomParagrah(randint(3, 6), corpus=corpus)
                           for _ in xrange(n))

    def makeEmail(self, name, simple=False):
        email = self._email_pattern % '-'.join(toAscii(name).lower().split())
        if simple:
            return email
        else:
            return "%s <%s>" % (name, email)

    def choiceFromVoc(self, voc_name):
        voc = self._portal.portal_vocabularies[voc_name]
        return choice(voc.keys())

    def sampleFromVoc(self, voc_name, n=3, corpus=None):
        voc = self._portal.portal_vocabularies[voc_name]
        keys = voc.keys()
        k = len(keys)

        # if no corpus is specified, select from the whole keys
        if corpus is None:
            return sample(keys, min(n, k))

        # else split the list of subjects into equal parts, one for each piece
        # of corpus and select a sub list from that part
        i = float(self._corpus_indexes[corpus])
        d = len(self._corpus)
        return sample(keys[int(i/d*k):int((i+1)/d*k)], min(n, k))

    def randomCorpus(self):
        return choice(self._corpus.keys())


if __name__ == '__main__':
    from sys import argv
    from AccessControl.User import UnrestrictedUser as BaseUnrestrictedUser
    from AccessControl.SecurityManagement import newSecurityManager
    from Testing.makerequest import makerequest

    class UnrestrictedUser(BaseUnrestrictedUser):
        """Unrestricted user that still has an id."""
        def getId(self):
            """Return the ID of the user."""
            return self.getUserName()

    app = makerequest(app)

    if len(argv) == 1:
        rpath = 'cps'
        print "Inject Random Mails, no rpath specified."
    else:
        rpath = argv[1]
    print "Injecting random mails in %s" % rpath
    portal = app.unrestrictedTraverse(rpath)
    user = UnrestrictedUser('script', '', ['Manager'], '').__of__(portal)
    newSecurityManager(None, user)
    inject(portal)
