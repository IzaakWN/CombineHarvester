#! /bin/bash

function peval { # print and evaluate given command
  echo -e ">>> $(tput setab 0)$(tput setaf 7)$@$(tput sgr0)"; eval "$@";
}

DIRS="output log debug plots postfit shapes controlPlots toys biastest impacts"
echo ">>> Are you sure you want to reset all these directories?"
echo ">>>   $DIRS"
printf ">>> "
read proceed
[ x$proceed != x"y" ] && exit 0

for dir in $DIRS; do
  peval "rm -r $dir/*"
done

