#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
#include <time.h>

int totalMax = 0, totalBids[100000], nBids = 0;
int randomRestart(int t, int coalblocks, int companies, int bids, int bidsId[][coalblocks + 1], int bidsRevenue[], int bidsCompany[], int bidsCount[]) {
    //Random initialization
    int randComp[companies];
    for(int i = 0;i < companies;++i){
        randComp[i] = i;
    }
    for(int i = 0;i < companies;++i) {
        int r = rand()%companies;
        int temp = randComp[i];
        randComp[i] = randComp[r];
        randComp[r] = temp;
    }
    int companySold[companies];
    memset( companySold, 0, (companies) * sizeof(int));
    int blockSold[coalblocks];
    memset( blockSold, 0, (coalblocks) * sizeof(int));
    int bidsSold[bids];
    memset( bidsSold, 0, (bids) * sizeof(int));
    int compBidSold[companies];
    memset( compBidSold, -1, (companies) * sizeof(int));
    //Random initial state
    for(int i = 0;i < companies;++i) {
        int curComp = randComp[i];
        int s = 0 , f = bidsCount[curComp];
        if(curComp != 0) {
            s = bidsCount[curComp - 1];
        }
        int valid = 0;
        for(int j = f - 1;j >= s;--j) {
            valid = 0;
            for(int k = 0;k < coalblocks;++k) {
                if(bidsId[j][k] == 1 && blockSold[k] == 1) {
                    valid = 1;
                    break;
                }
            }
            if(valid == 0) {
                bidsSold[j] = 1;
                for(int k = 0;k < coalblocks;++k) {
                    if(bidsId[j][k] == 1) {
                        blockSold[k] = 1;
                    }
                }
                totalMax += bidsRevenue[j];
                totalBids[nBids++] = j;
                companySold[curComp] = 1;
                compBidSold[curComp] = j;
                break;
            }
        }
    }
    /*for(int i = 0;i < bids;++i) {
        printf("%d ",bidsSold[i]);
    }*/
    //printf("\n");
    //Selecting neighbours
    int localMax = 0;
    int curMax = 0;
    int curBid = -1;
    int prevBid = -1;

    while(!localMax) {
        curBid = -1;
        curMax = 0;
        //printf("Out\n");
        for(int i = 0;i < companies;++i) {
            int s = 0 , f = bidsCount[i];
            if(i != 0) {
                s = bidsCount[i - 1];
            }
            int valid = 0;
            if(!companySold[i]) {
                for(int j = s;j < f;++j) {
                    valid = 0;
                    for(int l = 0;l < coalblocks;++l) {
                        if(bidsId[j][l] == 1 && blockSold[l] == 1) {
                            valid = 1;
                            break;
                        }
                    }
                    if(valid == 0) {
                        if(bidsRevenue[j] > curMax) {
                            curMax = bidsRevenue[j];
                            curBid = j;
                            prevBid = j;
                        }
                    }
                }
                continue;
            }
            int remBid = compBidSold[i];
            //printf("X: \n%d  %d\n",remBid, i);
            //printf("%d  %d\n",companySold[0], companySold[1]);
            for(int k = 0;k < coalblocks;++k) {
                if(bidsId[remBid][k] == 1) {
                    blockSold[k] = 0;
                }
            }
            bidsSold[remBid] = 0;

            for(int j = s;j < f;++j) {
                valid = 0;
                if(j != remBid) {
                    for(int l = 0;l < coalblocks;++l) {
                        if(bidsId[j][l] == 1 && blockSold[l] == 1) {
                            valid = 1;
                            break;
                        }
                    }
                    if(valid == 0) {
                        if(bidsRevenue[j] - bidsRevenue[remBid] > curMax) {
                            curMax = bidsRevenue[j] - bidsRevenue[remBid];
                            curBid = j;
                            prevBid = remBid;
                        }
                    }
                }
            }
            //printf("%d  %d\n",curBid, prevBid);
            //printf("%d  %d\n", i, companySold[bidsCompany[remBid]]);
            for(int j = 0;j < companies;++j) {
                if(!companySold[j]) {
                    s = 0 , f = bidsCount[j];
                    if(j != 0) {
                        s = bidsCount[j - 1];
                    }
                    valid = 0;
                    for(int k = s;k < f;++k) {
                        valid = 0;
                        for(int l = 0;l < coalblocks;++l) {
                            if(bidsId[k][l] == 1 && blockSold[l] == 1) {
                                valid = 1;
                                break;
                            }
                        }
                        if(valid == 0) {
                            if(bidsRevenue[k] - bidsRevenue[remBid] > curMax) {
                                curMax = bidsRevenue[k] - bidsRevenue[remBid];
                                curBid = k;
                                prevBid = remBid;
                            }
                        }
                    }
                }
            }
            for(int k = 0;k < coalblocks;++k) {
                if(bidsId[remBid][k] == 1) {
                    blockSold[k] = 1;
                }
            }
            //printf("%d  %d\n",curBid, prevBid);
            bidsSold[remBid] = 1;
        }
        if(curBid == -1) {
            localMax = 1;
            break;
        }
        for(int k = 0;k < coalblocks;++k) {
            if(bidsId[prevBid][k] == 1) {
                blockSold[k] = 0;
            }
        }
        bidsSold[prevBid] = 0;
        companySold[bidsCompany[prevBid]] = 0;
        for(int k = 0;k < coalblocks;++k) {
            if(bidsId[curBid][k] == 1) {
                blockSold[k] = 1;
            }
        }
        bidsSold[curBid] = 1;
        companySold[bidsCompany[curBid]] = 1;
        compBidSold[bidsCompany[curBid]] = curBid;
    }

    int curRevenue = 0, curNBids = 0;
    for(int i = 0;i < bids;++i) {
        curRevenue += bidsRevenue[i] * bidsSold[i];
        curNBids += bidsSold[i];
    }
    if(curRevenue > totalMax) {
        totalMax = curRevenue;
        nBids = curNBids;
        int track = 0;
        for(int i = 0;i < bids;++i) {
            if(bidsSold[i]) {
                totalBids[track++] = i;
            }
        }
    }
    return 0;
}
int main(int argc, char *argv[]) {
    srand(time(NULL));
    FILE *inputFile, *outputFile;
    inputFile = fopen(argv[1], "r");
    outputFile = fopen(argv[2], "w");
    totalMax = 0, nBids = 0;
    int t, coalblocks, companies, bids;
    fscanf(inputFile, "%d%d%d%d",&t,&coalblocks,&bids,&companies);
    memset( totalBids, 0, (10000) * sizeof(int));
    int bidsId[bids + 1][coalblocks + 1];
    memset( bidsId, 0, (bids + 1) * (coalblocks + 1) * sizeof(int));
    int bidsRevenue[bids + 1];
    memset( bidsRevenue, 0, (bids + 1) * sizeof(int));
    int bidsCompany[bids + 1];
    memset( bidsCompany, 0, (bids + 1) * sizeof(int));
    int bidsCount[companies];
    int nb = 0;
    int cid, ncid, nBlocks, bidVal, curBlock;
    while(nb < bids) {
        fscanf(inputFile, "%d%d",&cid,&ncid);

        while(ncid--) {
            fscanf(inputFile, "%d%d%d",&cid,&nBlocks,&bidVal);
            while(nBlocks--) {
                fscanf(inputFile, "%d",&curBlock);
                bidsId[nb][curBlock - 1] = 1;
            }
            bidsRevenue[nb] = bidVal;
            bidsCompany[nb] = cid - 1;
            nb++;
        }
        bidsCount[cid - 1] = nb;
    }
    clock_t start,end;
    start = clock();
    double timeTaken;
    while(true) {
        randomRestart(t, coalblocks, companies, bids, bidsId, bidsRevenue, bidsCompany, bidsCount);
        end=clock();
        timeTaken=((double)(end-start))/CLOCKS_PER_SEC;
        if(time_taken>t*60) {
            break;
        }
    }
    fprintf(outputFile, "%d ",totalMax);
    for(int i = 0;i < nBids;++i) {
        fprintf(outputFile, "%d ", totalBids[i]);
    }
    fclose(inputFile);
    fclose(outputFile);
    return 0;
}
