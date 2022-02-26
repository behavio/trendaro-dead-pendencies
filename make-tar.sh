# path to setup.py
INSETUP="$1"

# output directory, where the tar.gz file will be created
OUTDIR="$2"

# fail if less than two arguments are given
if [ $# -lt 2 ]; then
    echo "Usage: $0 <path to setup.py> <output directory>"
    exit 1
fi

# change to the directory where the setup.py file is
# (some packages do local imports from the setup.py file)
PKGDIR=$(dirname $INSETUP)
pushd "$PKGDIR" >/dev/null

# get the package name and version from the setup.py file
PKGNAME=$(python setup.py --fullname)

# get back to the original directory, to OUTDIR makes sense
popd >/dev/null

# let tar change directory one level up from the setup.py file
# tar the package, excluding __pycache__ and .pyc files
tar czf "$OUTDIR/$PKGNAME.tar.gz" \
  --exclude=__pycache__ --exclude='*.pyc' --exclude=".eggs" \
  -C "$PKGDIR"/.. \
  "$(basename "$PKGDIR")"
