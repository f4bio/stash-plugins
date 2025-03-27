#!/bin/bash

# builds a repository of scrapers
# outputs to _site with the following structure:
# index.yml
# <scraper_id>.zip
# Each zip file contains the scraper.yml file and any other files in the same directory

outDir="$1"
if [ -z "$outDir" ]; then
    outDir="_site"
fi

rm -rf "$outDir"
mkdir -p "$outDir"

buildPlugin()
{
    f=$1

    if grep -q "^#pkgignore" "$f"; then
        return
    fi

    # get the scraper id from the directory
    dir=$(dirname "$f")
    plugin_id=$(basename "$f" .yml)

    echo "Processing $plugin_id"

    # create a directory for the version
    version=$(git log -n 1 --pretty=format:%h -- "$dir"/*)
    updated=$(TZ=UTC0 git log -n 1 --date="format-local:%F %T" --pretty=format:%ad -- "$dir"/*)

    # create the zip file
    # copy other files
    zipfile=$(realpath "$outDir/$plugin_id.zip")

    pushd "$dir" > /dev/null || exit
    zip -r "$zipfile" . > /dev/null
    popd > /dev/null || exit

    name=$(grep "^name:" "$f" | head -n 1 | cut -d' ' -f2- | sed -e 's/\r//' -e 's/^"\(.*\)"$/\1/')
    description=$(grep "^description:" "$f" | head -n 1 | cut -d' ' -f2- | sed -e 's/\r//' -e 's/^"\(.*\)"$/\1/')
    ymlVersion=$(grep "^version:" "$f" | head -n 1 | cut -d' ' -f2- | sed -e 's/\r//' -e 's/^"\(.*\)"$/\1/')
    version="$ymlVersion-$version"
    dep=$(grep "^# requires:" "$f" | cut -c 12- | sed -e 's/\r//')

    # write to spec index
    echo "- id: $plugin_id
  name: $name
  metadata:
    description: $description
  version: $version
  date: $updated
  path: $plugin_id.zip
  sha256: $(sha256sum "$zipfile" | cut -d' ' -f1)" >> "$outDir"/index.yml

    # handle dependencies
    if [ -n "$dep" ]; then
        echo "  requires:" >> "$outDir"/index.yml
        for d in ${dep//,/ }; do
            echo "    - $d" >> "$outDir"/index.yml
        done
    fi

    echo "" >> "$outDir"/index.yml
}

find ./plugins -mindepth 1 -name "*.yml" | while read -r file; do
    buildPlugin "$file"
done
