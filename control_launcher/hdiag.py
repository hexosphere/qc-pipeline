#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np

print ("Debut de l'execution du script hdiag.py")
print ('')


B=np.loadtxt("mime")

print ("MIME de depart (cm-1)")
print ('')
for i in B:
   for j in i:
    print (np.format_float_scientific(j,precision=10,unique=False,pad_left=2), end = " ")
   print ('')

print ('')
print ('Diagonalisation du MIME')
print ('')
   
A=np.linalg.eig(B)

eigenvalues=A[0]
eigenvectors=A[1]
transpose=np.transpose(eigenvectors)

ua=eigenvalues/219474.6313705
nm=10000000/eigenvalues
ev=eigenvalues/8065.6

print ('******    VALEURS ET VECTEURS PROPRES    ******')
print ('')

print("Valeurs propres (cm-1 / ua / eV / nm)")
for i in range(len(eigenvalues)):
	print ("% 12.5f || % 1.8e || % 10.6f || % 8.7f" % (eigenvalues[i],ua[i],ev[i],nm[i]))

np.savetxt('energies_cm-1',eigenvalues,fmt='%1.10e')
np.savetxt('energies_ua',ua,fmt='%1.10e',footer='comment',comments='#')
np.savetxt('energies_nm',nm,fmt='%1.10e')
np.savetxt('energies_ev',ev,fmt='%1.10e')

print ('')
print("Matrice des vecteurs propres")
print ('')
for i in eigenvectors:
   for j in i:
    print (np.format_float_scientific(j,precision=10,unique=False,pad_left=2), end = " ")
   print ('')
np.savetxt('mat_pto',eigenvectors,fmt='% 18.10e')
   
print ('')
print("Matrice transposee des vecteurs propres")
print ('')
for i in transpose:
   for j in i:
    print (np.format_float_scientific(j,precision=10,unique=False,pad_left=2), end = " ")
   print ('')
np.savetxt('mat_otp',transpose,fmt='% 18.10e')

print ('')
print ('******    MOMENTS DIPOLAIRES    ******')   
   
M=np.loadtxt("momdip")

print ('')
print("Matrice des moments dipolaires dans la base des etats d'ordre zero (ua)")
print ('')
for i in M:
   for j in i:
    print (np.format_float_scientific(j,precision=10,unique=False,pad_left=2), end = " ")
   print ('')
np.savetxt('momdip_0',M,fmt='% 18.10e')
   
O=np.dot(transpose,M)
for i in range(len(O)):
	for j in range(i):
		O[j,i]=O[i,j]
		
print ('')
print("Matrice des moments dipolaires dans la base des etats propres (ua)")
print ('')
for i in O:
   for j in i:
    print (np.format_float_scientific(j,precision=10,unique=False,pad_left=2), end = " ")
   print ('')
np.savetxt('momdip_p',O,fmt='% 18.10e')	

print ('')
print ('******    MATRICE DENSITE INITIALE   ******') 

print ('')
print("Creation du fichier de population initiale (fondamental, etats propres)")
dim = len(ua)
I = np.zeros((dim,dim),dtype=complex)
I[0,0]=1+0j
f = open("fondamental_1","w+")
for i in I:
   for j in i:
    print ('( {0.real:.2f} , {0.imag:.2f} )'.format(j), end = " ", file = f)
   print ('', file = f)
f.close()

print ('')
print("Creation des projecteurs")
print ('')
with open('etats') as file:
    tcount = 0
    for line in file:
        parts = line.split()
        if parts[1] == 'T':
            state = int(parts[0])
            print ("L'etat", state, "est un triplet. Preparation du projecteur correspondant.") 
            P = np.zeros((dim,dim),dtype=complex)
            P[state-1,state-1]=1+0j
            tcount = tcount + 1
            name = "projectorT" + str(tcount) + "_1"
            g = open(name,"w+")
            for i in P:
                for j in i:
                   print ('( {0.real:.2f} , {0.imag:.2f} )'.format(j), end = " ", file = g)
                print ('', file = g)
            g.close()
print(' ')
print("Tous les projecteurs ont ete crees")

print(' ')
print("Fin de l'execution du script hdiag.py")