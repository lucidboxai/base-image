#!/bin/false

# Ubuntu 24.04 ships a default 'ubuntu' user/group at UID/GID 1000, which
# collides with the ai-dock runtime user (also UID/GID 1000) and makes its
# useradd fail. Remove it so UID/GID 1000 is free. (No-op on 22.04.)
userdel -r ubuntu 2>/dev/null || true
groupdel ubuntu 2>/dev/null || true

groupadd -g 1111 ai-dock
chown root.ai-dock /opt
chmod g+w /opt
chmod g+s /opt

mkdir -p /opt/environments/{python,javascript}

dpkg --add-architecture i386
apt-get update
apt-get upgrade -y --no-install-recommends

# System packages
$APT_INSTALL \
    acl \
    apt-transport-https \
    apt-utils \
    bc \
    build-essential \
    bzip2 \
    ca-certificates \
    cmake \
    curl \
    dnsutils \
    dos2unix \
    fakeroot \
    ffmpeg \
    file \
    fonts-dejavu \
    fonts-freefont-ttf \
    fonts-ubuntu \
    fuse3 \
    git \
    git-lfs \
    gnupg \
    gpg \
    gzip \
    htop \
    inotify-tools \
    jq \
    language-pack-en \
    less \
    libcap2-bin \
    libelf1 \
    libgl1 \
    libglib2.0-0 \
    libtcmalloc-minimal4 \
    locales \
    lsb-release \
    lsof \
    man \
    plocate \
    net-tools \
    nano \
    openssh-server \
    pkg-config \
    psmisc \
    python3-full \
    python3-pip \
    python3-venv \
    rclone \
    rsync \
    screen \
    software-properties-common \
    sox \
    ssl-cert \
    sudo \
    supervisor \
    tmux \
    tzdata \
    unar \
    unrar \
    unzip \
    vim \
    wget \
    xz-utils \
    zip \
    zstd
    
ln -sf $(ldconfig -p | grep -Po "libtcmalloc_minimal.so.\d" | head -n 1) \
        /lib/x86_64-linux-gnu/libtcmalloc.so

# Ensure deadsnakes is available for Python versions not included with base distribution
add-apt-repository ppa:deadsnakes/ppa
apt update
  
locale-gen en_US.UTF-8

# Install
# Use the distribution default python3 (3.12 on Ubuntu 24.04) for the
# serviceportal venv. python3-full / python3-venv are installed above.
python3 -m venv "$SERVICEPORTAL_VENV"
"$SERVICEPORTAL_VENV_PIP" install \
    --no-cache-dir -r /opt/ai-dock/fastapi/requirements.txt

# Get Cloudflare daemon — pinned to a verified version.
# Cloudflare does not publish a checksums file in their GitHub releases, so
# the SHA256 is hardcoded here. To bump CLOUDFLARED_VERSION, compute the new
# hash with:
#   curl -fsSL https://github.com/cloudflare/cloudflared/releases/download/<VER>/cloudflared-linux-amd64.deb | sha256sum
# then update both CLOUDFLARED_VERSION and CLOUDFLARED_SHA256 below.
CLOUDFLARED_VERSION="2026.5.0"
CLOUDFLARED_SHA256="0173a478774c635e577ef1eaa5a49af88d09d2d69b4a3e46f7033598f68f6521"
wget -c -O cloudflared.deb "https://github.com/cloudflare/cloudflared/releases/download/${CLOUDFLARED_VERSION}/cloudflared-linux-amd64.deb"
echo "${CLOUDFLARED_SHA256}  cloudflared.deb" | sha256sum -c -
dpkg -i cloudflared.deb
rm cloudflared.deb

# Prepare environment for running SSHD
chmod 700 /root
mkdir -p /root/.ssh
chmod 700 /root/.ssh
touch /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

# Remove less relevant parts of motd
rm -f /etc/update-motd.d/10-help-text

# Ensure critical paths/files are present
mkdir -p --mode=0755 /etc/apt/keyrings
mkdir -p --mode=0755 /run/sshd
chown -R root.ai-dock /var/log
chmod -R g+w /var/log
chmod -R g+s /var/log
mkdir -p /var/log/supervisor
mkdir -p /var/empty
mkdir -p /etc/rclone
touch /etc/rclone/rclone.conf

# Install SyncThing to enable transport between local machine and cloud instance

export SYNCTHING_VERSION="$(curl -fsSL "https://api.github.com/repos/syncthing/syncthing/releases/latest" \
            | jq -r '.tag_name' | sed 's/[^0-9\.\-]*//g')"
env-store SYNCTHING_VERSION

SYNCTHING_URL="https://github.com/syncthing/syncthing/releases/download/v${SYNCTHING_VERSION}/syncthing-linux-amd64-v${SYNCTHING_VERSION}.tar.gz"
SYNCTHING_SUMS_URL="https://github.com/syncthing/syncthing/releases/download/v${SYNCTHING_VERSION}/sha256sum.txt.asc"
mkdir /opt/syncthing/
wget -O /opt/syncthing.tar.gz "$SYNCTHING_URL"
# Verify against sha256sum.txt.asc in the same release. The file is
# PGP-clearsigned, but grep for the specific filename only matches the hash
# line (not the PGP armor blocks). We don't verify the signature itself —
# pinning syncthing's signing key is more maintenance than the threat model
# warrants for a developer image.
SYNCTHING_EXPECTED_SHA="$(curl -fsSL "$SYNCTHING_SUMS_URL" \
    | grep "syncthing-linux-amd64-v${SYNCTHING_VERSION}.tar.gz$" \
    | awk '{print $1}')"
if [[ -z "$SYNCTHING_EXPECTED_SHA" ]]; then
    echo "Failed to extract syncthing SHA256 for v${SYNCTHING_VERSION}" >&2
    exit 1
fi
echo "${SYNCTHING_EXPECTED_SHA}  /opt/syncthing.tar.gz" | sha256sum -c -
(cd /opt && tar -zxf syncthing.tar.gz -C /opt/syncthing/ --strip-components=1)
rm -f /opt/syncthing.tar.gz
if [[ -f /opt/syncthing/syncthing ]]; then
    ln -s /opt/syncthing/syncthing /opt/ai-dock/bin/syncthing
else
    echo "Failed to fetch syncthing. Exiting build"
    exit 1
fi
# Install node version manager and latest nodejs
export NVM_DIR=/opt/nvm
env-store NVM_DIR
git clone https://github.com/nvm-sh/nvm.git "$NVM_DIR"
(cd "$NVM_DIR" && git checkout `git describe --abbrev=0 --tags --match "v[0-9]*" $(git rev-list --tags --max-count=1)`)
source $NVM_DIR/nvm.sh
nvm install $NODE_VERSION
nvm alias default $NODE_VERSION

# Ensure correct environment for child builds
printf "source %s/nvm.sh\n" "$NVM_DIR" >> /opt/ai-dock/etc/environment.sh
printf "source %s/bash_completion\n" "$NVM_DIR" >> /opt/ai-dock/etc/environment.sh
printf "source /opt/ai-dock/etc/environment.sh\n" >> /etc/profile.d/02-ai-dock.sh
printf "source /opt/ai-dock/etc/environment.sh\n" >> /etc/bash.bashrc
printf "ready-test\n" >> /root/.bashrc

# Give our runtime user full access (added to ai-dock group)
/opt/ai-dock/bin/fix-permissions.sh -o container