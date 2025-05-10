# MEduKG-Python-Library
This is a fully automated Python Library for constructing multimodal educational knowledge graphs. All you need to do is configure the large language model with its official API Key, as well as the paths to video and PDF lecture materials, to automatically build a multimodal educational knowledge graph covering four modalities: text, images, audio, and video.

We have already used this Python Library to build a multimodal educational knowledge graph covering natural science subjects for middle and high school education, available at https://aaa.com .

For ease of use, please read the following usage rules in detail.

## Features

- Video to audio conversion
- Text extraction from video (transcripts)
- Semantic segmentation of text using LLMs
- Video clipping based on timestamps
- Named Entity Recognition (NER) for educational concepts
- Concept explanation generation using Wikipedia and LLMs
- Image extraction from PDFs
- Image-concept alignment using multimodal LLMs
- Speech synthesis for explanations
- Generation of structured JSON data for concepts, knowledge points, and images
- Creation of RDF-like triples

## Installation

```bash
pip install -r requirements.txt
python setup.py install
```

## Directory Structure
```code
educational_content_pipeline/
├── educational_content_pipeline/
│   ├── __init__.py
│   ├── config.py
│   ├── dataprocess/
│   │   ├── __init__.py
│   │   ├── audio_video.py
│   │   ├── text_extraction.py
│   │   └── llm_segmentation.py
│   ├── ner/
│   │   ├── __init__.py
│   │   ├── extractor.py
│   │   └── prompts.py
│   ├── enrichment/
│   │   ├── __init__.py
│   │   ├── conceptnet_api.py
│   │   ├── translation.py
│   │   ├── wikipedia_api.py
│   │   └── explanation_generator.py
│   ├── multimodal/
│   │   ├── __init__.py
│   │   ├── image_analysis.py
│   │   ├── speech_synthesis.py
│   │   └── pdf_processing.py
│   ├── structuring/
│   │   ├── __init__.py
│   │   └── json_operations.py
│   ├── triplestore/
│   │   ├── __init__.py
│   │   └── triple_generator.py
│   └── utils/
│       ├── __init__.py
│       ├── api_client.py
│       └── file_operations.py
├── tests/
│   └── (test files would go here)
├── README.md
├── requirements.txt
└── setup.py
```
## Future Work
We will formally release this Python Library to the open-source community after refinement.
