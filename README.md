# TENET: TExtual traiNing Examples from daTa
Repository for TENET, an evidence extraction pipeline from tabular data. Developed as a semester project at EURECOM under the supervision of Professor Paolo Papotti. TENET implements various heuristics to retrieve data from the FEVEROUS dataset as well as transformer-based tasks to construct meaningful sentences from this data.

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
You can check that everything works by running examples/pipeline_main.py or alternatively generate your sentences directly on the following Google Colab notebook: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/akatief/eurecom-evidence-generator/blob/develop/examples/TENET_colab.ipynb)
