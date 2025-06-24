# 🚆 TARDIS - SNCF Train Delay Analysis

Analysis and prediction of SNCF train delays across France.

It is an *Epitech project*.

## 📋 Prerequisites

- Python ([Download Python](https://www.python.org/downloads/))
- pip (Python package manager)

## 🛠️ Installation

1. **Create the virtual environment**

   ```bash
   # Creation
   python3 -m venv env

   # Activation
   source env/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   This will install:
   - notebook
   - pandas
   - numpy 
   - matplotlib
   - seaborn
   - streamlit
   - joblib
   - scikit-learn
   - rapidfuzz
   - xgboost

## 📊 Usage

### 1. Exploratory Data Analysis (EDA)

To explore the data and visualizations:

```bash
jupyter notebook tardis_eda.ipynb
```

This notebook contains:
- Data cleaning
- Station validation
- Global statistics 
- Delay visualizations

### 2. Modeling

To see the creation of the predictive model:

```bash
jupyter notebook tardis_model.ipynb
```

This notebook presents:
- Data preparation
- Training of different models
- Performance evaluation
- Analysis of important features

### 3. Interactive Dashboard

To launch the web application:

```bash
streamlit run tardis_dashboard.py
```

## 📁 Project Structure

```
tardis/
├── dataset.csv                  # Raw data
├── cleaned_dataset.csv          # Cleaned data
├── liste-des-gares.csv          # Official list of stations
├── worldcities.csv              # Cities database
├── tardis_eda.ipynb             # Analysis notebook
├── tardis_model.ipynb           # Modeling notebook
├── tardis_dashboard.py          # Streamlit application
└── requirements.txt             # Python dependencies
```

## 🔍 Features

- Complete analysis of delays by station and period
- Prediction of future delays
- Interactive visualizations
- Web user interface

## 🐛 Troubleshooting

1. **"Module not found"**
   ```bash
   pip install -r requirements.txt
   ```

2. **"Jupyter not found"**
   ```bash
   pip install jupyter
   ```

3. **"Port already in use"**
   ```bash
   streamlit run tardis_dashboard.py --server.port 8502
   ```

## 📫 Support

If you have any issues:
1. Make sure the virtual environment is activated
2. Reinstall the dependencies
3. Make sure you are in the correct folder

## 🔗 References

**dataset.csv** is given by Epitech

- Data:
- [DATA LIST OF STATIONS](www.data.gouv.fr/fr/datasets/liste-des-gares/)
- [DATA LIST OF CITIES](simplemaps.com/data/world-cities)

## 👨‍💻 Author

```py
def Alexandro_Almeida():
    print("First-year project\n")
    print("Created by me and Mathis Loiseau\n")
    print("Thank you for reading the README :)\n")
```
