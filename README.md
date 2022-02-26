# trendaro-dead-pendencies
A monorepo with all obscure packages surrounding the `matl-is-core`.

GitHub's `Releases` host packages for `pip install`.

As many of the packages are depending on eg `django-chamber`, update to one
usually means releasing all, otherwise pip calls out dependency mismatch.

# create a new release
It is necessary to update more than just a single package, because they refer
to each other in their `setup.py` files.

```bash
TAG=v1.2
DIR=release/$TAG
MESSAGE="Deferred fields in django-chamber"

rm -rf $DIR
mkdir -p $DIR

# find all references to update
grep -r --include setup.py dead
# TODO: update paths in the setup.py files

# find all directories looking like packages
find . -maxdepth 2 -name 'setup.py' | xargs -I{} bash make-tar.sh "{}" "$DIR"

# check if all is commited!
git status
git commit ...

git tag -am $MESSAGE $TAG

# push the tags to remote
git push

# create a release from the pushed tag and upload all files
gh release create -t "$MESSAGE" --notes '' "$TAG" $DIR/*
```

# Dependency graph
Use [Mermaid live](https://mermaid.live/) to test.

```mermaid
graph LR;
    A[Trendaro Admin]-->C;
    A-->D(django-security);
    A-->E(django-reversion);
    A-->H(django-validated-file);
    A-->I(django-cors-middleware);
    A-->F(django_compressor);
    A-->G(django-mailer);
    A-->B(germanium);

    C(django-is-core)-->K(django-apptemplates);
    C-->L(django-piston);
    C-->M(django-block-snippets);
    C-->N(django-project-info);
    C-->J;

    %% placing this here improves rendering
    A-->J(django-chamber);

    E-->J;

    H-->J;

    D-->O(django-json-field);
```
