# GAIA 

# Structure du Projet

```text
GAIA/
├── app/
│   ├── __init__.py        
│   ├── db.py              
│   ├── models.py          
│   ├── routes/
│   │   ├── main.py     
│   │   └── auth.py
│   ├── static/   
│   │   ├── css
│   │   │   ├── index.css
│   │   │   └── login.css
│   │   ├──Logo.png
│   └── templates/ 
│       ├── index.html
│       ├── login.html
│       └── register.html
├── docs/
│   ├── PERSONAS/          
│   ├── USERSTORIES.md     
│   ├── UML.png            
│   └── fiche_projet_GAIA.pdf
├── tests/
│   └── test_db.py         
├── run.py                 
├── requirements.txt       
└── .env/ 
```
# Lancer le projet 

```text
git clone  https://github.com/LSINC1509-Projet4/GAIA.git
cd GAIA
source .env/bin/activate
python install -r requirements.txt
```
Si pas de base de donnée active 
```text 
python -m test.test_db
```