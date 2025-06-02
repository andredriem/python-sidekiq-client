from setuptools import setup, find_packages

setup(
    name="python-sidekiq-client",
    version="0.1.0",
    description="Python client for enqueuing jobs to Sidekiq-compatible queues",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="André Driemeyer",
    url="https://github.com/andredriem/python-sidekiq-client",
    packages=find_packages(),
    install_requires=["redis>=4.0"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)