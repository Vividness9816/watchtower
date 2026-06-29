SMART Attributes documentation
Main Page > Server Software > Linux > Linux-Storage > Smartmontools
S.M.A.R.T. (Self-Monitoring, Analysis and Reporting Technology; written as SMART) SMART is a system for monitoring and early detection of errors of storage media such as hard disks or SSDs. All current hard drives and SSDs have SMART functionality. However, the data provided by SMART, (SMART attributes), are different from manufacturer to manufacturer. Only a few manufacturers document the importance of the individual SMART attributes in detail (eg. Intel, see SMART attributes of Intel SSDs). It is difficult for the user to interpret the SMART attributes without documentation.


Contents
1	Origination
2	Standardization
3	SMART Attributes
3.1	Reading the SMART Attributes
4	SMART Tests
5	References
Origination
SMART was originally developed in the mid 90s by the Small Form Factor (SFF) Committee, [1] in the meantime Technical Committee T13 are responsible for SMART. SMART has been standard since ATA-3 to ATA/ATAPI. However, it was removed shortly before the publication of the standard description of the SMART attributes. Therefore, the consequence is that a hard disk drive only provides a status of "OK" or "not OK" according to Standard. It does not specify how many or which sensors (attributes) a hard drive must have.

Over time, a relative standard equivalent has been formed to then remove it. However, the SMART attributes of hard drives can still be read and assigned, eg. with the help of tools smartctl. The exact meaning of a particular SMART attribute (eg. Raw Read Error Rate) is often specific according to the manufacturer. Since SSDs, many of the previous SMART attributes that were created no longer make sense and were given new meaning or removed entirely by the manufacturers.

Standardization
The standardization of SMART was first seen with ATA-3. The 7b revision of the ATA-3 draft[2] still contained descriptions of the SMART attributes, these were removed but before the adoption of standards. Since ATA-3 a standard chapter is found in (eg. Chapter 4.21 in ATA-8[3]) to SMART, which does not, however, refer to the attributes, but rather treated only as general SMART functions. There was a proposal for the description of SMART attributes for ATA-8[4] (was subsequently split into three proposals)[5][6][7] which were not included in the standard.

There was also a proposal on SMART self tests.[8] These were recorded as SPC-x[9] (SCSI Primary Commands).

The following table shows which SMART functions were standardized:

Have been standardized:[3][9]
SMART data format
SMART data collection
Response to exceeding of thresholds ("Dev OK"; "Dev fail")
SMART commands
SMART error logs
SMART tests
Not standardized, but handled (semi-standard based on the ATA-3 drafts[2]):
SMART attributes (it is not specified which attributes must be present and how these are to be stored)
Interpretation of the SMART attributes (it is not specified whether an attribute eg. is a bit pattern or a number)
SMART Attributes
Since the SMART attributes are not standardized, each manufacturer can choose which SMART attributes it defines for each hard disk or SSD model.

A SMART attribute contains:

Attribute name (e.g. Raw Read Error Rate)
raw value (RAW_VALUE in the smartctl output): is individually defined by the manufacturer. Without specific documentation of the importance of this value an interpretation is not reliable. Often raw values ​​are physical quantities (e.g. temperature, hours, ...).
normalized value (VALUE in the smartctl output): Value between 1 (worst condition) and 253 (best condition), most manufacturers use 100 or 200 as a best value.
of previously measured values the worst normalized values (WORST in the smartctl output)
Limit for the normalized value (THRESH in the output of smartctl): when it falls below the normalized value of this limit, it is set to "Dev fail" SMART status.
Various attributes are only updated when you restart or during a self-test, this can be seen in smartctl output in the column on the entry UPDATED "offline". Values​​ that are updated during operation are labeled "Always". There are also various types of attributes. Attributes of 'Pre-fail' may show an early failure of the disk in low values. Attributes of "Old-age" can be changed by the normal aging process of a hard disk.

Here is a sample smartctl tool output:

adminuser@ubuntu-12-04:~$ sudo smartctl -a /dev/sda
smartctl 5.41 2011-06-09 r3365 [x86_64-linux-3.2.0-54-generic] (local build)
Copyright (C) 2002-11 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF INFORMATION SECTION ===
Model Family:     Western Digital RE4
Device Model:     WDC WD1003FBYX-01Y7B0
[...]
Vendor Specific SMART Attributes with Thresholds:
ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
  1 Raw_Read_Error_Rate     0x002f   200   200   051    Pre-fail  Always       -       0
  3 Spin_Up_Time            0x0027   174   171   021    Pre-fail  Always       -       4291
  4 Start_Stop_Count        0x0032   100   100   000    Old_age   Always       -       126
  5 Reallocated_Sector_Ct   0x0033   200   200   140    Pre-fail  Always       -       0
  7 Seek_Error_Rate         0x002e   200   200   000    Old_age   Always       -       0
  9 Power_On_Hours          0x0032   087   087   000    Old_age   Always       -       9532
 10 Spin_Retry_Count        0x0032   100   100   000    Old_age   Always       -       0
 11 Calibration_Retry_Count 0x0032   100   100   000    Old_age   Always       -       0
 12 Power_Cycle_Count       0x0032   100   100   000    Old_age   Always       -       123
192 Power-Off_Retract_Count 0x0032   200   200   000    Old_age   Always       -       68
193 Load_Cycle_Count        0x0032   200   200   000    Old_age   Always       -       57
194 Temperature_Celsius     0x0022   115   102   000    Old_age   Always       -       32
196 Reallocated_Event_Count 0x0032   200   200   000    Old_age   Always       -       0
197 Current_Pending_Sector  0x0032   200   200   000    Old_age   Always       -       0
198 Offline_Uncorrectable   0x0030   200   200   000    Old_age   Offline      -       0
199 UDMA_CRC_Error_Count    0x0032   200   200   000    Old_age   Always       -       0
200 Multi_Zone_Error_Rate   0x0008   200   200   000    Old_age   Offline      -       0
In the english Wikipedia article on SMART, a list of known attributes SMART Attributen including a short description is given.

This article contains instructions for increasing the size of a Logical Volume using a Debian Linux VMware Virtual Machine (VM). This how-to information should work similarly with other Linux distributions.


Contents
1	Initial situation
2	Step-by-step instructions
2.1	Increasing the size of the hard disk area at VMware level
2.2	Creating an additional partition
2.3	Initializing new partition as Physical Volume
2.4	Increasing the size of the Volume Group
2.5	Increasing the size of the Logical Volume
2.6	Increasing the size of the file system
3	Summary of steps
4	Additional Information
Initial situation


This screenshot shows that the entire hard disk space allocated to this VM is divided between the boot partition and the LVM.

The LVM (Logical Volume Manager) configuration is as follows for this example:

vm208:~# pvs
  PV         VG    Fmt  Attr PSize  PFree
  /dev/sda2  vm208 lvm2 a-   19,75G    0 
vm208:~# vgs
  VG    #PV #LV #SN Attr   VSize  VFree
  vm208   1   6   0 wz--n- 19,75G    0 
vm208:~# lvs
  LV     VG    Attr   LSize   Origin Snap%  Move Log Copy%  Convert
  home   vm208 -wi-ao  10,54G                                      
  root   vm208 -wi-ao 332,00M                                      
  swap_1 vm208 -wi-ao   1,07G                                      
  tmp    vm208 -wi-ao 380,00M                                      
  usr    vm208 -wi-ao   4,66G                                      
  var    vm208 -wi-ao   2,79G                                      
vm208:~# df -h
File System          Size Used  Avail Used% Shared as
/dev/mapper/vm208-root
                      322M  175M  131M  58% /
tmpfs                 187M     0  187M   0% /lib/init/rw
udev                   10M  612K  9,5M   6% /dev
tmpfs                 187M     0  187M   0% /dev/shm
/dev/sda1             228M   28M  189M  13% /boot
/dev/mapper/vm208-home
                       11G  155M  9,7G   2% /home
/dev/mapper/vm208-tmp
                      368M   11M  339M   3% /tmp
/dev/mapper/vm208-usr
                      4,6G  332M  4,1G   8% /usr
/dev/mapper/vm208-var
                      2,8G  280M  2,4G  11% /var
vm208:~#
The size of the "root" logical volume for the "vm208" (/dev/mapper/vm208-root) volume group should be increased.

Step-by-step instructions
Increasing the size of the hard disk area at VMware level
The VM dialog for configuring the settings will be opened by right-clicking the VM from the vSphere client and then clicking "Edit Settings". From there, select the hard disk and increase its size to the desired value, from 20 gigabytes to 25 gigabytes for our example.



Once the VM has been re-booted, the following image should then appear.



Creating an additional partition
To be able to use this additional hard disk space, an additional partition must be created (such as by using the cfdisk utility). To do that, the free memory will be selected using the arrow keys and New > Primary > completely available memory selected (if desired). Afterwards, the area will be partitioned.



Afterwards, the new partition table must be written using the "Write" command and the partitioning utility closed using the "Quit" command. To continue with this example, the partition table must be re-read. To avoid another reboot, the partition table can be re-read by the "partprobe" command (a component in the "parted" package).

Initializing new partition as Physical Volume
So that this additional partition can be used for LVM and a volume group assigned, it must next be initialized as a Physical Volume (PV).

vm208:~# pvs
  PV         VG    Fmt  Attr PSize  PFree
  /dev/sda2  vm208 lvm2 a-   19,75G    0 
vm208:~# pvcreate /dev/sda3
  Physical volume "/dev/sda3" successfully created
vm208:~# pvs
  PV         VG    Fmt  Attr PSize  PFree
  /dev/sda2  vm208 lvm2 a-   19,75G    0 
  /dev/sda3        lvm2 --    5,00G 5,00G
vm208:~#
Increasing the size of the Volume Group
So that the size of the logical volume "root" can be increased, the size of the corresponding volume group must first be increased.

vm208:~# vgs
  VG    #PV #LV #SN Attr   VSize  VFree
  vm208   1   6   0 wz--n- 19,75G    0 
vm208:~# vgextend vm208 /dev/sda3
  Volume group "vm208" successfully extended
vm208:~# vgs
  VG    #PV #LV #SN Attr   VSize  VFree
  vm208   2   6   0 wz--n- 24,75G 5,00G
vm208:~#
Increasing the size of the Logical Volume
Next, the size of the logical "root" volume can be increased.

vm208:~# lvs
  LV     VG    Attr   LSize   Origin Snap%  Move Log Copy%  Convert
  home   vm208 -wi-ao  10,54G                                      
  root   vm208 -wi-ao 332,00M                                      
  swap_1 vm208 -wi-ao   1,07G                                      
  tmp    vm208 -wi-ao 380,00M                                      
  usr    vm208 -wi-ao   4,66G                                      
  var    vm208 -wi-ao   2,79G                                      
vm208:~# lvextend -L 1G /dev/mapper/vm208-root 
  Extending logical volume root to 1,00 GB
  Logical volume root successfully resized
vm208:~# lvs
  LV     VG    Attr   LSize   Origin Snap%  Move Log Copy%  Convert
  home   vm208 -wi-ao  10,54G                                      
  root   vm208 -wi-ao   1,00G                                      
  swap_1 vm208 -wi-ao   1,07G                                      
  tmp    vm208 -wi-ao 380,00M                                      
  usr    vm208 -wi-ao   4,66G                                      
  var    vm208 -wi-ao   2,79G                                      
