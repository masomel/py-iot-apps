#! /bin/sh

mkdir -p /home/pi/pb/Pictures/ 
mkdir -p /home/pi/pb/Pictures/ex
cd /home/pi/pb/
mv /var/www/pics/_img* /var/www/pics_ex/
mv ./Pictures/img* ./Pictures/ex/
cp Instructable.png ./Pictures/Instructable.png
sudo python photobooth_control.py & 
exit


