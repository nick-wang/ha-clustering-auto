import os
import psutil

def memory_usage_psutil():
	process = psutil.Process(os.getpid())
	return process.memory_percent()

def cpu_usage_psutil():
	process = psutil.Process(os.getpid())
	return process.cpu_percent()

def get_fs_freespace(pathname):
	statvfs = os.statvfs(pathname)
	return 1.0*statvfs.f_bavail/statvfs.f_blocks
