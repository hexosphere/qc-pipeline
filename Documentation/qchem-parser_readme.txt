1) GoSam / Deneb => generation .xyz   structure initiale de la molecule
2) Orca => prend le .xyz en input et donne un new .xyz optimisé
3) Q-CHEM => prend le .xyz optimisé et sort un fichier .out
4) script de generation de matrice => mime, momdip, etats
5) hdiag.py + prepare-controle.sh + QOCT-RA => prend les matrices en input et genere les fichier + jobs PBS

Python libs:
- python 3.6
- numpy

.out = output du prg de calcul Q-CHEM
doivent etre un input pour le prg suivant


input = .out
output => mime (matrice), momdip (matrice), etats (liste 2col)
d'office matrice carrées et symetriques
par defaut 9x9
mais taille dynamique s'il trouve :
NRoots was altered as:  4 -->  9
par def: 4S + 4T + 0  => 9 x 9
=> 9S + 9T + 0   => 19 x 19

===
Lexique:
SOC = SPIN-ORBIT COUPLING
mime= Matrix image of the molecule
===


===========
tableau preparatif:
chercher:
"---------------------------------------------------
         TDDFT/TDA Excitation Energies              
---------------------------------------------------"
-> n° etat
-> energy etat eV ou "au"
-> Multiplicity
-> multiplicity order per name (1st, 2nd..; of the Triplets i.e.)
============


====
etats   (fin du fichier) => parsing tableau preparatif
----
start à 1 pas à 0 !!    mais 9 lignes par defaut
1	S	!!!!
2	T
3	T
4	S
...
----
chercher:
---------------------------------------------------
         TDDFT/TDA Excitation Energies
 ---------------------------------------------------
====



====
mime (matrice) - juste besoin des chiffres !! label explicité dans un fichier mime.debug
----
diag = energy value (eV/au)    / Ar[0][0] = 0   Ar[n][n] = x
CHERCHER : "Total SOC between the singlet ground state and excited triplet states" => S0 (Ar[0][0]) <> Tn
"Total SOC between the S1 state and excited triplet states:"
"Total SOC between the S3 state and excited triplet states:"

!! pas de value pour les singlets entre eux !!  => 0.0

ex:
"Total SOC between the T1 state and excited triplet states:"
T2      104.519613    cm-1
T3      104.525552    cm-1
T4      0.202028    cm-1
T5      0.311154    cm-1
T6      0.306091    cm-1
T7      28.222882    cm-1
T8      6.711935    cm-1
T9      27.534236    cm-1
(vide)

====



====
momdip
----
Tableaux a parser:
- "Transition Moments Between Ground and Triplet Excited States"
- "Transition Moments Between Triplet Excited States"
- "Transition Moments Between Ground and Singlet Excited States"
- "Transition Moments Between Singlet Excited States"

Colonnes à parser: 
- 2 colonnes "states" ==> indices
- Strength ==> valeur à l'indice [x][y]
- diag => 0

delimiteur tableau "--------------------------------------------------------------------------------"


ex:
                Transition Moments Between Ground and Triplet Excited States
 --------------------------------------------------------------------------------
    States   X          Y          Z           Strength(a.u.)
 --------------------------------------------------------------------------------
    0    1   0.000000   0.000000   0.000000              0
    0    2   0.000000   0.000000   0.000000              0
    0    3   0.000000   0.000000   0.000000              0
    0    4   0.000000   0.000000   0.000000              0
    0    5   0.000000   0.000000   0.000000              0
    0    6   0.000000   0.000000   0.000000              0
    0    7   0.000000   0.000000   0.000000              0
    0    8   0.000000   0.000000   0.000000              0
    0    9   0.000000   0.000000   0.000000              0
 --------------------------------------------------------------------------------

====


