# Sandbox image for AI-domain experiments (Section 23/P).
# Package set is pinned and vetted here; generated code cannot pip install
# arbitrary packages at run time (Section 18/57) - new packages require a
# reviewed rebuild of this image, not an ad-hoc install.
FROM python:3.12-slim

RUN pip install --no-cache-dir \
    numpy==2.2.1 \
    pandas==2.2.3 \
    scikit-learn==1.6.0 \
    scipy==1.14.1 \
    xgboost==2.1.3

RUN useradd --uid 1000 --create-home sandboxuser
WORKDIR /workspace
RUN chown sandboxuser:sandboxuser /workspace
USER sandboxuser

ENTRYPOINT ["python"]