vm208:~#
In this example, we will increase the size of the logical root volume to roughly 1 gigabyte. We will reserve the remaining free memory for the vm208 volume group for later use for another logical volume, for example.

Note: The lvextend command will not indicate the amount by which the logical volume should been increased, but rather the final size to which it should be increased. Alternatively, the + symbol can be used before setting the size and the logical volume will then be increased about the specified size.

Increasing the size of the file system
To be able to use the additional storage area, the size of the file system must finally be increased. ext3, which will support such increases without problems (even in the mounted state), has been used as the file system in our example.

vm208:~# df -h
File System          Size Used  Avail Used% Shared as
/dev/mapper/vm208-root
                      322M  175M  131M  58% /
tmpfs                 187M     0  187M   0% /lib/init/rw
udev                   10M  616K  9,4M   7% /dev
tmpfs                 187M     0  187M   0% /dev/shm
/dev/sda1             228M   28M  189M  13% /boot
/dev/mapper/vm208-home
                       11G  155M  9,7G   2% /home
/dev/mapper/vm208-tmp
                      368M   11M  339M   3% /tmp
/dev/mapper/vm208-usr
                      4,6G  332M  4,1G   8% /usr
/dev/mapper/vm208-var
                      2,8G  281M  2,4G  11% /var
vm208:~# resize2fs -p /dev/mapper/vm208-root 
resize2fs 1.41.3 (12-Oct-2008)
The file system under /dev/mapper/vm208-root will be mounted as /, and online size changes will be necessary.
old desc_blocks = 2, new_desc_blocks = 4
Execute an online size change to /dev/mapper/vm208-root to 1048576 (1k) blocks.
The file system under /dev/mapper/vm208-root will now be 1048576 block large.

vm208:~# df -h
File System          Size Used  Avail Used% Shared as
/dev/mapper/vm208-root
                      993M  176M  766M  19% /
tmpfs                 187M     0  187M   0% /lib/init/rw
udev                   10M  616K  9,4M   7% /dev
tmpfs                 187M     0  187M   0% /dev/shm
/dev/sda1             228M   28M  189M  13% /boot
/dev/mapper/vm208-home
                       11G  155M  9,7G   2% /home
/dev/mapper/vm208-tmp
                      368M   11M  339M   3% /tmp
/dev/mapper/vm208-usr
                      4,6G  332M  4,1G   8% /usr
/dev/mapper/vm208-var
                      2,8G  281M  2,4G  11% /var
vm208:~#
Summary of steps
Increase the size of the hard disk area (at physical or VMware level)
Reboot the machine so that the additional hard disk space will be detected
Create an additional partition, for example, by using cfdisk
Re-read the partition table, such as, by re-booting or using the partprobe command
Initialize a new physical volume using the pvcreate command
Increase the size of the volume group using the vgextend command
Increase the size of the logical volume using the lvextend command
Increase the size of the file system, such as, by using the resize2fs command

LVM basic configuration
Main Page > Server Software > Linux > Linux-Storage > LVM
In the following article, the basic configuration of LVs is explained. The used system is a Ubuntu Server 10.4 with the 2.6.32-24 kernel and the LVM-version 2.02.54(1) (2009-10-26). In the following, it is explained how to create partitions of Physical Volumes (PVs), a Volume Group (VG) and the Logical Volumes (LVs) built on top of them.


Contents
1	Creating partitions
2	Preparation of PVs
3	Creating a VG
4	Creating LVs
5	Creating file system
6	Removing LV
Creating partitions
First, the partitions for the PVs are created. The following points must be taken into account:

Partition Alignment
Switch display to sectors (Switch "-u")
switch off DOS-compatible mode (Switch "-c")
for later LVM management
switch system ID of partition to "8e" (Switch "-t" bei fdisk)
After the changes, the partition table looks as follows:

root@ubuntu:/home/tktest# fdisk -lu

Disk /dev/sda: 5368 MB, 5368709120 bytes
255 heads, 63 sectors/track, 652 cylinders, total 10485760 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0x00051afd

   Device Boot      Start         End      Blocks   Id  System
/dev/sda1   *        2048     9920511     4959232   83  Linux
Partition 1 does not end on cylinder boundary.
/dev/sda2         9922558    10483711      280577    5  Extended
Partition 2 does not end on cylinder boundary.
/dev/sda5         9922560    10483711      280576   82  Linux swap / Solaris

Disk /dev/sdb: 2147 MB, 2147483648 bytes
22 heads, 16 sectors/track, 11915 cylinders, total 4194304 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0x1673663d

   Device Boot      Start         End      Blocks   Id  System
/dev/sdb1            2048     4194303     2096128   8e  Linux LVM

Disk /dev/sdc: 2147 MB, 2147483648 bytes
22 heads, 16 sectors/track, 11915 cylinders, total 4194304 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0xbd277faf

   Device Boot      Start         End      Blocks   Id  System
/dev/sdc1            2048     4194303     2096128   8e  Linux LVM
Preparation of PVs
PVs also include meta data for the administration of volumes (see also LVM basics). 255 sectors (á 512 byte) are created for the meta data by default. Among other things, a meta data area that is too small can result in, for example, the inability to create snapshots anymore: Fix LVM VG vgname metadata too large for circular buffer. Therefore, it will make sense to configure a larger meta data area. If you want to enlargen your meta data area, the parameter "--metadatasize" must be added to the command "pvcreate" and then select the desired size at:

--metadatasize size
After that, the partitions are initialized as PV.

root@ubuntu:~# pvcreate /dev/sdb1 
  Physical volume "/dev/sdb1" successfully created
root@ubuntu:~# pvcreate /dev/sdc1 
  Physical volume "/dev/sdc1" successfully created
The commands "pvs" and "pvdisplay" offer a variety of possibilities to display the current status of the PVs.

root@ubuntu:~# pvs
  PV         VG   Fmt  Attr PSize PFree
  /dev/sdb1       lvm2 --   2.00g 2.00g
  /dev/sdc1       lvm2 --   2.00g 2.00g
Creating a VG
The PVs, that have been created before, are now summarized to a VG.

root@ubuntu:~# vgcreate vg00 /dev/sdb1 /dev/sdc1 
  Volume group "vg00" successfully created
The "pvdisplay" now shows that a VG was created with the PVs:

root@ubuntu:~# pvdisplay 
  --- Physical volume ---
  PV Name               /dev/sdb1
  VG Name               vg00
  PV Size               2.00 GiB / not usable 3.00 MiB
  Allocatable           yes 
  PE Size               4.00 MiB
  Total PE              511
  Free PE               511
  Allocated PE          0
  PV UUID               fl9ipM-bhhQ-V46G-2iH3-R3yZ-9DsN-JbRmY9
   
  --- Physical volume ---
  PV Name               /dev/sdc1
  VG Name               vg00
  PV Size               2.00 GiB / not usable 3.00 MiB
  Allocatable           yes 
  PE Size               4.00 MiB
  Total PE              511
  Free PE               511
  Allocated PE          0
  PV UUID               d1iY5L-ac3F-W5Sz-zyaE-uaT3-f66r-I3831o
vgdisplay also shows information on VG:

root@ubuntu:~# vgdisplay 
  --- Volume group ---
  VG Name               vg00
  System ID             
  Format                lvm2
  Metadata Areas        2
  Metadata Sequence No  1
  VG Access             read/write
  VG Status             resizable
  MAX LV                0
  Cur LV                0
  Open LV               0
  Max PV                0
  Cur PV                2
  Act PV                2
  VG Size               3.99 GiB
  PE Size               4.00 MiB
  Total PE              1022
  Alloc PE / Size       0 / 0   
  Free  PE / Size       1022 / 3.99 GiB
  VG UUID               YTEj9f-9LCT-EOP5-JBEA-YHSz-c0R1-TMzVmy
What stands out here is, that the PE size is 4.00 MiB. Since the lvm2-format, the number of PEs is not limited anymore. According to the Man page of vgcreate, a high number of PEs can slow down the tools. However, the number of pEs does not have influence on the I/O-performance of the Logical Volumes. If you want to change the PE-size, add the parameter to "vgcreate"

-s, --physicalextentsize PhysicalExtentSize
Creating LVs
There are different possibilities to specify the size of the LV to be created. However, all LVs require the parameter "-l" or "-L".

size specification in, for example, Gigabyte:
lvcreate -n data -L1G vg00
Percentage of available storage in the VG:
lvcreate -n data -l100%VG vg00
Percentage of free storage in the VG:
lvcreate -n data -l100%FREE vg00
The example in progress is continued by dividing the VG into two equally sized LVs:

root@ubuntu:~# lvcreate -n data -l50%VG vg00
  Logical volume "data" created
root@ubuntu:~# lvcreate -n data1 -l100%FREE vg00
  Logical volume "data1" created
Now, the status of the Logical Volume can be taken into consideration:

root@ubuntu:~# lvdisplay 
  --- Logical volume ---
  LV Name                /dev/vg00/data
  VG Name                vg00
  LV UUID                S1btrq-zQZQ-h9oU-2VE6-UNoT-hkqB-Fpv7pG
  LV Write Access        read/write
  LV Status              available
  # open                 0
  LV Size                2.00 GiB
  Current LE             511
  Segments               1
  Allocation             inherit
  Read ahead sectors     auto
  - currently set to     256
  Block device           252:0
   
  --- Logical volume ---
  LV Name                /dev/vg00/data1
  VG Name                vg00
  LV UUID                Syaml9-d1Ax-RYTs-tSZy-vEyq-yzqW-VoOddZ
  LV Write Access        read/write
  LV Status              available
  # open                 0
  LV Size                2.00 GiB
  Current LE             511
  Segments               1
  Allocation             inherit
  Read ahead sectors     auto
  - currently set to     256
  Block device           252:1
Creating file system
Now, the LVs can be formatted with a file system and mounted afterwards:

mkfs.ext4 /dev/vg00/data
mkdir data
mount /dev/vg00/data data
Removing LV
If a LV should be removed, it can be removed via lvremove command:

root@ubuntu:~# lvremove /dev/vg00/data_snap 
  Do you really want to remove active logical volume data_snap? [y/n]: y  
  Logical volume "data_snap" successfully removed 
The LV data_snap does no longer appear as an LV. However, the underlying partition is still listed as a PV:

  --- Physical volume ---   
PV Name               /dev/sde1   
VG Name               vg00   
PV Size               2.00 GiB / not usable 3.00 MiB   
Allocatable           yes    
PE Size               4.00 MiB   
Total PE              511   
Free PE               511   
Allocated PE          0   
PV UUID               lKEW15-1YHu-dikC-S0Pm-72UJ-UMPg-fgiW0Y
If the partition should be released completely, the PV must be removed from the VG first:

root@ubuntu:~# vgreduce vg00 /dev/sde1   
  Removed "/dev/sde1" from volume group "vg00"
root@ubuntu:~# pvdisplay
 "/dev/sde1" is a new physical volume of "2.00 GiB"  
 --- NEW Physical volume ---
   PV Name               /dev/sde1
   VG Name                 
   PV Size               2.00 GiB
   Allocatable           NO
   PE Size               0
   Total PE              0 
   Free PE               0
   Allocated PE          0
   PV UUID               lKEW15-1YHu-dikC-S0Pm-72UJ-UMPg-fgiW0Y 
