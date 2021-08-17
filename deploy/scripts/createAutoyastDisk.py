#!/usr/bin/python
import os
import sys
import tempfile
import shutil

PREFIX = "SUSE-HA-"
POSTFIX = "-autoyast"
AUTOYAST_FILENAME = "autoyast.xml"

class AutoyastDisk(object):
    '''
    Create a formatted qemu disk and allow put files in.

    Usage:
      import createAutoyastDisk

      i = createAutoyastDisk.AutoyastDisk("Name")
      i.save_autoyast_to_image("/tmp/xxx-autoyast.xml")
      # i.remove_img()

    '''
    def __init__(self, name="dummynode", path="/tmp",
            size="10M", fmt="raw"):
        '''
        Init function.
        Input:
          name: name to create the qemu image
          path: folder to put qemu image
          size: size of qemu image
          fmt:  format of qemu image
        '''
        self.name = PREFIX + name + POSTFIX + "." + fmt
        self.path = path
        self.fmt = fmt
        self.size = size
        self.img = ""

        tempimg = self.path + "/" + self.name
        if os.path.exists(tempimg):
            print("Remove existed file %s first!" %
                    self.img)
            os.system('rm -rf %s' % tempimg)

        if self._create() == 0:
            self.img = tempimg

            if self._format() == 0:
                print("Successfully create and format qemu image: %s" %
                        self.img)
                return

        # Failed to create or format
        if os.path.exists(self.path + self.name):
            os.system('rm -rf %s' % tempimg)


    def _create(self):
        '''
        create qemu image.
        '''
        if not os.path.isdir(self.path):
            os.mkdir(self.path)

        cmd = "qemu-img create -f %s %s %s" % (self.fmt,
                self.path + "/" + self.name, self.size)
        return os.system(cmd)


    def _format(self):
        '''
        Format the qemu image.
        '''
        if self.img != "" and os.path.exists(self.img):
            cmd = "mkfs.ext4 %s >/dev/null 2>&1" % (self.img)
            return os.system(cmd)

        return -1

    def _mount_img(self, path):
        '''
        Mount qemu image to a random place.
        '''
        cmd = "mount %s %s" % (self.img, path)
        return os.system(cmd)


    def _umount_img(self, path):
        '''
        Unmount qemu image.
        '''
        cmd = "umount %s" % (path)
        return os.system(cmd)


    def _cp_autoyast_file(self, path, autoyast):
        '''
        Copy autoyast file to mounted qemu disk.
        '''
        print("Copy %s to %s" %(autoyast, path + "/" + AUTOYAST_FILENAME))
        shutil.copyfile(autoyast, path + "/" + AUTOYAST_FILENAME)


    def save_autoyast_to_image(self, autoyast):
        '''
        Save autoyast file to image.
        '''
        if not os.path.exists(autoyast):
            print("ERROR! autoyast file %s not existed!" % autoyast)
            return False

        # tempfile.TemporaryDirectory() only available after python3.2
        #with tempfile.TemporaryDirectory() as tmpdname:
        tmpdname = tempfile.mkdtemp()
        print("Create temp dir %s to mount qemu img." % tmpdname)
        self._mount_img(tmpdname)
        self._cp_autoyast_file(tmpdname, autoyast)
        self._umount_img(tmpdname)

        os.system('rm -rf %s' % tmpdname)

    def get_img(self):
        '''
        Return the image.
        '''
        return self.img


    def remove_img(self):
        '''
        Remove the qemu image.
        '''
        if self.img == "":
            return True

        os.system('rm -rf %s' % self.img)

        ret = os.path.exists(self.img)
        if not ret:
            print("Successfully remove qemu image: %s" %
                    self.img)
            self.img = ""
            return True

        return False


if __name__ == "__main__":
    a = AutoyastDisk("NickWang")
    a.save_autoyast_to_image("/tmp/test-autoyast.xml")
    a.remove_img()

