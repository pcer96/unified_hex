from setuptools import setup, find_packages

setup(
    name="harvest-experiment-analysis",
    version="1.0.0",
    description="Centralized experiment analysis library for Harvest Hex notebooks",
    author="Your Team",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "plotly",
        "scipy",
        "slack-sdk",
        "kaleido",
        # Add other dependencies from your current notebook
    ],
    python_requires=">=3.8",
)