Now, the PV can be also deleted completely to reformat, for example, the hard drive:

root@ubuntu:~# pvremove /dev/sde1
  Labels on physical volume "/dev/sde1" successfully wiped
LVM Snapshots Information
Main Page > Server Software > Linux > Linux-Storage > LVM
Pages using deprecated source tags
LVM Snapshots simplifies Point-In-Time copies of logical volumes (LVs).[1] However, snapshots are not true copies of the reference LVs. If the original LV has been changed after the creation of the snapshot then the original data in the snapshot will be copied into the snapshot first, Copy-on-Write.


Contents
1	Functional Approach and Applications
2	Example Configuration
3	References
4	Additional Information
Functional Approach and Applications
Snapshots do not allocate disk space themselves like their associated original LVs, because the snapshot only requires space when the original has been changed. What is important is keeping an eye on the free space for the snapshot volume, since a fully consumed snapshot volume will be unusable, because changes in the original will not be able to be logged[2]. The consumption of a snapshot volume can be checked by means of the lvs command. It should be emphasized that snapshots themselves are not intended for use as a means of making backups, since only the changes will be saved. The following would be a typical backup scenario:

Create the snapshot
Create a backup of the snapshot data; the original LV can continue to run and be "online".
Delete the snapshot again, since otherwise the changes would continue to be tracked.
Doing this can avoid, for example, having to shutdown the server to make a backup, since the snapshot makes all of the data available for the backup[3].

An additional application of snapshot might be for experimental tests, which should not be performed on the original file system. For such purposes, a snapshot can be created, mounted and the tests then performed. Using this approach, only the snapshot would be changed and the original file system would remain unmodifed[4].

Example Configuration
In order to create a snapshot there has to bo unallocated, free space in the volume group. If it is the case that there is no more space left the volume group can be extended with vgextend (linux.die.net).

In the following volume group are still 2GB left being used for a snapshot:

root@ubuntu:~# vgdisplay
  --- Volume group ---
  VG Name               vg00
[...]
  VG Size               7.98 GiB
  PE Size               4.00 MiB
  Total PE              2044
  Alloc PE / Size       1533 / 5.99 GiB
  Free  PE / Size       511 / 2.00 GiB
  VG UUID               YTEj9f-9LCT-EOP5-JBEA-YHSz-c0R1-TMzVmy
The existing space of 2 GiB on vg00 can be used as a snapshot volume.

root@ubuntu:~# lvcreate -l100%FREE -s -n data_snap /dev/vg00/data
  Logical volume "data_snap" created
The entire 2 GiB snapshot LV is now available for the LV "data". If the 2 GiB should now be partitioned, in order to use it as a snapshot LV for several LVs, data_snap would first have to be deleted.

root@ubuntu:~# lvremove /dev/vg00/data_snap
  Do you really want to remove active logical volume data_snap? [y/n]: y
  Logical volume "data_snap" successfully removed
The existing space is available again and can be divided.

root@ubuntu:~# vgs
  VG   #PV #LV #SN Attr   VSize VFree
  vg00   4   2   0 wz--n- 7.98g 2.00g
root@ubuntu:~# lvcreate -l50%FREE -s -n data_snap /dev/vg00/data
  Logical volume "data_snap" created
root@ubuntu:~# vgs
  VG   #PV #LV #SN Attr   VSize VFree
  vg00   4   3   1 wz--n- 7.98g 1.00g
root@ubuntu:~# lvcreate -l100%FREE -s -n data_snap1 /dev/vg00/data1
  Logical volume "data_snap1" created
If data in the file system is now changed as part of ongoing operations then its original content will first be copied into the snapshot. This block will also be flagged as "copied" in the exception table. Since the lvm2-format, snapshots are created as read/write by default. If a snapshot is accessed, the changed blocks will be flagged as "used" in the exception table and will never be copied from that point on. Regarding the size of the snapshot, a maximum of 1 GiB of "data" may be changed in the original volume, so that the snapshot will remain useful. If more data is changed on the original volume, the snapshot will be destroyed and lost.[5]

For creating a backup, the snapshot can be mounted as usual and backed up afterwards. In the example above, there was "data" located on the LV from the time point of the creation of "data_snap", based on which only a snapshot existed. This file should now be deleted and its existence in the snapshot verified.

root@ubuntu:~# mount /dev/vg00/data data
root@ubuntu:~# mount /dev/vg00/data_snap data_snap
root@ubuntu:~# cd data
root@ubuntu:~/data# l
  file  lost+found/
root@ubuntu:~/data# rm file
root@ubuntu:~/data# cd ..
root@ubuntu:~# cd data_snap/
root@ubuntu:~/data_snap# l
  file  lost+found/
The deleted file in the snapshot will remain available and can be also be backed up, or even restored, for that reason.
Partition Alignment detailed explanation
Main Page > Server Software
Main Page > Server Software > Linux > Linux-Storage > LVM
﻿Partition alignment is understood to mean the proper alignment of partitions to the reasonable boundaries of a data storage device (such as a hard disk, solid-state drive (SSD) or RAID volume). Proper partition alignment ensures ideal performance during data access. Incorrect partition alignment will cause reduced performance, especially with regard to SSDs (with an internal page size of 4,096 or 8,192 bytes, for example), hard disks with four-kilobyte (4,096 byte) sectors and RAID volumes.


Contents
1	A History of Partitions
2	Proper Partition Alignment
2.1	Virtualized Systems
2.2	Windows
2.3	Linux
2.3.1	fdisk (Older Versions)
2.3.2	fdisk from Version 2.17.1
2.3.3	Incorrect Alignment Example
2.3.4	Proper Alignment Example using Older Versions of fdisk
2.3.5	Proper Alignment Example using fdisk Versions 2.17.1 or later
2.3.6	Testing the Alignment
2.3.7	Logical Volume Manager
2.3.8	Software RAID
3	Table of References
4	Additional Information
A History of Partitions
In the past, the first partition always began at LBA Address 63, which corresponds to the sixty-fourth sector (see also CHS and LBA hard disk addressing). Such (logical) sectors had a size of 512 bytes. This was acceptable for normal hard disks (with a physical sector size of 512 bytes). Newer hard disks with a physical sector size of 4,096 bytes (four kilobytes) are really emulating a sector size of 512 bytes as far as external access is concerned, however internally they are working with 4,096 bytes. Even SSDs work with page sizes of four or eight kilobytes. Partitioning beginning at LBA Address 63 as such is a problem for these new hard disk and SSDs.

If partitions are formatted with a file system with a typical block size of four kilobytes, the four-kilobyte blocks for the file system will not directly fit into the four-kilobyte sectors for a hard disk or the four-, or eight-, kilobyte pages for an SSD. When a four-kilobyte file system block is written, two four-kilobyte sectors or pages will have to be modified. The fact that the respective 512-byte blocks must be maintained simply adds to the already difficult situation, meaning that a Read/Modify/Write process will have to be performed. A reduction in writing performance of up to a factor of 25 is the consequence during smaller data access attempts.[1]

Problems with incorrect partition alignment

Proper Partition Alignment
To avoid these problems, alignment at one-megabyte boundaries is recommended, which is a conservative approach over the long term. With the current addressing system divided in logical sectors of 512 bytes, doing so would correspond to 2,048 sectors.

Proper partition alignment ensures somewhat increased performance for SSDs

Virtualized Systems
The article, File System Alignment in Virtualized Environments, contains information about virtualized systems.

Windows
Newer version of Windows (Windows Vista, Windows 7 and Windows Server 2008) perform the following, reasonable alignment:[2][3]

Disk sizes less than or equal to four gigabytes should be aligned on sixty-four-kilobyte boundaries
Disk sizes larger than four gigabytes should be aligned on one-megabyte boundaries
Older versions of Windows will require manual alignment.[4]

Linux
fdisk (Older Versions)
With older version of fdisk, manual alignment can be achieved using the -S and -H flags. There are a variety of recommendations with regards to the specific number of sectors per track determined by the -S flag and the number of heads determined by the -H flag.[5][6][7] The -S 32 -H 64 flags will however definitely align along the one megabyte boundary (32 sectors per track by 64 heads by 512 bytes equals 1,048,576 bytes or 1 megabyte). Thereby, creation of the first partition will begin with Cylinder 2. Misalignment will occur using fdisk, if special parameters are not used.

fdisk from Version 2.17.1
With regard to util-linux-ng versions after 2.17.1, fdisk will align on the one megabyte boundary, if DOS compatibility mode has been disabled.[8]

The recommended settings for newer versions of fdisk are:[9]

Use the fdisk utility from util-linux-ng versions 2.17.2 or later
Read the fdsik warnings.
Deactivate DOS compatibility mode (the -c flag).
Use sectors as display units (the -u flag).
Use the +size(M, G) option in order to specify the end of a partition.
Incorrect Alignment Example
The following example shows an incorrect alignment. It is caused by DOS compatibility mode.

root@ubuntu-10-04:~# fdisk /dev/sdb
Device contains neither a valid DOS partition table, nor Sun, SGI or OSF disklabel
Building a new DOS disklabel with disk identifier 0xe4909079.
Changes will remain in memory only, until you decide to write them.
After that, of course, the previous content won't be recoverable.

Warning: invalid flag 0x0000 of partition table 4 will be corrected by w(rite)

WARNING: DOS-compatible mode is deprecated. It's strongly recommended to
         switch off the mode (command 'c') and change display units to
         sectors (command 'u').

Command (m for help): p

Disk /dev/sdb: 160.0 GB, 160041885696 bytes
255 heads, 63 sectors/track, 19457 cylinders
Units = cylinders of 16065 * 512 = 8225280 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0xe4909079

   Device Boot      Start         End      Blocks   Id  System

Command (m for help): n
Command action
   e   extended
   p   primary partition (1-4)
p
Partition number (1-4): 1
First cylinder (1-19457, default 1): 
Using default value 1
Last cylinder, +cylinders or +size{K,M,G} (1-19457, default 19457): +10G

Command (m for help): u
Changing display/entry units to sectors

Command (m for help): p

Disk /dev/sdb: 160.0 GB, 160041885696 bytes
255 heads, 63 sectors/track, 19457 cylinders, total 312581808 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0xe4909079

   Device Boot      Start         End      Blocks   Id  System
/dev/sdb1              63    20980889    10490413+  83  Linux

Command (m for help): 
Proper Alignment Example using Older Versions of fdisk
Partitions can be properly aligned using the -S 32 -H 64 flags, if the second cylinder is used as the starting point.

debian:~# fdisk -S 32 -H 64 /dev/sdc

The number of cylinders for this disk is set to 65536.
There is nothing wrong with that, but this is larger than 1024,
and could in certain setups cause problems with:
1) software that runs at boot time (e.g., old versions of LILO)
2) booting and partitioning software from other OSs
   (e.g., DOS FDISK, OS/2 FDISK)

Command (m for help): p

Disk /dev/sdc: 68.7 GB, 68719476736 bytes
64 heads, 32 sectors/track, 65536 cylinders
Units = cylinders of 2048 * 512 = 1048576 bytes
Disk identifier: 0x5a3b93b6

   Device Boot      Start         End      Blocks   Id  System

