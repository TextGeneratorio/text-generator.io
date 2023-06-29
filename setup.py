import setuptools


# os.environ['TORCH_CUDA_ARCH_LIST']="3.5;3.7;6.1;7.0;7.5;8.6+PTX"

def setup_package():
    long_description = "textgenerator"
    setuptools.setup(
        name='textgenerator',
        version='0.0.1',
        description='textgenerator',
        long_description=long_description,
        long_description_content_type='text/markdown',
        author='lee penkman',
        license='MIT License',
        packages=setuptools.find_packages(
            exclude=['docs', 'tests', 'scripts', 'examples']),
        dependency_links=[
            'https://download.pytorch.org/whl/torch_stable.html',
        ],
        include_package_data=True,
        # also include the main.py file
        package_data={
            'textgenerator': ['main.py']
        },

        classifiers=[
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'Topic :: Scientific/Engineering :: Artificial Intelligence',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.7.10',
        ],
        keywords='text nlp machinelearning',
        install_requires=[
            'astroid==2.3.3',
            'Click==7.0',
            'colorama==0.4.3',
            'fastapi==0.75.1',
            'gunicorn==20.1.0',
            'h11==0.9.0',
            'isort==4.3.21',
            'lazy-object-proxy==1.4.3',
            'mccabe==0.6.1',
            'six==1.14.0',
            'uvicorn==0.17.0',
            'websockets==8.1',
            'wrapt==1.11.2',
            'transformers==4.19.2',
            'torch==1.11.0',
            'google-api-python-client==2.43.0',
            'google-api-core==1.31.5',
            'google-cloud-storage==2.3.0',
            'loguru==0.5.3',
            'pydantic==1.9.0',
            'jinja2==3.1.1',
            'nltk==3.7.0',
        ],
    )


if __name__ == '__main__':
    setup_package()
