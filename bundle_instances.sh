#!/bin/bash

INSTANCES_LOCATION="./instance"
REGISTERS=("asgs2016_australia"  "asgs2016_stateorterritory" "asgs2016_meshblock" "asgs2016_statisticalarealevel1"
"asgs2016_statisticalarealevel2" "asgs2016_statisticalarealevel3" "asgs2016_statisticalarealevel4" "asgs2016_greatercapitalcitystatisticalarea"
"asgs2016_indigeno*" "asgs2016_urbancentreandlocality" "asgs2016_commonwealthelectoraldivision" "asgs2016_localgovernmentarea" "asgs2016_naturalresource*"
"asgs2016_remotenessarea" "asgs2016_sectionofstate" "asgs2016_sectionofstaterange" "asgs2016_significanturbanarea" "asgs2016_statesuburb")
OUT_NAMES=("asgs2016_aus" "asgs2016_state" "asgs2016_meshblocks" "asgs2016_sa1" "asgs2016_sa2" "asgs2016_sa3" "asgs2016_sa4"
"asgs2016_gccsa" "asgs2016_ind" "asgs2016_ucl" "asgs2016_ced" "asgs2016_lga" "asgs2016_nrmr" "asgs2016_ra" "asgs2016_sos"
"asgs2016_sosr" "asgs2016_sua" "asgs2016_ssc")

CWD=`pwd`
cd $INSTANCES_LOCATION
REG_LEN=${#REGISTERS[@]}
NAMES_LEN=${#OUT_NAMES[@]}

if [ $REG_LEN -ne $NAMES_LEN ] ; then
  echo "$REG_LEN != $NAMES_LEN"
  exit 1
fi

for (( i=0; i<$REG_LEN; i++ )); do
  reg_match="./http_linked.data.gov.au_dataset_${REGISTERS[$i]}_p*.nt"
  out_name="${OUT_NAMES[$i]}"
  rm -f $out_name".nt.gz"
  rm -f $out_name".nt.gz.sha256"
  cat $reg_match | gzip -c -k --rsyncable > $out_name".nt.gz"
  sha256sum $out_name".nt.gz" > $out_name".nt.gz.sha256"
done
cd "$CWD"

# Upload to S3 like this:
# $> aws s3 cp . s3://loci-assets/asgs-20200426/ --recursive --include "asgs_2016*" --exclude="http_linked*"