Command (m for help): n
Command action
   e   extended
   p   primary partition (1-4)
p
Partition number (1-4): 1
First cylinder (1-65536, default 1): 2
Last cylinder or +size or +sizeM or +sizeK (2-65536, default 65536): 
Using default value 65536

Command (m for help): p

Disk /dev/sdc: 68.7 GB, 68719476736 bytes
64 heads, 32 sectors/track, 65536 cylinders
Units = cylinders of 2048 * 512 = 1048576 bytes
Disk identifier: 0x5a3b93b6

   Device Boot      Start         End      Blocks   Id  System
/dev/sdc1               2       65536    67107840   83  Linux

Command (m for help): w
The partition table has been altered!

Calling ioctl() to re-read partition table.
Syncing disks.
debian:~# fdisk -lu /dev/sdc

Disk /dev/sdc: 68.7 GB, 68719476736 bytes
64 heads, 32 sectors/track, 65536 cylinders, total 134217728 sectors
Units = sectors of 1 * 512 = 512 bytes
Disk identifier: 0x5a3b93b6

   Device Boot      Start         End      Blocks   Id  System
/dev/sdc1            2048   134217727    67107840   83  Linux
debian:~# 
Proper Alignment Example using fdisk Versions 2.17.1 or later
Proper alignment can be achieved by deactivating DOS compatibility mode and setting the sector unit (the partition will start at the LBA Address 2,048. In the case of an SSD with a page size of four kilobytes, there will be 256 empty pages at the beginning of the disk. The partition will begin precisely at the start of Page 257).

root@ubuntu-10-04:~# fdisk -c -u /dev/sdb
Device contains neither a valid DOS partition table, nor Sun, SGI or OSF disklabel
Building a new DOS disklabel with disk identifier 0xfae13403.
Changes will remain in memory only, until you decide to write them.
After that, of course, the previous content won't be recoverable.

Warning: invalid flag 0x0000 of partition table 4 will be corrected by w(rite)

Command (m for help): p

Disk /dev/sdb: 160.0 GB, 160041885696 bytes
255 heads, 63 sectors/track, 19457 cylinders, total 312581808 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0xfae13403

   Device Boot      Start         End      Blocks   Id  System

Command (m for help): n
Command action
   e   extended
   p   primary partition (1-4)
p
Partition number (1-4): 1
First sector (2048-312581807, default 2048): 
Using default value 2048
Last sector, +sectors or +size{K,M,G} (2048-312581807, default 312581807): +10G

Command (m for help): p

Disk /dev/sdb: 160.0 GB, 160041885696 bytes
255 heads, 63 sectors/track, 19457 cylinders, total 312581808 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0xfae13403

   Device Boot      Start         End      Blocks   Id  System
/dev/sdb1            2048    20973567    10485760   83  Linux

Command (m for help): 
Testing the Alignment
Either of the two following commands will test alignment under Linux (replace /dev/sdX with the name of the device, such as /dev/sda).

sfdisk -d /dev/sdX
fdisk -l -u /dev/sdX
This example shows a system with an Ubuntu 10.04 installation. In this case, the Ubuntu 10.04 installer has aligned both the primary and the logical partitions at the one-megabyte boundary. This is indicated by the fact that the start sector number for the partition can be divided by 2,048 (2,048 sectors * 512 bytes per sector equals 1,048,576 or one megabyte). The extended partition (in this example, /dev/sda2) has not been aligned at the one-megabyte boundary. However, this is not required, since that partition merely serves as a container for the logical partitions and the logical partitions themselves are aligned at the one-megabyte boundaries.

user@ubuntu-test:~$ sudo sfdisk -d /dev/sda
Warning: extended partition does not start at a cylinder boundary.
DOS and Linux will interpret the contents differently.
# partition table of /dev/sda
unit: sectors

/dev/sda1 : start=     2048, size= 39061504, Id=83, bootable
/dev/sda2 : start= 39065598, size=1761810434, Id= 5
/dev/sda3 : start=        0, size=        0, Id= 0
/dev/sda4 : start=        0, size=        0, Id= 0
/dev/sda5 : start= 39065600, size=  3997696, Id=82
/dev/sda6 : start= 43065344, size=1757810688, Id=83
user@ubuntu-test:~$ sudo fdisk -l -u /dev/sda

Disk /dev/sda: 1000.2 GB, 1000204886016 bytes
255 heads, 63 sectors/track, 121601 cylinders, total 1953525168 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0x000d8343

   Device Boot      Start         End      Blocks   Id  System
/dev/sda1   *        2048    39063551    19530752   83  Linux
/dev/sda2        39065598  1800876031   880905217    5  Extended
/dev/sda5        39065600    43063295     1998848   82  Linux swap / Solaris
/dev/sda6        43065344  1800876031   878905344   83  Linux
user@ubuntu-test:~$ 
Logical Volume Manager
If the Logical Volume Manager (LVM) is used, proper alignment will still be an important issue.

As a rule, alignment should be automatic. Older versions of the LVM align at the sixty-four-kilobyte boundary, which places the beginning of the physical volumes at the beginning of a page for SSDs as well. An August 2010 patch now ensures alignment at the one-megabyte boundary. The patch is included in the LVM Version 2.02.73 from August 18th 2010.

lvm-devel RFC PATCH change default alignment of pe_start to 1MB (Mike Snitzer, linux-lvm mailing list, 05.08.2010)
lvm-devel RFC PATCH v2 change default alignment of pe_start to 1MB (Mike Snitzer, linux-lvm mailing list, 06.08.2010)
LVM2 What's New (Change default alignment of pe_start to 1MB.)
Re: (linux-lvm) LVM Alignement (Mike Snitzer, linux-lvm mailing list, 22.07.2011)
Software RAID
A Linux Software RAID array normally aligns properly. The superblock for RAID volumes using the older Superblock Metadata Version 0.90 is at the end of the device (in a block aligned on a sixty-four-kilobyte boundary). The RAID data starts at the beginning of the device. A software RAID array using the newer Superblock Metadata Version 1.* will align the data at the one megabyte boundary (see Linux Software RAID: Testing Alignment).
Linux Multi-Queue Block IO Queueing Mechanism (blk-mq) Details
Main Page > Server Software > Linux > Linux-Storage
blk-mq (Multi-Queue Block IO Queueing Mechanism) is a new framework for the Linux block layer that was introduced with Linux Kernel 3.13, and which has become feature-complete with Kernel 3.16.[1] Blk-mq allows for over 15 million IOPS with high-performance flash devices (e.g. PCIe SSDs) on 8-socket servers, though even single and dual socket servers also benefit considerably from blk-mq.[2] To use a device with blk-mq, the device must support the respective driver.

This article explains how blk-mq integrates into the Linux storage stack and which devices have blk-mq compatible drivers already included in the Linux kernel.


Contents
1	blk-mq in the Linux Storage Stack
2	Device Drivers
3	Additional Resources
4	References
blk-mq in the Linux Storage Stack

Two-level Linux block layer design of blk-mq.[2]
Blk-mq integrates seamlessly into the Linux storage stack. It provides basic functions to device drivers for mapping I/O enquiries to multiple queues. The tasks are distributed across multiple threads and therefore to multiple CPU cores (per-core software queues). Blk-mq compatible drivers inform blk-mq how many parallel hardware queues a device supports (number of submission queues as part of the hardware dispatch queue registration).

Blk-mq-based device drivers bypass the previous Linux I/O scheduler. In the past, some drivers without blk-mq already performed this (iomemory-vsl, nvme, mtip32xx), but these had to establish as bio-based (block-I/O-based) drivers many generic functions on their own ("stacked" approach).

All device drivers that use the previous block I/O layer continue to work independently of blk-mq as request-based drivers according to the Linux I/O scheduler (request_fn based approach, see Linux I/O Stack Diagram).[3] How much longer this request_fn based approach will exist in the Linux kernel is currently unclear (July 2014).[4][5]

Device Drivers
Driver	Device Name	Supported Devices	blk-mq Since Kernel Version
null_blk	/dev/nullb*[6]	none (test drivers)	3.13 (git commit)
virtio-blk	/dev/vd*	Virtual guest drivers (e.g. under KVM[7][8])	3.13 (git commit)
mtip32xx	/dev/rssd*	Micron RealSSD PCIe	3.16 (git commit)
scsi (scsi_mq)	/dev/sd*	e.g. SAS and SATA SSDs/HDDs	3.17 (git commit)
NVMe	/dev/nvme*	e.g. Intel SSD DC P3600 DC P3700 Series[9]	3.19 (git commit)
rbd	/dev/rdb*	RADOS Block Device (Ceph)	4.0 (git commit)
ubi/block	/dev/ubiblock*		4.0 (git commit)
loop	/dev/loop*	Loopback-Device	4.0 (git commit)
dm / dm-mpath		request-based device mapper targets (derzeit ist dies ausschließlich dm-multipath)	planned for 4.1[10]
nalyzing a Faulty Hard Disk using Smartctl
Main Page > Server Software > Linux > Linux-Storage > Smartmontools
Under Linux, you can read the SMART (Self-Monitoring, Analysis and Reporting Technology) information from the hard disk using smartctl. In this example, we will show how to analyze a defective hard disk. The hard disk in this example can no longer read several sectors and is therefore defective. It has to be replaced.


Contents
1	Displaying SMART Information
1.1	Analysis
2	SMART Tests
2.1	Short Test
2.2	Displaying the Test Results
2.3	Forcing Re-mapping a Defective Sector
3	References
Displaying SMART Information
The smartctl -a /dev/DEVICENAME command will display all SMART information for the affected hard disk. The hard disk in this example is showing increased errors for multiple SMART settings.

root@ubuntu-10-10:~# smartctl -a /dev/sdb
smartctl 5.40 2010-03-16 r3077 [x86_64-unknown-linux-gnu] (local build)
Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF INFORMATION SECTION ===
Model Family:     SAMSUNG SpinPoint F2 EG series
Device Model:     SAMSUNG HD502HI
Serial Number:    S1VZJ9CS712490
Firmware Version: 1AG01118
User Capacity:    500,107,862,016 bytes
Device is:        In smartctl database [for details use: -P show]
ATA Version is:   8
ATA Standard is:  ATA-8-ACS revision 3b
Local Time is:    Wed Feb  9 15:30:42 2011 CET
SMART support is: Available - device has SMART capability.
SMART support is: Enabled

=== START OF READ SMART DATA SECTION ===
SMART overall-health self-assessment test result: PASSED

General SMART Values:
Offline data collection status:  (0x00)    Offline data collection activity
                    was never started.
                    Auto Offline Data Collection: Disabled.
Self-test execution status:      (   0)    The previous self-test routine completed
                    without error or no self-test has ever 
                    been run.
Total time to complete Offline 
data collection:          (6312) seconds.
Offline data collection
capabilities:              (0x7b) SMART execute Offline immediate.
                    Auto Offline data collection on/off support.
                    Suspend Offline collection upon new
                    command.
                    Offline surface scan supported.
                    Self-test supported.
                    Conveyance Self-test supported.
                    Selective Self-test supported.
SMART capabilities:            (0x0003)    Saves SMART data before entering
                    power-saving mode.
                    Supports SMART auto save timer.
