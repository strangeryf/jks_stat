# -*- coding: utf-8 -*-
# depends on: python-jenkins
# pip install python-jenkins
import sys
import jenkins

#Jenkins statistics
class JenkinsStat():
  def __init__(self, url, usr, token):
    try:
      self.server = jenkins.Jenkins(url, username=usr, password=token)
      version = self.server.get_version()
      print('Jenkins ver: %s' % version)
    except Exception as e:
      print(e)
      sys.exit(-1)

  #job statistics
  def job_stat(self, jobname):
    build_count, duration, success = 0, 0, 0
    for build in self.server.get_job_info(jobname).get('builds', ''):
      build_count+=1
      build_num=build.get('number')
      duration += self.server.get_build_info(jobname, build_num).get('duration', 0)
      if 'SUCCESS' == self.server.get_build_info(jobname, build_num).get('result'):
        success += 1
    return build_count, duration, success
    #print('%s: ' % jobname)
    #print('Average build duration: %.1fs' % (duration/1000./build_count))
    #print('succesful build: %.1f%%' % (success*100./build_count))

  # job MTTR
  def job_MTTR(self, jobname):
    failedBuildTS = 0
    totalFailedTime = 0
    buildCount = 0
    build_nums = []
    for build in self.server.get_job_info(jobname).get('builds', ''):
      build_nums.append(build.get('number'))
    build_nums.sort()
    for build_num in build_nums:
      result = self.server.get_build_info(jobname, build_num).get('result');
      if result==None: continue;
      if result!='SUCCESS':
        if failedBuildTS != 0: continue
        failedBuildTS = self.server.get_build_info(jobname, build_num).get('timestamp')
        continue
      if failedBuildTS==0: continue
      failedLastTS = self.server.get_build_info(jobname, build_num).get('timestamp') - failedBuildTS
      totalFailedTime += failedLastTS
      buildCount += 1
      failedBuildTS = 0
    
    mttr = 0
    if buildCount!=0:
      mttr = totalFailedTime/1000./60/buildCount
    #print('debug: ' + jobname + ': ' + str(mttr))
    return mttr
  
  #group statistics
  def group_stat(self, groupname):
    print("counting group " + groupname + "...")
    jobs = self.server.get_jobs()
    group=[]
    for job in jobs:
      jobname = job.get('name','')
      if jobname.startswith(groupname):
        group.append(jobname)
    grp_build_count, grp_duration, grp_success, grp_mttr = 0, 0, 0, 0
    for job in group:
      print '.',
      build_count, duration, success = self.job_stat(job)
      grp_build_count += build_count
      grp_duration += duration
      grp_success += success
      grp_mttr += self.job_MTTR(job)
    print
    print('Average build duration: %.1fs' % (duration/1000./build_count))
    print('succesful build: %.1f%%' % (success*100./build_count))
    print('total build number: %d' % grp_build_count)
    print('MTTR: %d' % (grp_mttr/len(group)))
  
if __name__=='__main__':
  jksstat=JenkinsStat('http://192.168.10.212:30080', 'admin', '1eb1a49aebf097541e3103e4f06c0dce')
  groups = "GRP00", "GRP01", "GRP02", "GRP03"
  for group in groups:
    jksstat.group_stat(group)
