from setuptools import setup, find_packages

setup(
    name='purecpp_huggingface_embedding',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'transformers',
        'sentence-transformers',
        'torch',
    ],
    author='PureCpp',
    author_email='',
    description='A Python package for generating text embeddings using Hugging Face models.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='',
)
