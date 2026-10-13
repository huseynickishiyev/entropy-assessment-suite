/* Research implementation of SP800-90B RCT/APT on raw discrete symbols.
 * APT uses non-overlapping windows and first symbol of each window as reference.
 * Cutoffs are user supplied; no claim of NIST validation.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <errno.h>

static void usage(void){fprintf(stderr,"usage: ip4_health FILE BITS SAMPLES RCT_C APT_W APT_C\n");}
int main(int argc,char **argv){
 if(argc!=7){usage();return 2;}
 char *end=NULL; errno=0; long bits=strtol(argv[2],&end,10);
 if(errno||*end||!(bits==1||bits==4||bits==8)){usage();return 2;}
 errno=0; unsigned long long n=strtoull(argv[3],&end,10);if(errno||*end||n==0){usage();return 2;}
 errno=0; unsigned long long rc=strtoull(argv[4],&end,10);if(errno||*end||rc<2){usage();return 2;}
 errno=0; unsigned long long aw=strtoull(argv[5],&end,10);if(errno||*end||aw<2){usage();return 2;}
 errno=0; unsigned long long ac=strtoull(argv[6],&end,10);if(errno||*end||ac<2||ac>aw){usage();return 2;}
 FILE *fp=fopen(argv[1],"rb");if(!fp){perror("open");return 2;}
 uint64_t counts[256]={0}; int prev=-1, ref=-1;uint64_t run=0,maxrun=0, winpos=0, wincount=0, rct_hits=0, apt_hits=0, windows=0, first_rct=0, first_apt=0; int invalid=0;
 const int limit=(1<<bits);
 for(uint64_t i=0;i<n;i++){
  int c=fgetc(fp);if(c==EOF){fprintf(stderr,"input shorter than claimed sample count\n");fclose(fp);return 2;}
  if(c>=limit){invalid=1;break;}
  counts[c]++;
  if(c==prev)run++;else{run=1;prev=c;}
  if(run>maxrun)maxrun=run;
  if(run==rc){rct_hits++;if(!first_rct)first_rct=i+1;}
  if(winpos==0){ref=c;wincount=1;}else if(c==ref)wincount++;
  winpos++;
  if(winpos==aw){windows++;if(wincount>=ac){apt_hits++;if(!first_apt)first_apt=i+1;}winpos=0;wincount=0;}
 }
 int extra=fgetc(fp);fclose(fp);
 if(invalid||extra!=EOF){fprintf(stderr,"invalid symbol or extra bytes (expected exactly %llu bytes)\n",n);return 2;}
 double sh=0,pmax=0;for(int i=0;i<limit;i++){if(counts[i]){double p=(double)counts[i]/(double)n;sh-=p*log2(p);if(p>pmax)pmax=p;}}
 printf("{\"samples\":%llu,\"bits\":%ld,\"rct_cutoff\":%llu,\"rct_alarms\":%llu,\"rct_first_alarm_sample\":%llu,\"rct_max_run\":%llu,\"apt_window\":%llu,\"apt_cutoff\":%llu,\"apt_full_windows\":%llu,\"apt_alarms\":%llu,\"apt_first_alarm_sample\":%llu,\"apt_partial_window_samples\":%llu,\"empirical_shannon\":%.10f,\"empirical_mcv_plugin\":%.10f,\"health_alarm\":%s}\n",n,bits,rc,(unsigned long long)rct_hits,(unsigned long long)first_rct,(unsigned long long)maxrun,aw,ac,(unsigned long long)windows,(unsigned long long)apt_hits,(unsigned long long)first_apt,(unsigned long long)winpos,sh,-log2(pmax),(rct_hits||apt_hits)?"true":"false");
 return 0;
}
