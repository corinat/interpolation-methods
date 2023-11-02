#!/bin/bash
set -e
mkdir -p /root/.ssh/
echo "$SSH_PRIVATE_KEY" | base64 -d > /root/.ssh/q_gitlab
echo "$SSH_PUBLIC_KEY" | base64 -d  > /root/.ssh/q_gitlab.pub
chmod 400 /root/.ssh/q_gitlab
chmod 400 /root/.ssh/q_gitlab.pub
touch /root/.ssh/known_hosts
ssh-keyscan gitlab.com >> /root/.ssh/known_hosts
echo "PermitRootLogin yes" >> /root/.ssh/sshd_config
echo "IdentityFile ~/.ssh/q_gitlab" >> /root/.ssh/ssh_config
echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config
git config --global user.email "$GITLAB_USER_EMAIL"
git config --global user.name "$GITLAB_USER_NAME"
git config --global --add safe.directory /usr/src/app
eval `ssh-agent -s`
ssh-add /root/.ssh/q_gitlab
ssh-add -l
echo "host all all all $POSTGRES_HOST_AUTH_METHOD" >> pg_hba.conf
if [ $# -gt 0 ]; then
    # If arguments were passed, run them as additional commands
    exec "$@"
fi