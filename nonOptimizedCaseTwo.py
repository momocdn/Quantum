import pennylane as qml
from pennylane import numpy as np

# Liste des clauses
clause_list = [[0, 1],
               [0, 2],
               [1, 3],
               [2, 3]]

# Définir un appareil avec des noms de qubits
named_wires = ["v0", "v1", "v2", "v3", "c0", "c1", "c2", "c3", "out0"]  # Noms des qubits
dev = qml.device("default.qubit", wires=named_wires)

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
    qml.MultiControlledX(wires=["c0", "c1", "c2", "c3", "out0"], work_wires=["v0"])

    # Annuler les clauses pour réinitialiser les qubits de clause à leur état d'origine
    for i, clause in enumerate(clause_list):
        XOR(a=f"v{clause[0]}", b=f"v{clause[1]}", output=f"c{i}")  # Annule le XOR

# Construire le circuit principal
@qml.qnode(dev)
def circuit():
    # Ajouter l'oracle Sudoku
    sudoku_oracle(clause_list)

    # Retourner l'état complet
    return qml.state()

# Dessiner le circuit
drawer = qml.draw(circuit)
print(drawer())
