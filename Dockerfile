FROM registry.access.redhat.com/ubi8/python-38

USER 0

# Red Hat certificates
RUN wget https://password.corp.redhat.com/RH-IT-Root-CA.crt \
         -O /etc/pki/ca-trust/source/anchors/RH-IT-Root-CA.crt && \
    update-ca-trust extract

# Requires git-core to clone github.com/openshift/cincinnati-graph-data
# Already included in recent UBI images
# RUN dnf install -y git-core

# Source code
COPY . /tmp/src
RUN /usr/bin/fix-permissions /tmp/src
USER 1001

# Use pipfile and update pip/setuptools
ENV ENABLE_PIPENV 1
ENV UPGRADE_PIP_TO_LATEST 1

# Install the dependencies
RUN /usr/libexec/s2i/assemble

# Entrypoint
ENV APP_FILE cluster_support_bot/__init__.py

# Set the default command for the resulting image
CMD /usr/libexec/s2i/run
