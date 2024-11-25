import pennylane as qml
from matplotlib import pyplot as plt
from pennylane import numpy as np
from collections import Counter

# Liste des clauses
clause_list = [[0, 1],
               [0, 2],
               [1, 3],
               [2, 3]]

# Définir un appareil avec des noms de qubits
named_wires = ["v0", "v1", "v2", "v3", "c0", "c1", "c2", "c3", "out0", "work"]  # Ajout du qubit de travail
dev = qml.device("default.qubit", wires=named_wires, shots=1000)  # Utilisation de plusieurs shots pour histogramme


# Fonction XOR utilisant deux portes CNOT
def XOR(a, b, output):
    qml.CNOT(wires=[a, output])
    qml.CNOT(wires=[b, output])


# Fonction pour construire l'oracle Sudoku
def sudoku_oracle(clause_list):
    # Vérifier chaque clause en appliquant XOR
    for i, clause in enumerate(clause_list):
        XOR(a=f"v{clause[0]}", b=f"v{clause[1]}", output=f"c{i}")  # Résultat XOR stocké dans les qubits de clause

    # Ajouter une porte (MC-Toffoli) pour vérifier toutes les clauses
    qml.MultiControlledX(wires=["c0", "c1", "c2", "c3", "out0"], work_wires=["work"])

    # Annuler les clauses pour réinitialiser les qubits de clause à leur état d'origine
    for i, clause in enumerate(clause_list):
        XOR(a=f"v{clause[0]}", b=f"v{clause[1]}", output=f"c{i}")  # Annule le XOR


# Fonction pour le diffuseur (diffusion)
def diffuser(variable_wires):
    # Appliquer les portes Hadamard à chaque qubit individuellement
    for wire in variable_wires:
        qml.Hadamard(wires=wire)

    for wire in variable_wires:
        qml.PauliX(wires=wire)

    # Appliquer une porte Z contrôlée sur tous les qubits
    qml.MultiControlledX(wires=[*variable_wires, "out0"], work_wires=["work"])

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
    for wire in ["v0", "v1", "v2", "v3"]:
        qml.Hadamard(wires=wire)

    # Première itération : Oracle et diffuseur
    sudoku_oracle(clause_list)  # Appliquer l'oracle Sudoku
    diffuser(["v0", "v1", "v2", "v3"])  # Appliquer le diffuseur

    # Deuxième itération : Oracle et diffuseur
    sudoku_oracle(clause_list)  # Appliquer à nouveau l'oracle Sudoku
    diffuser(["v0", "v1", "v2", "v3"])  # Appliquer le diffuseur

    # Retourner l'état complet
    return qml.sample(wires=["v0", "v1", "v2", "v3"])


# Dessiner le circuit
drawer = qml.draw(circuit)
print("Dessin du circuit :")
print(drawer())

# Exécuter le circuit et récupérer les mesures
samples = circuit()

# Convertir les résultats en une forme lisible
results = ["".join(map(str, sample)) for sample in samples]

# Compter les occurrences des résultats
counts = Counter(results)

# Afficher les résultats
print("\nRésultats des mesures :")
for state, count in counts.items():
    print(f"{state}: {count}")

# Créer un histogramme des résultats
plt.bar(counts.keys(), counts.values())
plt.xlabel("État mesuré")
plt.ylabel("Nombre d'occurrences")
plt.title("Histogramme des résultats mesurés")
plt.show()



