oarsub -t deploy -l slash_22=1+nodes=5,walltime=2 -I
g5k-subnets -sp
kadeploy3 -f $OAR_NODE_FILE -e jessie-x64-nfs -k