Error logging capability:        (0x01)    Error logging supported.
                    General Purpose Logging supported.
Short self-test routine 
recommended polling time:      (   2) minutes.
Extended self-test routine
recommended polling time:      ( 106) minutes.
Conveyance self-test routine
recommended polling time:      (  12) minutes.
SCT capabilities:            (0x003f)    SCT Status supported.
                    SCT Error Recovery Control supported.
                    SCT Feature Control supported.
                    SCT Data Table supported.

SMART Attributes Data Structure revision number: 16
Vendor Specific SMART Attributes with Thresholds:
ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
  1 Raw_Read_Error_Rate     0x000f   099   099   051    Pre-fail  Always       -       2376
  3 Spin_Up_Time            0x0007   091   091   011    Pre-fail  Always       -       3620
  4 Start_Stop_Count        0x0032   100   100   000    Old_age   Always       -       405
  5 Reallocated_Sector_Ct   0x0033   100   100   010    Pre-fail  Always       -       0
  7 Seek_Error_Rate         0x000f   253   253   051    Pre-fail  Always       -       0
  8 Seek_Time_Performance   0x0025   100   100   015    Pre-fail  Offline      -       0
  9 Power_On_Hours          0x0032   100   100   000    Old_age   Always       -       717
 10 Spin_Retry_Count        0x0033   100   100   051    Pre-fail  Always       -       0
 11 Calibration_Retry_Count 0x0012   100   100   000    Old_age   Always       -       0
 12 Power_Cycle_Count       0x0032   100   100   000    Old_age   Always       -       405
 13 Read_Soft_Error_Rate    0x000e   099   099   000    Old_age   Always       -       2375
183 Runtime_Bad_Block       0x0032   100   100   000    Old_age   Always       -       0
184 End-to-End_Error        0x0033   100   100   000    Pre-fail  Always       -       0
187 Reported_Uncorrect      0x0032   100   100   000    Old_age   Always       -       2375
188 Command_Timeout         0x0032   100   100   000    Old_age   Always       -       0
190 Airflow_Temperature_Cel 0x0022   084   074   000    Old_age   Always       -       16 (Lifetime Min/Max 16/16)
194 Temperature_Celsius     0x0022   084   071   000    Old_age   Always       -       16 (Lifetime Min/Max 16/16)
195 Hardware_ECC_Recovered  0x001a   100   100   000    Old_age   Always       -       3558
196 Reallocated_Event_Count 0x0032   100   100   000    Old_age   Always       -       0
197 Current_Pending_Sector  0x0012   098   098   000    Old_age   Always       -       81
198 Offline_Uncorrectable   0x0030   100   100   000    Old_age   Offline      -       0
199 UDMA_CRC_Error_Count    0x003e   100   100   000    Old_age   Always       -       1
200 Multi_Zone_Error_Rate   0x000a   100   100   000    Old_age   Always       -       0
201 Soft_Read_Error_Rate    0x000a   253   253   000    Old_age   Always       -       0

SMART Error Log Version: 1
No Errors Logged

SMART Self-test log structure revision number 1
No self-tests have been logged.  [To run self-tests, use: smartctl -t]


SMART Selective self-test log data structure revision number 1
 SPAN  MIN_LBA  MAX_LBA  CURRENT_TEST_STATUS
    1        0        0  Not_testing
    2        0        0  Not_testing
    3        0        0  Not_testing
    4        0        0  Not_testing
    5        0        0  Not_testing
Selective self-test flags (0x0):
  After scanning selected spans, do NOT read-scan remainder of disk.
If Selective self-test is pending on power-up, resume after 0 minute delay.

root@ubuntu-10-10:~#
Analysis
In this example, the following values are interesting for the detailed analysis.

  1 Raw_Read_Error_Rate     0x000f   099   099   051    Pre-fail  Always       -       2376
 13 Read_Soft_Error_Rate    0x000e   099   099   000    Old_age   Always       -       2375
187 Reported_Uncorrect      0x0032   100   100   000    Old_age   Always       -       2375
195 Hardware_ECC_Recovered  0x001a   100   100   000    Old_age   Always       -       3558
197 Current_Pending_Sector  0x0012   098   098   000    Old_age   Always       -       81
199 UDMA_CRC_Error_Count    0x003e   100   100   000    Old_age   Always       -       1
The RAW_VALUE of the Current_Pending_Sector value indicates how many of the hard disks sectors can no longer be read and are waiting for re-mapping.[1] You will find detailed information about the other error codes in the ATA S.M.A.R.T. Attributes section of the Wikipedia article about SMART.[2]

SMART Tests
SMART supports several hard disk tests. You can find the details on the man page for smartctl.

Short Test
We will start a short test in this example.

root@ubuntu-10-10:~# smartctl -t short /dev/sdb
smartctl 5.40 2010-03-16 r3077 [x86_64-unknown-linux-gnu] (local build)
Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF OFFLINE IMMEDIATE AND SELF-TEST SECTION ===
Sending command: "Execute SMART Short self-test routine immediately in off-line mode".
Drive command "Execute SMART Short self-test routine immediately in off-line mode" successful.
Testing has begun.
Please wait 2 minutes for test to complete.
Test will complete after Wed Feb  9 15:35:31 2011

Use smartctl -X to abort test.
root@ubuntu-10-10:~#
Displaying the Test Results
The test results will be displayed by the command: smartctl -l selftest /dev/sdb. The LBA address is obviously the first defective sector in this example.

root@ubuntu-10-10:~# smartctl -l selftest /dev/sdb
smartctl 5.40 2010-03-16 r3077 [x86_64-unknown-linux-gnu] (local build)
Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF READ SMART DATA SECTION ===
SMART Self-test log structure revision number 1
Num  Test_Description    Status                  Remaining  LifeTime(hours)  LBA_of_first_error
# 1  Short offline       Completed: read failure       20%       717         555027747

root@ubuntu-10-10:~#
Forcing Re-mapping a Defective Sector
When you write to a defective sector, the hard disk will attempt to re-map the affected sector. The original content of the sector will be lost by this procedure. You will find details about this on the Bad Block HOWTO page.[3]

The following command will display the remapping process for a sector. The Current_Pending_Sector counter will be reduced (these steps were performed according to the Bad Block HOWTO page).

root@ubuntu-10-10:~# fdisk -lu /dev/sdb

Disk /dev/sdb: 500.1 GB, 500107862016 bytes
255 heads, 63 sectors/track, 60801 cylinders, total 976773168 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0x20d1585d

   Device Boot      Start         End      Blocks   Id  System
/dev/sdb1   *        2048      206847      102400    7  HPFS/NTFS
Partition 1 does not end on cylinder boundary.
/dev/sdb2          206848    97863097    48828125    7  HPFS/NTFS
/dev/sdb3        97868041   976768064   439450012    5  Extended
/dev/sdb5        97868043   964703249   433417603+  83  Linux
/dev/sdb6       964703313   976768064     6032376   82  Linux swap / Solaris
root@ubuntu-10-10:~# tune2fs -l /dev/sdb5 | grep Block
Block count:              108354400
Block size:               4096
Blocks per group:         32768
root@ubuntu-10-10:~# debugfs 
debugfs 1.41.12 (17-May-2010)
debugfs:  open /dev/sdb5
debugfs:  testb 57144963
Block 57144963 not in use
debugfs:  quit
root@ubuntu-10-10:~# dd if=/dev/zero of=/dev/sdb5 bs=4096 count=1 seek=57144963
1+0 records in
1+0 records out
4096 bytes (4,1 kB) copied, 0,000379164 s, 10,8 MB/s
root@ubuntu-10-10:~# sync
root@ubuntu-10-10:~# smartctl -A /dev/sdb
smartctl 5.40 2010-03-16 r3077 [x86_64-unknown-linux-gnu] (local build)
Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF READ SMART DATA SECTION ===
SMART Attributes Data Structure revision number: 16
Vendor Specific SMART Attributes with Thresholds:
ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
[...]
197 Current_Pending_Sector  0x0012   098   098   000    Old_age   Always       -       80
[...]
Another set of tests will be started and another remapping procedure will be performed.

root@ubuntu-10-10:~# smartctl -t short /dev/sdb
smartctl 5.40 2010-03-16 r3077 [x86_64-unknown-linux-gnu] (local build)
Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF OFFLINE IMMEDIATE AND SELF-TEST SECTION ===
Sending command: "Execute SMART Short self-test routine immediately in off-line mode".
Drive command "Execute SMART Short self-test routine immediately in off-line mode" successful.
Testing has begun.
Please wait 2 minutes for test to complete.
Test will complete after Wed Feb  9 15:47:41 2011

Use smartctl -X to abort test.
root@ubuntu-10-10:~# smartctl -l selftest /dev/sdb
smartctl 5.40 2010-03-16 r3077 [x86_64-unknown-linux-gnu] (local build)
Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF READ SMART DATA SECTION ===
SMART Self-test log structure revision number 1
Num  Test_Description    Status                  Remaining  LifeTime(hours)  LBA_of_first_error
# 1  Short offline       Completed: read failure       20%       717         555027784
# 2  Short offline       Completed: read failure       20%       717         555027747

root@ubuntu-10-10:~# debugfs 
debugfs 1.41.12 (17-May-2010)
debugfs:  open /dev/sdb5
debugfs:  testb 57144967
Block 57144967 not in use
debugfs:  quit
root@ubuntu-10-10:~# dd if=/dev/zero of=/dev/sdb5 bs=4096 count=1 seek=57144967
1+0 records in
1+0 records out
4096 bytes (4,1 kB) copied, 0,000374713 s, 10,9 MB/s
root@ubuntu-10-10:~# smartctl -A /dev/sdb
smartctl 5.40 2010-03-16 r3077 [x86_64-unknown-linux-gnu] (local build)
Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF READ SMART DATA SECTION ===
SMART Attributes Data Structure revision number: 16
Vendor Specific SMART Attributes with Thresholds:
ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
[...]
197 Current_Pending_Sector  0x0012   098   098   000    Old_age   Always       -       79
[...]

Smartmontools with MegaRAID Controller
Main Page > Server Hardware > RAID Controllers > LSI
Main Page > Server Software > Linux > Linux-Storage > Smartmontools
The smartctl Command Line Tool of Smartmontools is primarily used to query SMART attributes of hard drives and SSDs that are connected directly to the motherboard or to an HBA on a server. In addition to this conventional way the Smartmontools also support querying SMART attributes of hard drives/SSDs, which are connected to an LSI RAID controller.[1]

This article shows you how to query SMART attributes of hard drives and SSDs that are connected to an LSI RAID controller.

Checking for hard disk access
Using

cat /proc/scsi/scsi
can display which disks of the RAID controller are accessible.
Output example:

Attached devices:
Host: scsi0 Channel: 02 Id: 00 Lun: 00
  Vendor: LSI      Model: MR9271-4i        Rev: 3.27
  Type:   Direct-Access                    ANSI  SCSI revision: 05
Host: scsi0 Channel: 02 Id: 01 Lun: 00
  Vendor: LSI      Model: MR9271-4i        Rev: 3.27
  Type:   Direct-Access                    ANSI  SCSI revision: 05
Host: scsi2 Channel: 00 Id: 00 Lun: 00
  Vendor: ATA      Model: WDC WD5003ABYX-0 Rev: 01.0
  Type:   Direct-Access                    ANSI  SCSI revision: 05
