#!/usr/bin/env bash

testrargs=""
venv=${VENV:-.venv}
with_venv=tools/with_venv.sh
installvenvopts="--no-site-packages"
wrapper="${with_venv}"
tempest_home_dir=""

while [ $# -gt 0 ]; do
  case "$1" in
    -u|--update) update=1;;
    -t|--tempest-home*|--tempest-dir*)
        shift;
        tempest_home_dir=$1;;
    *) testrargs="$testrargs $1";;
  esac
  shift
done

function abort_venv_installation {
    echo ""
    echo "---- Abort venv Installation ----"
    echo ""
    echo "  Reason: Not at tempest directory."
    echo "  You need to run this script from tempest home directory."
    echo ""
    exit 1
}

function check_iam_at_tempest_dir {
    if [ ! -d tempest ]; then
        abort_venv_installation
    fi
    if [ ! -f requirements.txt ]; then
        abort_venv_installation
    fi
    if [ ! -f run_tempest.sh ]; then
        abort_venv_installation
    fi
    if [ ! -f tools/with_venv.sh ]; then
        abort_venv_installation
    fi
}

if [ ! "${tempest_home_dir}" == "" ]; then
    if [ -d ${tempest_home_dir} ]; then
        cd ${tempest_home_dir}
    else
        echo "tempest directory ${tempest_home_dir} does not exist, or not a directory."
        exit 1
    fi
fi

check_iam_at_tempest_dir

function install_venv {
      echo "Installing virtualenv..."
      virtualenv $installvenvopts $venv
      wrapper="${with_venv}"
      ${wrapper} pip install -U -r requirements.txt
}

function update_venv {
      echo "Updating virtualenv..."
      virtualenv $installvenvopts $venv
      $venv/bin/pip install -U -r requirements.txt
}

# install/update VENV
if [ ! -d $venv ]; then
    install_venv
else
    echo -e "Virtual environment found...update it? (Y/n) \c"
    read use_ve
    if [ "x$use_ve" = "xY" -o "x$use_ve" = "x" -o "x$use_ve" = "xy" ]; then
        update_venv
    fi
fi

# check vmware-nsx is installed!
nsx_tempest=$(tools/with_venv.sh pip show vmware-nsx 2>/dev/null | grep vmware-nsx-tempest-plugin)
echo ""
if [ -z "${nsx_tempest}" ]; then
    echo "--- Warning ---"
    echo "   vmware-nsx-tempest is not installed at tempest VENV environment."
    echo "   please goto VENV and install editable vmware-nsx master branch."
    echo "   Example steps, assume vmware-nsx is /opt/devtest/vmware-nsx:"
    echo ""
    echo "     source .venv/bin/active"
    echo "     pip install -e /opt/devtest/vmware-nsx/"
else
    echo "--- OK ---"
    echo "   You have vmware-nsx-tempest plugin installed."
fi
echo ""
