# Sandbox image for quantum-domain experiments (Section 25/R).
FROM python:3.12-slim

RUN pip install --no-cache-dir \
    numpy==2.2.1 \
    qiskit==1.3.1 \
    qiskit-aer==0.15.1

RUN useradd --uid 1000 --create-home sandboxuser
WORKDIR /workspace
RUN chown sandboxuser:sandboxuser /workspace
USER sandboxuser

ENTRYPOINT ["python"]