Host: scsi3 Channel: 00 Id: 00 Lun: 00
  Vendor: ATA      Model: WDC WD5003ABYX-0 Rev: 01.0
  Type:   Direct-Access                    ANSI  SCSI revision: 05
RAID volumes in this example are marked by the string "Vendor: LSI". One or more hard drives or SSDs can hide behind each RAID volume.

Access to hard disks with smartctl
smartctl provides integrated support for MegaRAID controller. Access is made in the following manner:

sudo smartctl -a -d megaraid,N  /dev/sdX
Where <N> stands for the device ID on the RAID controller. These can be displayed via the StorCLI (column DID).

sudo storcli /c0 /eall /sall show
Output example:

Controller = 0
Status = Success
Description = Show Drive Information Succeeded.


Drive Information :
=================

------------------------------------------------------------------------------
EID:Slt DID State DG      Size Intf Med SED PI SeSz Model                  Sp 
------------------------------------------------------------------------------
252:0     7 Onln   0 465.25 GB SATA HDD N   N  512B WDC WD5003ABYX-01WERA1 U  
252:1     6 Onln   1 465.25 GB SATA HDD N   N  512B WDC WD5003ABYX-01WERA1 U  
252:2     5 Onln   2   74.0 GB SATA SSD N   N  512B INTEL SSDSC2BB080G4    U  
252:3     4 Onln   2   74.0 GB SATA SSD N   N  512B INTEL SSDSC2BB080G4    U  
------------------------------------------------------------------------------

EID-Enclosure Device ID|Slt-Slot No.|DID-Device ID|DG-DriveGroup
DHS-Dedicated Hot Spare|UGood-Unconfigured Good|GHS-Global Hotspare
UBad-Unconfigured Bad|Onln-Online|Offln-Offline|Intf-Interface
Med-Media Type|SED-Self Encryptive Drive|PI-Protection Info
SeSz-Sector Size|Sp-Spun|U-Up|D-Down|T-Transition|F-Foreign
UGUnsp-Unsupported
The type of block devices is necessary, but the SMART data on the disk that has the appropriate device ID will always be displayed on the RAID controller. For example, this can also display SMART data from hard disks that has not been passed on by the RAID controller to the operating system. So, for example, it shows the following commands of different SMART data, although the same block device was specified.

sudo smartctl -a -d megaraid,5  /dev/sdc
sudo smartctl -a -d megaraid,6  /dev/sdc

Smartctl Tool
Main Page > Server Software > Linux > Linux-Storage > Smartmontools
smartctl is a command line tool for controlling the SMART (Self-Monitoring, Analysis and Reporting Technology) features of hard disks and SSDs, and a component of Smartmontools. The objective of SMART[1] is to monitor the reliability of hard disks and SSDs, as well as to give the ability to run certain drive tests. The Smartmontools[2] include the command line tool smartctl and the smartd Daemon. The Smartmontools are available in a wide selection of our most popular operating systems (Darwin (Mac OS X), Linux, FreeBSD, NetBSD, OpenBSD, Solaris, OS/2, Cygwin, QNX, eComStation, Windows). The article, however, refers to the Linux version.


Contents
1	Installation
2	Usage
2.1	Viewing the SMART Attributes
2.2	Important SMART Attributes
2.3	Performing of Tests
3	References
Installation
Smartmontools is available in the repositories of many Linux distributions. For Ubuntu, install the package with the following command:

sudo apt-get install smartmontools
Now smartctl is ready for use.

Usage
Before using smartctl, check to see if the hard disk in use supports S.M.A.R.T.:

sudo smartctl -i /dev/sdc
The following data should be present in the output:

SMART support is: Available - device has SMART capability.
SMART support is: Enabled
In case SMART support is available, but for some reason is not activated, try using

sudo smartctl -s on /dev/sdc
to assist with activation.

Viewing the SMART Attributes
To display the SMART attributes of the hard disk, perform the following command:

sudo smartctl -a /dev/sdc
Example output:

smartctl 5.41 2011-06-09 r3365 [x86_64-linux-3.5.0-39-generic] (local build)
Copyright (C) 2002-11 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF INFORMATION SECTION ===
Model Family:     Western Digital RE4 Serial ATA
Device Model:     WDC WD5003ABYX-01WERA1
Serial Number:    WD-WMAYP5453158
LU WWN Device Id: 5 0014ee 00385d526
Firmware Version: 01.01S02
User Capacity:    500,107,862,016 bytes [500 GB]
Sector Size:      512 bytes logical/physical
Device is:        In smartctl database [for details use: -P show]
ATA Version is:   8
ATA Standard is:  Exact ATA specification draft version not indicated
Local Time is:    Tue Sep  3 09:05:27 2013 CEST
SMART support is: Available - device has SMART capability.
SMART support is: Enabled

=== START OF READ SMART DATA SECTION ===
SMART overall-health self-assessment test result: PASSED

General SMART Values:
Offline data collection status:  (0x82)	Offline data collection activity
					was completed without error.
					Auto Offline Data Collection: Enabled.
Self-test execution status:      (   0)	The previous self-test routine completed
					without error or no self-test has ever 
					been run.
Total time to complete Offline 
data collection: 		( 8160) seconds.
Offline data collection
capabilities: 			 (0x7b) SMART execute Offline immediate.
					Auto Offline data collection on/off support.
					Suspend Offline collection upon new
					command.
					Offline surface scan supported.
					Self-test supported.
					Conveyance Self-test supported.
					Selective Self-test supported.
SMART capabilities:            (0x0003)	Saves SMART data before entering
					power-saving mode.
					Supports SMART auto save timer.
Error logging capability:        (0x01)	Error logging supported.
					General Purpose Logging supported.
Short self-test routine 
recommended polling time: 	 (   2) minutes.
Extended self-test routine
recommended polling time: 	 (  83) minutes.
Conveyance self-test routine
recommended polling time: 	 (   5) minutes.
SCT capabilities: 	       (0x303f)	SCT Status supported.
					SCT Error Recovery Control supported.
					SCT Feature Control supported.
					SCT Data Table supported.

SMART Attributes Data Structure revision number: 16
Vendor Specific SMART Attributes with Thresholds:
ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
  1 Raw_Read_Error_Rate     0x002f   200   200   051    Pre-fail  Always       -       0
  3 Spin_Up_Time            0x0027   144   143   021    Pre-fail  Always       -       3775
  4 Start_Stop_Count        0x0032   100   100   000    Old_age   Always       -       28
  5 Reallocated_Sector_Ct   0x0033   200   200   140    Pre-fail  Always       -       0
  7 Seek_Error_Rate         0x002e   200   200   000    Old_age   Always       -       0
  9 Power_On_Hours          0x0032   098   098   000    Old_age   Always       -       2090
 10 Spin_Retry_Count        0x0032   100   253   000    Old_age   Always       -       0
 11 Calibration_Retry_Count 0x0032   100   253   000    Old_age   Always       -       0
 12 Power_Cycle_Count       0x0032   100   100   000    Old_age   Always       -       27
192 Power-Off_Retract_Count 0x0032   200   200   000    Old_age   Always       -       24
193 Load_Cycle_Count        0x0032   200   200   000    Old_age   Always       -       3
194 Temperature_Celsius     0x0022   117   103   000    Old_age   Always       -       26
196 Reallocated_Event_Count 0x0032   200   200   000    Old_age   Always       -       0
197 Current_Pending_Sector  0x0032   200   200   000    Old_age   Always       -       0
198 Offline_Uncorrectable   0x0030   200   200   000    Old_age   Offline      -       0
199 UDMA_CRC_Error_Count    0x0032   200   200   000    Old_age   Always       -       0
200 Multi_Zone_Error_Rate   0x0008   200   200   000    Old_age   Offline      -       0

SMART Error Log Version: 1
No Errors Logged

SMART Self-test log structure revision number 1
Num  Test_Description    Status                  Remaining  LifeTime(hours)  LBA_of_first_error
# 1  Short offline       Completed without error       00%      2089         -
# 2  Extended offline    Completed without error       00%      2087         -
# 3  Short offline       Completed without error       00%      2084         -

SMART Selective self-test log data structure revision number 1
 SPAN  MIN_LBA  MAX_LBA  CURRENT_TEST_STATUS
    1        0        0  Not_testing
    2        0        0  Not_testing
    3        0        0  Not_testing
    4        0        0  Not_testing
    5        0        0  Not_testing
Selective self-test flags (0x0):
  After scanning selected spans, do NOT read-scan remainder of disk.
If Selective self-test is pending on power-up, resume after 0 minute delay.
Important SMART Attributes
The following parameters may provide information concerning an impending hard drive failure.

Reallocated Sectors Count: Number of sectors that have been reallocated due to read errors (remaped).
Spin Retry Count: Number of attempts that have been required ot bring the spindel to operating speed.
Reallocation Event Count: Number of remaps that have been carried out both (successful and unsuccessful).
Current Pending Sector Count: Number of sectors waiting for remapping.
Offline_Uncorrectable: Number of uncorrectable errors when accessing (read/write) to sectors.
Performing of Tests
For information regarding performing SMART tests, see the following article: SMART tests with smartctl.

SMART tests with smartctl
Main Page > Server Software > Linux > Linux-Storage > Smartmontools
All modern hard drives offer the possibility to monitor its current state via SMART attributes. These values ​​provide information about various parameters of the hard disk and can provide information on the disk's remaining lifespan or on any possible errors. In addition, various SMART tests can be performed to determine any hardware problems on the disk. This article describes how such tests can be performed for Linux using smartctl (Smartmontools).


Contents
1	Installation of Smartmontools
2	Available Tests
2.1	ATA/SCSI Tests
2.1.1	Short Test
2.1.2	Long Test
2.2	ATA specified Tests
2.2.1	Conveyance Test
2.2.2	Select Tests
3	Test procedure with smartctl
4	Viewing the Test Results
5	References
Installation of Smartmontools
The Smartmontools can be installed on Ubuntu using the package sources:

sudo apt-get install smartmontools
To ensure the hard disk supports SMART and is enabled, use the following command (in this example for the hard disk /dev/sdc):

sudo smartctl -i /dev/sdc
Example Output:

smartctl 5.41 2011-06-09 r3365 [x86_64-linux-3.5.0-39-generic] (local build)
Copyright (C) 2002-11 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF INFORMATION SECTION ===
Model Family:     Western Digital RE4 Serial ATA
Device Model:     WDC WD5003ABYX-01WERA1
Serial Number:    WD-WMAYP5453158
LU WWN Device Id: 5 0014ee 00385d526
Firmware Version: 01.01S02
User Capacity:    500,107,862,016 bytes [500 GB]
Sector Size:      512 bytes logical/physical
Device is:        In smartctl database [for details use: -P show]
ATA Version is:   8
ATA Standard is:  Exact ATA specification draft version not indicated
Local Time is:    Mon Sep  2 14:06:57 2013 CEST
SMART support is: Available - device has SMART capability.
SMART support is: Enabled
The last two lines are the most important as these indicate whether SMART support is available and enabled.

Available Tests
SMART offers two different tests, according to specification type, for and SCSI devices.[1] Each of these tests can be performed in two modes:

