#!/bin/sh
dos2unix buildfiles.lst
cat buildfiles.lst | xargs dos2unix
tar -czvf venus-data.tar.gz --mode='a+rwX' -T buildfiles.lst
