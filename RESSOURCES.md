# Ressources externes

Retour à l'[accueil](README.md) · Voir les [cours](cours/README.md) · Voir les [writeups](writeups/README.md)

Sélection courte et tenue de ressources qui servent réellement, classées par usage. Les annuaires
complets sont cités en fin de page : ils valent le détour, mais ils changent vite et personne ne
les relit.

## Apprendre

| Ressource | Ce qu'on y trouve |
| --- | --- |
| [pwn.college](https://pwn.college/) | programme universitaire complet, avec environnement d'entraînement |
| [PortSwigger Web Security Academy](https://portswigger.net/web-security) | cours web gratuits, labs intégrés, référence OWASP |
| [OverTheWire](https://overthewire.org/wargames/) | wargames progressifs, du shell à l'exploitation |
| [ROP Emporium](https://ropemporium.com/) | huit exercices ROP, du ret2win au stack pivot |
| [CryptoHack](https://cryptohack.org/) | cryptographie par la pratique, du classique à l'ECC |
| [pwntools-tutorial](https://github.com/Gallopsled/pwntools-tutorial) | chapitres officiels sur tubes, ELF, ROP, debugging |

## S'entraîner

| Plateforme | Format |
| --- | --- |
| [Hack The Box](https://www.hackthebox.com/) | machines, challenges, saisons |
| [TryHackMe](https://tryhackme.com/) | rooms guidées, parcours débutant |
| [Hackropole](https://hackropole.fr/) | archive officielle du FCSC, la référence francophone |
| [Root-Me](https://www.root-me.org/) | épreuves par catégorie, en français |
| [picoCTF](https://picoctf.org/) | compétition débutant, archives ouvertes |
| [VulnHub](https://www.vulnhub.com/) | machines virtuelles à télécharger, hors ligne |

## Outils

| Outil | Usage |
| --- | --- |
| [pwntools](https://github.com/Gallopsled/pwntools) | exploitation binaire, dialoguer avec une cible |
| [Ghidra](https://ghidra-sre.org/) | désassembleur et décompilateur, gratuit |
| [radare2 / rizin](https://rizin.re/) | analyse binaire en ligne de commande |
| [ROPgadget](https://github.com/JonathanSalwan/ROPgadget) | recherche de gadgets |
| [one_gadget](https://github.com/david942j/one_gadget) | adresses `execve("/bin/sh")` dans la libc |
| [libc-database](https://libc.rip/) | identifier une libc à partir d'une fuite |
| [CyberChef](https://gchq.github.io/CyberChef/) | encodages, chiffrements, analyse de données |
| [Wireshark](https://www.wireshark.org/) | analyse de trafic |
| [Burp Suite Community](https://portswigger.net/burp/communitydownload) | tests web |

## Références

| Référence | Contenu |
| --- | --- |
| [MITRE ATT&CK](https://attack.mitre.org/) | tactiques et techniques adverses, vocabulaire commun |
| [OWASP Top 10](https://owasp.org/www-project-top-ten/) | les dix risques web majeurs |
| [GTFOBins](https://gtfobins.github.io/) | binaires Unix détournables pour élever ses privilèges |
| [LOLBAS](https://lolbas-project.github.io/) | équivalent Windows |
| [HackTricks](https://book.hacktricks.xyz/) | aide-mémoire très large, à recouper |

## Annuaires complets

Trois listes de référence, avec leur licence — utile si tu veux en reprendre une partie :

| Dépôt | Licence | Contenu |
| --- | --- | --- |
| [apsdehal/awesome-ctf](https://github.com/apsdehal/awesome-ctf) | CC0-1.0 | frameworks, outils et ressources CTF |
| [vitalysim/Awesome-Hacking-Resources](https://github.com/vitalysim/Awesome-Hacking-Resources) | GPL-3.0 | outils et guides, très large |
| [enaqx/awesome-pentest](https://github.com/enaqx/awesome-pentest) | CC0-1.0 | tests d'intrusion, outils et lectures |

La licence compte : **CC0** autorise la reprise sans condition, la **GPL-3.0** impose de republier
sous GPL, ce qui est incompatible avec la CC BY-SA 4.0 de ce dépôt. D'où le choix de renvoyer par
lien plutôt que de recopier.

## Éthique

Toutes ces ressources supposent un cadre : CTF, plateforme d'entraînement, machine personnelle, ou
autorisation écrite. Une technique apprise ici ne s'applique pas sur un système qui ne
t'appartient pas.