Foreground Mode
Background Mode
In Background Mode the priority of the test is low, which means the normal instructions continue to be processed by the hard disk. If the hard drive is busy, the test is paused and then continues at a lower load speed, so there is no interruption of the operation.
In Foreground Mode all commands will be answered during the test with a "CHECK CONDITION" status. Therefore, this mode is only recommended when the hard disk is not used. In principle, the background mode is the preferred mode.

ATA/SCSI Tests
Short Test
The goal of the short test is the rapid identification of a defective hard drive. Therefore, a maximum run time for the short test is 2 min. The test checks the disk by dividing it into three different segments. The following areas are tested:

Electrical Properties: The controller tests its own electronics, and since this is specific to each manufacturer, it cannot be explained exactly what is being tested. It is conceivable, for example, to test the internal RAM, the read/write circuits or the head electronics.
Mechanical Properties: The exact sequence of the servos and the positioning mechanism to be tested is also specific to each manufacturer.
Read/Verify: It will read a certain area of ​​the disk and verify certain data, the size and position of the region that is read is also specific to each manufacturer.
Long Test
The long test was designed as the final test in production and is the same as the short test with two differences. The first: there is no time restriction and in the Read/Verify segment the entire disk is checked and not just a section. The Long test can, for example, be used to confirm the results of the short tests.

ATA specified Tests
All tests listed here are only available for ATA hard drives.

Conveyance Test
This test can be performed to determine damage during transport of the hard disk within just a few minutes.

Select Tests
During selected tests the specified range of LBAs is checked. The LBAs to be scanned are specified in the following formats:

sudo smartctl -t select,10-20 /dev/sdc #LBA 10 to LBA 20 (incl.)
sudo smartctl -t select,10+11 /dev/sdc #LBA 10 to LBA 20 (incl.)
It is also possible to have multiple ranges, (up to 5), to scan:

sudo smartctl -t select,0-10 -t select,5-15 -t select,10-20 /dev/sdc
Test procedure with smartctl
Before performing a test, an approximate indication of the time duration of the various tests are displayed using the following command:

sudo smartctl -c /dev/sdc
Example output:

[...]
Short self-test routine 
recommended polling time: 	 (   2) minutes.
Extended self-test routine
recommended polling time: 	 (  83) minutes.
Conveyance self-test routine
recommended polling time: 	 (   5) minutes.
[...]
The following command starts the desired test (in Background Mode):

sudo smartctl -t <short|long|conveyance|select> /dev/sdc
It is also possible to perform an "offline" test.[2] However, only of the standard self test (Short Test) is performed.

Example output:

smartctl 5.41 2011-06-09 r3365 [x86_64-linux-3.5.0-39-generic] (local build)
Copyright (C) 2002-11 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF OFFLINE IMMEDIATE AND SELF-TEST SECTION ===
Sending command: "Execute SMART Short self-test routine immediately in off-line mode".
Drive command "Execute SMART Short self-test routine immediately in off-line mode" successful.
Testing has begun.
Please wait 2 minutes for test to complete.
Test will complete after Mon Sep  2 15:32:30 2013

Use smartctl -X to abort test.
To perform the tests in Foreground Mode a "-C" must be added to the command.

sudo smartctl -t <short|long|conveyance|select> -C /dev/sdc
Viewing the Test Results
In general, the test results are included in the output of the following commands:

sudo smartctl -a /dev/sdc
Example:

[...]
SMART Self-test log structure revision number 1
Num  Test_Description    Status                  Remaining  LifeTime(hours)  LBA_of_first_error
# 1  Short offline       Completed without error       00%      2089         -
# 2  Extended offline    Completed without error       00%      2087         -
# 3  Short offline       Completed without error       00%      2084         -

SMART Selective self-test log data structure revision number 1
 SPAN  MIN_LBA  MAX_LBA  CURRENT_TEST_STATUS
    1        0        0  Not_testing
    2        0        0  Not_testing
    3        0        0  Not_testing
    4        0        0  Not_testing
    5        0        0  Not_testing
Selective self-test flags (0x0):
  After scanning selected spans, do NOT read-scan remainder of disk.
If Selective self-test is pending on power-up, resume after 0 minute delay.
[...]
The following command can also be used, if only the test results should are displayed:

sudo smartctl -l selftest /dev/sdc
Example output:

smartctl 5.41 2011-06-09 r3365 [x86_64-linux-3.5.0-39-generic] (local build)
Copyright (C) 2002-11 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF READ SMART DATA SECTION ===
SMART Self-test log structure revision number 1
Num  Test_Description    Status                  Remaining  LifeTime(hours)  LBA_of_first_error
# 1  Short offline       Completed without error       00%      2089         -
# 2  Extended offline    Completed without error       00%      2087         -
# 3  Short offline       Completed without error       00%      2084         -
In the english Wikipedia article on SMART, a list of known attributes SMART Attributen including a short description is given.

SMART Attributes Monitoring Plugin setup
Main Page > Network+Accessories > Monitoring
Main Page > Server Software > Linux > Linux-Storage > Smartmontools
The Smart Attributes Monitoring Plugin allows you to monitor the Smart-Values of SSDs and hard disks. The plugin is written in the scripting language Perl and uses smartctl to query the values. The plugin is necessary as an interpretation of the smart attributes is not normed. Each manufacturer has its own definition of evaluating smart attributes. The plugin provides an easy way to define definitions and monitor SSDs and HDDs correctly.


Percent Lifetime and Temperature are displayed as performance data.

Contents
1	Current Version
1.1	Functionalities
2	Requirements
3	Example Plugin Outputs
4	Installation
5	Configuration
5.1	Via NRPE
5.1.1	On Icinga Servers
5.1.2	On Monitored Servers
5.2	Local
Current Version
The current version of check_smart_attributes plugins can be obtained from GitHub:

https://github.com/thomas-krenn/check_smart_attributes.git
Functionalities
The plugin README lists all available checks:

Version 1.3 Plugin README (github.com)
Requirements
The installation conditions will be explained in more detail in the following section:

On monitored servers
check_smart_attributes plugin installed
libconfig-json-perl installed
smartmontools (smartctl) installed
sudoers record for nagios and smartctl users
If via NRPE, the command definition for NRPE
On Icinga servers
Command Definition
Service Definition
Example Plugin Outputs
:~$ sudo ./check_smart_attributes -d /dev/sda -d /dev/sdc -dbj ./check_smartdb.json
Critical (sda, sdc) [sdc_Raw_Read_Error_Rate = Critical][sdc_Reallocated_Sector_Ct = Critical][sdc_UDMA_CRC_Error_Count = Critical][sdc_ATA_Error_Count = Critical]
[sda_CRC_Error_Count = Warning]|sda_Media_Wearout_Indicator=097;16;6 sda_Host_Writes_32MiB=517485 sda_Host_Reads_32MiB=395618 sdc_Temperature_Celsius=40
Installation
For the installation the Plugin-File is copied into the directory /usr/lib/nagios/plugins. The Lookup-JSON-File comes to /etc/nagios-plugins/config/.

:~$ git clone https://github.com/thomas-krenn/check_smart_attributes.git
Cloning into 'check_smart_attributes'...
:~$ cd check_smart_attributes/
:~$ sudo cp check_smart_attributes /usr/lib/nagios/plugins/
:~$ sudo cp check_smartdb.json /etc/nagios-plugins/config/
The perl library Config::JSON is needed to read the smartdb in JSON-format:

:~$ sudo apt-get install libconfig-json-perl
The command line tool smartctl is installed via the package smartmontools:

:~$ sudo apt-get install smartmontools 
Configuration
The plugin is suitable for smart monitoring of a remote server via NRPE, as well as for monitoring a local host. Regardless, the check_smart_attributes plugin must be installed on the monitored system.

Via NRPE
On Icinga Servers
When a host definition is created, a command is defined that is performed via NRPE. The parameters themselves are specificed on the monitored host.

define service {
    service_description           smart_attributes-nrpe
    display_name                  SMART attributes
    use                           generic-service
    host_name                     test
    check_command                 check_nrpe_1arg!check_smart_attributes
}
On Monitored Servers
With this, the nagios user can run the command line tool without entering a password. The following pseudo-configuration muss be defined:

:~$ sudo vi /etc/sudoers.d/check_smart_attributes
nagios ALL=(root)NOPASSWD:/usr/sbin/smartctl
:~$ sudo chmod 440 /etc/sudoers.d/check_smart_attributes
The following test does not require entry of a password:

:~$ sudo su nagios --shell /bin/bashs
:~$ sudo smartctl -V
smartctl 5.41 2011-06-09 r3365 [x86_64-linux-3.2.0-48-generic] (local build)
Copyright (C) 2002-11 by Bruce Allen, http://smartmontools.sourceforge.net
[...]
An NRPE-Configuration-File specifies which check is performed when the command check_smart_attributes is called up. This command must correspond with the Host Definition parameters on the Icinga server page:

:~$ sudo vi /etc/nagios/nrpe.d/smart.cfg
command[check_smart_attributes]=/usr/lib/nagios/plugins/check_smart_attributes -d /dev/sda -dbj /etc/nagios-plugins/config/check_smartdb.json
Caution: The specified smartdb JSON file must be able to be read by the nagios users.

:~$ sudo service nagios-nrpe-server restart
The check can be tested on the Icinga side to see if it functions correctly:

:~$ /usr/lib/nagios/plugins/check_nrpe -H 10.0.0.2 -c check_smart_attributes
Critical (sda) [sda_CRC_Error_Count = Critical]|sda_Media_Wearout_Indicator=097;16;6 sda_Host_Writes_32MiB=517400 sda_Host_Reads_32MiB=395557
Local
A local configuration is useful when the smart values are to be monitored on the host itself (e.g. Icinga Server).

Requirements for a local installation are the steps described above, concerning the plugin, the Perl modules, smartctl and sudo. As a first step the command definition is created:

define command {
        command_name check_smart
        command_line /usr/lib/nagios/plugins/check_smart_attributes -d $ARG1$ -dbj /etc/nagios-plugins/config/check_smartdb.json
}
A service definition can then use this command:

define service{
    service_description           SMART attributes
    display_name                  SMART attributes
    use                           generic-service
    host_name                     localhost
    check_command                 check_smart!/dev/sda

}
Analyzing a Faulty Hard Disk using Smartctl
Main Page > Server Software > Linux > Linux-Storage > Smartmontools
Under Linux, you can read the SMART (Self-Monitoring, Analysis and Reporting Technology) information from the hard disk using smartctl. In this example, we will show how to analyze a defective hard disk. The hard disk in this example can no longer read several sectors and is therefore defective. It has to be replaced.


Contents
1	Displaying SMART Information
1.1	Analysis
2	SMART Tests
2.1	Short Test
2.2	Displaying the Test Results
2.3	Forcing Re-mapping a Defective Sector
3	References
Displaying SMART Information
The smartctl -a /dev/DEVICENAME command will display all SMART information for the affected hard disk. The hard disk in this example is showing increased errors for multiple SMART settings.

