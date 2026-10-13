# Sandbox image for cybersecurity + PQC-domain experiments (Section 24/29/Q/S).
# network_mode=none is enforced by the executor regardless of image
# contents, so generated "cybersecurity experiments" cannot reach any
# external system (Rule 7).
FROM python:3.12-slim

RUN pip install --no-cache-dir \
    numpy==2.2.1 \
    pandas==2.2.3 \
    scikit-learn==1.6.0 \
    scapy==2.6.1 \
    cryptography==44.0.0 \
    networkx==3.4.2

RUN useradd --uid 1000 --create-home sandboxuser
WORKDIR /workspace
RUN chown sandboxuser:sandboxuser /workspace
USER sandboxuser

ENTRYPOINT ["python"]
