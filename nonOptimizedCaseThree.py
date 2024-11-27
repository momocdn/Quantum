import pennylane as qml
from matplotlib import pyplot as plt
from pennylane import numpy as np
from collections import Counter

# Liste des clauses
clause_list = [[0, 1, 2],
               [3, 4, 5],
               [6, 7, 8],
               [0, 3, 6],
               [1, 4, 7],
               [2, 5, 8]]

sudoku_wires = ["v0", "v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8"]

clause_wires = ["c0", "c1", "c2", "c3", "c4", "c5"]


# Définir un appareil avec des noms de qubits
named_wires = sudoku_wires + clause_wires + ["out0", "work"]  # Ajout du qubit de travail
dev = qml.device("default.qubit", wires=named_wires, shots=1000)  # Utilisation de plusieurs shots pour histogramme


# Fonction XOR utilisant deux portes CNOT
def XOR(a, b, c, output):
    qml.CNOT(wires=[a, output])
    qml.CNOT(wires=[b, output])
    qml.CNOT(wires=[c, output])
    


# Fonction pour construire l'oracle Sudoku
def sudoku_oracle(clause_list):
    # Vérifier chaque clause en appliquant XOR
    for i, clause in enumerate(clause_list):
        XOR(a=f"v{clause[0]}", b=f"v{clause[1]}", c=f"v{clause[2]}", output=f"c{i}")  # Résultat XOR stocké dans les qubits de clause

    # Ajouter une porte (MC-Toffoli) pour vérifier toutes les clauses
    qml.MultiControlledX(wires=clause_wires + ["out0"], work_wires=["work"])

    # Annuler les clauses pour réinitialiser les qubits de clause à leur état d'origine
    for i, clause in enumerate(reversed(clause_list)):
       XOR(a=f"v{clause[2]}", b=f"v{clause[1]}", c=f"v{clause[0]}", output=f"c{5 - i}") # Annule le XOR


# Fonction pour le diffuseur (diffusion)
def diffuser(variable_wires):
    # Appliquer les portes Hadamard à chaque qubit individuellement
    for wire in variable_wires:
        qml.Hadamard(wires=wire)

    for wire in variable_wires:
        qml.PauliX(wires=wire)

    qml.Hadamard(wires=["v8"])

    # Appliquer une porte Z contrôlée sur tous les qubits
    qml.MultiControlledX(wires=sudoku_wires,control_values=[1,1,1,1,1,1,1,1])

    qml.Hadamard(wires=["v8"])

    for wire in variable_wires:
        qml.PauliX(wires=wire)

    # Réappliquer les portes Hadamard à chaque qubit individuellement
    for wire in variable_wires:
        qml.Hadamard(wires=wire)



# Construire le circuit principal
@qml.qnode(dev)
def circuit():
    # Initialiser le qubit de sortie `out0` dans l'état |->.
    qml.PauliX(wires="out0")
    qml.Hadamard(wires="out0")

    # Initialiser les qubits de variables avec des portes Hadamard
    for wire in sudoku_wires:
        qml.Hadamard(wires=wire)

    for i in range(4) :
        # Première itération : Oracle et diffuseur
        sudoku_oracle(clause_list)  # Appliquer l'oracle Sudoku
        diffuser(sudoku_wires)  # Appliquer le diffuseur
    
    # Retourner l'état complet
    # return qml.sample(wires=sudoku_wires)
    return qml.probs(wires=sudoku_wires)

# print(circuit())

# Exécuter le circuit et récupérer les mesures
proba_list = circuit()
etat_list = []

# Afficher les résultats
print("\nRésultats des mesures :")
for i in range(len(proba_list)) :
    etat_list.append(bin(i))
    print(etat_list[i] + " : " + str(proba_list[i]))

# Dessiner le circuit
drawer = qml.draw(circuit)
print("Dessin du circuit :")
print(drawer())

# Créer un histogramme des résultats
plt.bar(etat_list, proba_list)
plt.xlabel("État mesuré")
plt.ylabel("Nombre d'occurrences")
plt.title("Histogramme des résultats mesurés")
plt.show()
