import pandas as pd
import numpy as np

# Lire le fichier CSV
data = pd.read_csv('Base1.csv', sep=';', encoding='ISO-8859-1')

# Corriger les valeurs de Type d'appel
data['Type d\'appel'] = data['Type d\'appel'].replace({'Appel planifi\x82': 'Appel planifié'})

# Identifier les colonnes de semaines (à partir de la 6ème colonne)
semaines_columns = data.columns[5:]

# Calculer le total des appels clients et des appels planifiés par famille
total_appels_clients = data[data['Type d\'appel'] == 'Appel'].groupby('Famille')[semaines_columns].sum()
total_appels_planifies = data[data['Type d\'appel'] == 'Appel planifié'].groupby('Famille')[semaines_columns].sum()

# Afficher les totaux pour vérification
print("Total Appels Clients:")
print(total_appels_clients)

print("\nTotal Appels Planifiés:")
print(total_appels_planifies)

# Calculer le load en évitant la division par zéro
load = np.where(total_appels_clients.values != 0, total_appels_planifies.values / total_appels_clients.values, 0)

# Convertir le résultat en DataFrame pour une meilleure visualisation
load_df = pd.DataFrame(load, index=total_appels_planifies.index, columns=total_appels_planifies.columns)

# Remplacer les NaN par 0
load_df = load_df.fillna(0)

# Afficher le résultat
print("\nLoad Calculé:")
print(load_df)