root@ubuntu-10-10:~# smartctl -a /dev/sdb
smartctl 5.40 2010-03-16 r3077 [x86_64-unknown-linux-gnu] (local build)
Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF INFORMATION SECTION ===
Model Family:     SAMSUNG SpinPoint F2 EG series
Device Model:     SAMSUNG HD502HI
Serial Number:    S1VZJ9CS712490
Firmware Version: 1AG01118
User Capacity:    500,107,862,016 bytes
Device is:        In smartctl database [for details use: -P show]
ATA Version is:   8
ATA Standard is:  ATA-8-ACS revision 3b
Local Time is:    Wed Feb  9 15:30:42 2011 CET
SMART support is: Available - device has SMART capability.
SMART support is: Enabled

=== START OF READ SMART DATA SECTION ===
SMART overall-health self-assessment test result: PASSED

General SMART Values:
Offline data collection status:  (0x00)    Offline data collection activity
                    was never started.
                    Auto Offline Data Collection: Disabled.
Self-test execution status:      (   0)    The previous self-test routine completed
                    without error or no self-test has ever 
                    been run.
Total time to complete Offline 
data collection:          (6312) seconds.
Offline data collection
capabilities:              (0x7b) SMART execute Offline immediate.
                    Auto Offline data collection on/off support.
                    Suspend Offline collection upon new
                    command.
                    Offline surface scan supported.
                    Self-test supported.
                    Conveyance Self-test supported.
                    Selective Self-test supported.
SMART capabilities:            (0x0003)    Saves SMART data before entering
                    power-saving mode.
                    Supports SMART auto save timer.
Error logging capability:        (0x01)    Error logging supported.
                    General Purpose Logging supported.
Short self-test routine 
recommended polling time:      (   2) minutes.
Extended self-test routine
recommended polling time:      ( 106) minutes.
Conveyance self-test routine
recommended polling time:      (  12) minutes.
SCT capabilities:            (0x003f)    SCT Status supported.
                    SCT Error Recovery Control supported.
                    SCT Feature Control supported.
                    SCT Data Table supported.

SMART Attributes Data Structure revision number: 16
Vendor Specific SMART Attributes with Thresholds:
ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
  1 Raw_Read_Error_Rate     0x000f   099   099   051    Pre-fail  Always       -       2376
  3 Spin_Up_Time            0x0007   091   091   011    Pre-fail  Always       -       3620
  4 Start_Stop_Count        0x0032   100   100   000    Old_age   Always       -       405
  5 Reallocated_Sector_Ct   0x0033   100   100   010    Pre-fail  Always       -       0
  7 Seek_Error_Rate         0x000f   253   253   051    Pre-fail  Always       -       0
  8 Seek_Time_Performance   0x0025   100   100   015    Pre-fail  Offline      -       0
  9 Power_On_Hours          0x0032   100   100   000    Old_age   Always       -       717
 10 Spin_Retry_Count        0x0033   100   100   051    Pre-fail  Always       -       0
 11 Calibration_Retry_Count 0x0012   100   100   000    Old_age   Always       -       0
 12 Power_Cycle_Count       0x0032   100   100   000    Old_age   Always       -       405
 13 Read_Soft_Error_Rate    0x000e   099   099   000    Old_age   Always       -       2375
183 Runtime_Bad_Block       0x0032   100   100   000    Old_age   Always       -       0
184 End-to-End_Error        0x0033   100   100   000    Pre-fail  Always       -       0
187 Reported_Uncorrect      0x0032   100   100   000    Old_age   Always       -       2375
188 Command_Timeout         0x0032   100   100   000    Old_age   Always       -       0
190 Airflow_Temperature_Cel 0x0022   084   074   000    Old_age   Always       -       16 (Lifetime Min/Max 16/16)
194 Temperature_Celsius     0x0022   084   071   000    Old_age   Always       -       16 (Lifetime Min/Max 16/16)
195 Hardware_ECC_Recovered  0x001a   100   100   000    Old_age   Always       -       3558
196 Reallocated_Event_Count 0x0032   100   100   000    Old_age   Always       -       0
197 Current_Pending_Sector  0x0012   098   098   000    Old_age   Always       -       81
198 Offline_Uncorrectable   0x0030   100   100   000    Old_age   Offline      -       0
199 UDMA_CRC_Error_Count    0x003e   100   100   000    Old_age   Always       -       1
200 Multi_Zone_Error_Rate   0x000a   100   100   000    Old_age   Always       -       0
201 Soft_Read_Error_Rate    0x000a   253   253   000    Old_age   Always       -       0

SMART Error Log Version: 1
No Errors Logged

SMART Self-test log structure revision number 1
No self-tests have been logged.  [To run self-tests, use: smartctl -t]


SMART Selective self-test log data structure revision number 1
 SPAN  MIN_LBA  MAX_LBA  CURRENT_TEST_STATUS
    1        0        0  Not_testing
    2        0        0  Not_testing
    3        0        0  Not_testing
    4        0        0  Not_testing
    5        0        0  Not_testing
Selective self-test flags (0x0):
  After scanning selected spans, do NOT read-scan remainder of disk.
If Selective self-test is pending on power-up, resume after 0 minute delay.

root@ubuntu-10-10:~#
Analysis
In this example, the following values are interesting for the detailed analysis.

  1 Raw_Read_Error_Rate     0x000f   099   099   051    Pre-fail  Always       -       2376
 13 Read_Soft_Error_Rate    0x000e   099   099   000    Old_age   Always       -       2375
187 Reported_Uncorrect      0x0032   100   100   000    Old_age   Always       -       2375
195 Hardware_ECC_Recovered  0x001a   100   100   000    Old_age   Always       -       3558
197 Current_Pending_Sector  0x0012   098   098   000    Old_age   Always       -       81
199 UDMA_CRC_Error_Count    0x003e   100   100   000    Old_age   Always       -       1
The RAW_VALUE of the Current_Pending_Sector value indicates how many of the hard disks sectors can no longer be read and are waiting for re-mapping.[1] You will find detailed information about the other error codes in the ATA S.M.A.R.T. Attributes section of the Wikipedia article about SMART.[2]

SMART Tests
SMART supports several hard disk tests. You can find the details on the man page for smartctl.

Short Test
We will start a short test in this example.

root@ubuntu-10-10:~# smartctl -t short /dev/sdb
smartctl 5.40 2010-03-16 r3077 [x86_64-unknown-linux-gnu] (local build)
Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF OFFLINE IMMEDIATE AND SELF-TEST SECTION ===
Sending command: "Execute SMART Short self-test routine immediately in off-line mode".
Drive command "Execute SMART Short self-test routine immediately in off-line mode" successful.
Testing has begun.
Please wait 2 minutes for test to complete.
Test will complete after Wed Feb  9 15:35:31 2011

Use smartctl -X to abort test.
root@ubuntu-10-10:~#
Displaying the Test Results
The test results will be displayed by the command: smartctl -l selftest /dev/sdb. The LBA address is obviously the first defective sector in this example.

root@ubuntu-10-10:~# smartctl -l selftest /dev/sdb
smartctl 5.40 2010-03-16 r3077 [x86_64-unknown-linux-gnu] (local build)
Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF READ SMART DATA SECTION ===
SMART Self-test log structure revision number 1
Num  Test_Description    Status                  Remaining  LifeTime(hours)  LBA_of_first_error
# 1  Short offline       Completed: read failure       20%       717         555027747

root@ubuntu-10-10:~#
Forcing Re-mapping a Defective Sector
When you write to a defective sector, the hard disk will attempt to re-map the affected sector. The original content of the sector will be lost by this procedure. You will find details about this on the Bad Block HOWTO page.[3]

The following command will display the remapping process for a sector. The Current_Pending_Sector counter will be reduced (these steps were performed according to the Bad Block HOWTO page).

root@ubuntu-10-10:~# fdisk -lu /dev/sdb

Disk /dev/sdb: 500.1 GB, 500107862016 bytes
255 heads, 63 sectors/track, 60801 cylinders, total 976773168 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0x20d1585d

   Device Boot      Start         End      Blocks   Id  System
/dev/sdb1   *        2048      206847      102400    7  HPFS/NTFS
Partition 1 does not end on cylinder boundary.
/dev/sdb2          206848    97863097    48828125    7  HPFS/NTFS
/dev/sdb3        97868041   976768064   439450012    5  Extended
/dev/sdb5        97868043   964703249   433417603+  83  Linux
/dev/sdb6       964703313   976768064     6032376   82  Linux swap / Solaris
root@ubuntu-10-10:~# tune2fs -l /dev/sdb5 | grep Block
Block count:              108354400
Block size:               4096
Blocks per group:         32768
root@ubuntu-10-10:~# debugfs 
debugfs 1.41.12 (17-May-2010)
debugfs:  open /dev/sdb5
debugfs:  testb 57144963
Block 57144963 not in use
debugfs:  quit
root@ubuntu-10-10:~# dd if=/dev/zero of=/dev/sdb5 bs=4096 count=1 seek=57144963
1+0 records in
1+0 records out
4096 bytes (4,1 kB) copied, 0,000379164 s, 10,8 MB/s
root@ubuntu-10-10:~# sync
root@ubuntu-10-10:~# smartctl -A /dev/sdb
smartctl 5.40 2010-03-16 r3077 [x86_64-unknown-linux-gnu] (local build)
Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF READ SMART DATA SECTION ===
SMART Attributes Data Structure revision number: 16
Vendor Specific SMART Attributes with Thresholds:
ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
[...]
197 Current_Pending_Sector  0x0012   098   098   000    Old_age   Always       -       80
[...]
Another set of tests will be started and another remapping procedure will be performed.

root@ubuntu-10-10:~# smartctl -t short /dev/sdb
smartctl 5.40 2010-03-16 r3077 [x86_64-unknown-linux-gnu] (local build)
Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF OFFLINE IMMEDIATE AND SELF-TEST SECTION ===
Sending command: "Execute SMART Short self-test routine immediately in off-line mode".
Drive command "Execute SMART Short self-test routine immediately in off-line mode" successful.
Testing has begun.
Please wait 2 minutes for test to complete.
Test will complete after Wed Feb  9 15:47:41 2011

Use smartctl -X to abort test.
root@ubuntu-10-10:~# smartctl -l selftest /dev/sdb
smartctl 5.40 2010-03-16 r3077 [x86_64-unknown-linux-gnu] (local build)
Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF READ SMART DATA SECTION ===
SMART Self-test log structure revision number 1
Num  Test_Description    Status                  Remaining  LifeTime(hours)  LBA_of_first_error
# 1  Short offline       Completed: read failure       20%       717         555027784
# 2  Short offline       Completed: read failure       20%       717         555027747

root@ubuntu-10-10:~# debugfs 
debugfs 1.41.12 (17-May-2010)
debugfs:  open /dev/sdb5
debugfs:  testb 57144967
Block 57144967 not in use
debugfs:  quit
root@ubuntu-10-10:~# dd if=/dev/zero of=/dev/sdb5 bs=4096 count=1 seek=57144967
1+0 records in
1+0 records out
4096 bytes (4,1 kB) copied, 0,000374713 s, 10,9 MB/s
root@ubuntu-10-10:~# smartctl -A /dev/sdb
smartctl 5.40 2010-03-16 r3077 [x86_64-unknown-linux-gnu] (local build)
Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

=== START OF READ SMART DATA SECTION ===
SMART Attributes Data Structure revision number: 16
Vendor Specific SMART Attributes with Thresholds:
ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
[...]
197 Current_Pending_Sector  0x0012   098   098   000    Old_age   Always       -       79
[...]
