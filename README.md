# ALLIRT
Tool that converts  All of libc to signatures for IDA Pro FLIRT Plugin. and utility make sig with FLAIR easily



## Usage
```
$ python3 allirt.py
```
```
Usage : python3 alirt.py (-o <out_dir> -s <start> -e <end> -f <flair_dir> -c <compress>)
```

*you must have* `flair` *utilities.* (`pelf`, `sigmake`, `zipsig`)

### Options
```
$ allirt.py -h
```
```
Usage: allirt.py -o <out_dir>

Options:
  -h, --help            show this help message and exit
  -o OUT_DIR, --outdir=OUT_DIR
                        set result directory
  -s START, --start=START
                        set series start range
  -e END, --end=END     set series end range
  -f FLAIR, --flair=FLAIR
                        set flair util directory
  -c, --no-compress     sig not compress
```

`-f` option is flair utilities directory ( default : `flair` ) 
```
├── dumpsig
├── pcf
├── pelf
├── pelf.rtb
├── plb
├── pmacho
├── pomf166
├── ppsx
├── ptmobj
├── sigmake
└── zipsig
```

requires `pelf` `sigmake` `zipsig`
 
### Get all of signatures of libc packages
```
$ python3 allirt.py -f flair -o tmp
[INFO] OS : ubuntu
[INFO] Package : libc6-dev


[INFO] OS Series (1/30) : warty (4.10)

[INFO] Architecture (1/3) : amd64

[INFO] Package Version (1/3) : 2.3.2.ds1-13ubuntu2
[INFO] ubuntu 4.10 libc6-dev amd64 2.3.2.ds1-13ubuntu2 2018-06-03 02:09:52.441499
[INFO] Download Completed : http://launchpadlibrarian.net/1251110/libc6-dev_2.3.2.ds1-13ubuntu2_amd64.deb (2961464 bytes)
[INFO] Target library : ./usr/lib/libc.a
[INFO] Signature has been generated. -> tmp/ubuntu/4.10 (warty)/amd64/libc6_2.3.2.ds1-13ubuntu2_amd64.sig

[INFO] Package Version (2/3) : 2.3.2.ds1-13ubuntu2.2
[INFO] ubuntu 4.10 libc6-dev amd64 2.3.2.ds1-13ubuntu2.2 2018-06-03 02:10:10.521781
[WARNING] Package deleted

[INFO] Package Version (3/3) : 2.3.2.ds1-13ubuntu2.3
[INFO] ubuntu 4.10 libc6-dev amd64 2.3.2.ds1-13ubuntu2.3 2018-06-03 02:10:11.242

.........................


[INFO] Architecture (5/5) : sparc
[WARNING] SKIPPED
[INFO] Finished
```


### Get signatures of some libc packages 
using `-s` start `-e` end options.

range of os series

```
$ python3 allirt.py -f flair -s 1 -e 2 -o tmp
[INFO] OS : ubuntu
[INFO] Package : libc6-dev


[INFO] OS Series (1/1) : hoary (5.04)

[INFO] Architecture (1/5) : amd64

[INFO] Package Version (1/3) : 2.3.2.ds1-20ubuntu13
[INFO] ubuntu 5.04 libc6-dev amd64 2.3.2.ds1-20ubuntu13 2018-06-03 02:04:58.0489
```

### Result
```
└── ubuntu
    ├── 4.10\ (warty)
    │   └── amd64
    │       └── libc6_2.3.2.ds1-13ubuntu2_amd64.sig
    └── 5.04\ (hoary)
        ├── amd64
        │   ├── libc6_2.3.2.ds1-20ubuntu13_amd64.sig
        │   └── libc6_2.3.2.ds1-20ubuntu15_amd64.sig
        ├── i386
        │   ├── libc6_2.3.2.ds1-20ubuntu13_i386.sig
        │   └── libc6_2.3.2.ds1-20ubuntu15_i386.sig
        ├── ia64
        └── powerpc
            ├── libc6_2.3.2.ds1-20ubuntu13_powerpc.sig
            └── libc6_2.3.2.ds1-20ubuntu15_powerpc.sig
```

## TODO
* save a file (static library ex: libc.a)
* fliar.py command line interface

*suggests me your idea and issue*

this tool uses `launchpad.net` mirror. I am finding package mirrors.

Thanks to @hstocks - `Unknown relocation type`
