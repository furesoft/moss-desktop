#/bin/bash
python3 -m nuitka --mode=app --include-data-dir=assets=assets --include-data-files=LICENSE=LICENSE \
--assume-yes-for-downloads --output-dir=build --script-name=moss.py --linux-icon=assets/icons/moss.png \
--deployment --disable-console