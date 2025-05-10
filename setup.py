from setuptools import setup, find_packages

setup(
    name="educational_content_pipeline",
    version="0.1.0",
    author="[Your Name]",
    author_email="[Your Email]",
    description="A library for processing educational content, extracting concepts, and generating structured data.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="[Your Repository URL]",
    packages=find_packages(exclude=["tests*", "examples*"]),
    install_requires=[
        "python-docx",
        "moviepy",
        "google-generativeai",
        "dashscope",  # Included as it was in the original script
        "requests",
        "beautifulsoup4", # For ImageExtractFromPdf.py, though not directly used in provided snippet
        "wikipedia-api",
        "openai",       # For TTS and potentially other models
        "setuptools"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License", # Choose your license
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)