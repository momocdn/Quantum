import pennylane as qml
from matplotlib import pyplot as plt
import pennylane as qml
from pennylane.tape import QuantumTape
from pennylane.operation import Operation
from pennylane.measurements import MeasurementProcess
from pennylane.transforms import create_expand_fn
from pennylane import numpy as np

# Liste des clauses
clause_list = [[0, 1],
               [0, 2],
               [1, 3],
               [2, 3]]

# Définir un appareil avec des noms de qubits
named_wires = ["v0", "v1", "v2", "v3", "c0", "c1", "c2", "c3", "out0"]  # Noms des qubits
sudoku_wires = ["v0", "v1", "v2", "v3"]
aux0_wire = ["out0"]
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

# Fonction qui construit le diffuseur de grover
def sudoku_diffuser():

    qml.broadcast(unitary=qml.Hadamard, pattern="single", wires=sudoku_wires)
    qml.broadcast(unitary=qml.PauliX, pattern="single", wires=sudoku_wires)
    qml.Hadamard(wires=["v3"])
    qml.MultiControlledX(wires=sudoku_wires, control_values=[1,1,1])
    qml.Hadamard(wires=["v3"])
    qml.broadcast(unitary=qml.PauliX, pattern="single", wires=sudoku_wires)
    qml.broadcast(unitary=qml.Hadamard, pattern="single", wires=sudoku_wires)

def iteration():
    
    # Ajouter l'oracle Sudoku
    sudoku_oracle(clause_list)

    # Ajouter diffuser grover
    sudoku_diffuser()

def initialisation():

    # initialisation du dernier qubit pour le mettre à l'état |->
    qml.PauliX(wires=aux0_wire)
    qml.Hadamard(wires=aux0_wire)

    # initialisation des qubits 'v' avec Hadamard
    qml.broadcast(unitary=qml.Hadamard, pattern="single", wires=sudoku_wires)
    

# Construire le circuit principal
@qml.qnode(dev)
def circuit():

    initialisation()
   
    # effectuer
    for i in range(2):
        iteration()
        qml.Barrier()

    # Retourner l'état complet
    # return qml.state()

    return qml.probs(wires=["v0", "v1", "v2", "v3"])

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


# Les portes de base de notre expansion
# Je triche ici en rajoutant RZ, RX, RY
# Mais c'est surement ok vu que ce qui nous intéresse au final c'est les CNOT
base_gates = ["T", "Adjoint(T)",
              "S", "Adjoint(S)",
              "SX", "Adjoint(SX)",
              "PauliX", "PauliY", "PauliZ",
              "Hadamard", "CNOT",
              "RZ", "RX", "RY"]


def decompose(tape: QuantumTape) -> QuantumTape:
    def stop_at(op: Operation):
        return op.name in base_gates

    # PennyLane create_expand_fn does the job for us
    custom_expand_fn = create_expand_fn(depth=9, stop_at=stop_at)
    tape = custom_expand_fn(tape)
    return tape


# Définir un device
# dev = qml.device("default.qubit")


# # Le noeud à expandre
# @qml.qnode(dev)
# def circuit():
#     qml.MultiControlledX([0, 1, 2, 3, 4, 5], [6])
#     return qml.probs()


# Une fonction utilitaire qui crée un noeud à partir d'un tape
# Il y a surement un meilleur moyen de faire ça, mais c'est ce que j'ai
@qml.qnode(dev)
def arbitrary_circuit(tape: QuantumTape, measurement=qml.counts):
    """
    Create a quantum function out of a tape and a default measurement to use (overrides the measurements in the tape)
    """
    for op in tape.operations:
        if len(op.parameters) > 0:
            qml.apply(op)
        else:
            qml.apply(op)

    def get_wires(mp: MeasurementProcess):
        return [w for w in mp.wires] if mp is not None and mp.wires is not None and len(mp.wires) > 0 else tape.wires

    # Retourner une liste de mesures si on a plusieurs mesures, sinon retourner une seule mesure
    return [measurement(wires=get_wires(meas)) for meas in tape.measurements] if len(tape.measurements) > 1 \
        else measurement(wires=get_wires(tape.measurements[0] if len(tape.measurements) > 0 else None))


# Exécuter le circuit, récupérer le tape, décomposer le tape
circuit()
tape = circuit.tape
tape = decompose(tape)

# Créer un circuit à partir du tape décomposé et récupérer les specs
specs = qml.specs(arbitrary_circuit)(tape)
resources = specs["resources"]

# Voilà le gate count
print("\n".join([f"{k} : {v}" for k, v in resources.gate_types.items()]))

