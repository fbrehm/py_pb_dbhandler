#!/bin/bash

pot_file="py_pb_dbhandler.pot"
output_dir="po"
pkg_version="0.4.2"
pkg_name="profitbricks-python-dbhandler"
src_dir="src/pb_dbhandler"

cd $(dirname $0)

xgettext --output="${pot_file}" \
        --output-dir="${output_dir}" \
        --language="Python" \
        --add-comments \
        --keyword=_ \
        --keyword=__ \
        --force-po \
        --indent \
        --add-location \
        --width=85 \
        --sort-by-file \
        --package-name="${pkg_name}" \
        --package-version="${pkg_version}" \
        --msgid-bugs-address=frank.brehm@profitbricks.com \
        $(find "${src_dir}" -type f -name '*.py' | sort)

sed -i -e 's/msgid[ 	][ 	]*"/msgid "/' \
       -e 's/msgstr[ 	][ 	]*"/msgstr "/' \
       -e 's/^        /      /' \
       "${output_dir}/${pot_file}"

# vim: ts=4 et
