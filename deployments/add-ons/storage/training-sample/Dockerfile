FROM public.ecr.aws/kubeflow-on-aws/notebook-servers/jupyter-tensorflow:2.6.0-cpu-py38

COPY training.py /
ENTRYPOINT ["python", "/training.py"]