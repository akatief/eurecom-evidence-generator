# eurecom-evidence-generator
Repository for an evidence extraction pipeline from tabular data. Developed as a semester project at EURECOM.

## Setup
First, create a new virtual environment in the project directory and activate it
```python
python3 -m venv .env
source .env/bin/activate
```
Then, install all requirements
```python
pip install -r requirements.txt
pip install --no-deps feverous
```
## Usage
You can check that everything works by running examples/pipeline_main.py or alternatively generate your sentences directly on the following Google Colab notebook: [![Open In Colab](https://colab.research.google.com/github/akatief/eurecom-evidence-generator/blob/9cc56a4056860e2ee72f97ac3fe9a49cff297bff/examples/TENET_colab.ipynb)