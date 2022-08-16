#!/bin/bash

STAGE3_NAME=${STAGE3_NAME:-riscv-buildbot-0}
MACHINES_PATH="${MACHINES_PATH:-/var/lib/machines}"
stage3_path="${MACHINES_PATH}/${STAGE3_NAME}"

STAGE3_MIRROR="${STAGE3_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/gentoo}"
STAGE3_ARCH="${STAGE3_ARCH:-riscv}"
STAGE3_PROFILE="${STAGE3_PROFILE:-rv64_lp64d-systemd}"
latest_stage3_name="$(curl -sL ${STAGE3_MIRROR}/releases/${STAGE3_ARCH}/autobuilds/latest-stage3-rv64_lp64d-systemd.txt | tail -1 | awk '{print $1}')"
latest_stage3_url="${STAGE3_MIRROR}/releases/${STAGE3_ARCH}/autobuilds/${latest_stage3_name}"

create_nspawn_image() {
    if [ ! -d "$stage3_path" ]; then
        machinectl pull-tar --verify=no ${latest_stage3_url} ${STAGE3_NAME}
    fi
}

sync_etc_portage_dir() {
    if [ ! -f "$stage3_path/etc/portage/bashrc" ]; then
        cp -r riscv64/etc/portage "${stage3_path}/etc"
        local proc_num=$(nproc)
        echo "MAKEOPTS=\"-j$proc_num\"" >> "$stage3_path/etc/portage/make.conf"
        echo "EMERGE_DEFAULT_OPTS=\"--jobs 10 --load-average $proc_num\"" >> "$stage3_path/etc/portage/make.conf"
    fi
}

download_qemu_static() {
    local file_path="${stage3_path}/opt/bin/qemu-riscv64"
    if [ ! -f "$file_path" ]; then
        mkdir -p "${stage3_path}/opt/bin/"
        # TODO : get github latest release
        local qemu_latest_version="v7.0.0-7"
        wget --output-document "$file_path" "https://github.com/multiarch/qemu-user-static/releases/download/${qemu_latest_version}/qemu-riscv64-static"
        chmod +x "$file_path"
    fi

    eval "$file_path --version"
}

clone_main_tree() {
    local main_tree="${stage3_path}/var/db/repos/gentoo"
    mkdir -p "$main_tree"
    pushd "$main_tree"
    if ! git rev-parse --is-inside-work-tree &> /dev/null ; then
        git clone --depth=1 https://github.com/gentoo-mirror/gentoo.git .
    fi
    popd
}

chroot_cmd="systemd-nspawn --quiet -D ${stage3_path} --bind=/var/cache/distfiles"
_chroot_eval() {
    echo -e "\n${@}"
    eval "$chroot_cmd ${@}"
}

run_emerge() {
    local opts=(
        --verbose
        --noreplace
        --update
        --deep
        --newuse
        --keep-going
        --autounmask-write y
        --autounmask-continue y
        --autounmask-use y
    )
    _chroot_eval "emerge ${opts[@]} $@"
}

emerge_install_git() {
    local pakcages=(
        dev-vcs/git
    )
    run_emerge "${pakcages[@]}"
}

emerge_update() {
    _chroot_eval "emerge --sync"

    local pakcages=(
        @world
    )
    run_emerge "${pakcages[@]}"
}

emerge_install_packages() {
    local pakcages=(
        app-portage/eix
        app-portage/flaggie
        app-portage/genlop
        app-portage/gentoolkit
        app-portage/iwdevtools
        app-portage/nattka
        app-portage/pkg-testing-tools
        app-portage/portage-utils
        app-portage/tatt
        app-text/tree
        app-text/wgetpaste
        dev-lang/rust-bin
        dev-util/buildbot-worker
        dev-util/debugedit
        dev-util/pkgcheck
        dev-util/pkgdev
        dev-vcs/git
        sys-apps/ripgrep
    )
    run_emerge "${pakcages[@]}"
}

create_nspawn_image
sync_etc_portage_dir
clone_main_tree
download_qemu_static

emerge_install_git
emerge_update
emerge_install_packages

#_chroot_eval
