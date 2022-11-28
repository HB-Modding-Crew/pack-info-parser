# pack-info-parser

## Mise en route:

```sh
cp config/default/config.json config/config.json
```

Dans config.json, modifier la valeur output pour qu'elle corresponde à votre dossier resource pack.

```
{
    "output_path": "./output/"
}
```

Installer les requirments.

```
pip install -r requirements.txt
```

Analyse sans réparations:
```
python3 main.py analyse -p <pathToPack>
```
Réparation de pack:
```
python3 main.py repair -p <pathToPack>
```
Ajout des commentaires (commandes de gives) dans les fichiers:
```
python3 main.py comment -p <pathToPack>
```

