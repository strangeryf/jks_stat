    # -*- coding: utf-8 -*-
    # depends on: python-jenkins matploblib numpy
    # pip install python-jenkins matploblib numpy
    import sys
    import jenkins
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    import os

    class groupMetrics():
      # abd - average build duration
      # tbn - total build number
      # sbr - succesful build rate
      # mttr - mean time to recovery
      def __init__(self, group_name):
        self.group_name = group_name
        self.abd = self.tbn = self.sbr = self.mttr = 0
        
      def __str__(self):
        return ('group %s --- abd: %d, tbn: %d, sbr: %.1f%%, mttr: %d' % (self.group_name, self.abd, self.tbn, self.sbr, self.mttr))

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
      def job_stat(self, job_name):
        build_count, duration, success = 0, 0, 0
        for build in self.server.get_job_info(job_name).get('builds', ''):
          build_count+=1
          build_num=build.get('number')
          duration += self.server.get_build_info(job_name, build_num).get('duration', 0)
          if 'SUCCESS' == self.server.get_build_info(job_name, build_num).get('result'):
            success += 1
        return build_count, duration, success
        #print('%s: ' % job_name)
        #print('Average build duration: %.1fs' % (duration/1000./build_count))
        #print('succesful build: %.1f%%' % (success*100./build_count))

      def job_MTTR(self, job_name):
        """
        calculate Mean Time To Recovery of a job
        """
        failedBuildTS = 0
        totalFailedTime = 0
        buildCount = 0
        build_nums = []
        
        # get sorted build number(first to last), which is from last to first by default
        for build in self.server.get_job_info(job_name).get('builds', ''):
          build_nums.append(build.get('number'))
        build_nums.sort()
        
        # count failure time and recover times(buildCount)
        for build_num in build_nums:
          result = self.server.get_build_info(job_name, build_num).get('result');
          if result==None: continue;
          if result!='SUCCESS':
            if failedBuildTS != 0: continue
            failedBuildTS = self.server.get_build_info(job_name, build_num).get('timestamp')
            continue
          if failedBuildTS==0: continue
          failedLastTS = self.server.get_build_info(job_name, build_num).get('timestamp') - failedBuildTS
          totalFailedTime += failedLastTS
          buildCount += 1
          failedBuildTS = 0
        
        mttr = 0
        if buildCount!=0:
          mttr = totalFailedTime/1000./60/buildCount
        #print('debug: ' + job_name + ': ' + str(mttr))
        return mttr
      
      #group statistics
      def group_stat(self, group_name):
        print("counting group " + group_name + "...")
        jobs = self.server.get_jobs()
        group=[]
        gm = groupMetrics(group_name)
        for job in jobs:
          job_name = job.get('name','')
          if job_name.startswith(group_name):
            group.append(job_name)
        grp_build_count, grp_duration, grp_success, grp_mttr = 0, 0, 0, 0
        for job in group:
          print '.',
          build_count, duration, success = self.job_stat(job)
          grp_build_count += build_count
          grp_duration += duration
          grp_success += success
          grp_mttr += self.job_MTTR(job)
        print
        
        if grp_build_count!=0:
          gm.abd = grp_duration/1000./grp_build_count
          gm.sbr = grp_success*100./grp_build_count
        gm.tbn = int(grp_build_count)
        if len(group)!=0:
          gm.mttr=int(grp_mttr/len(group))

        return gm

    def autolabel(rects, ax):
        """
        Attach a text label above each bar displaying its height
        """
        for rect in rects:
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width()/2., height, '%d' % int(height),
                    ha='center', va='bottom')

    if __name__=='__main__':
      jks_stat=JenkinsStat('http://192.168.1.1:8080', 'admin', '1eb1a49aebf097541e3103e4f06c0dce')
      groups = "GRP00", "GRP01", "GRP02"
      abd=[] # average build duration
      tbn=[] # total build number
      sbr=[] # succesful build rate
      mttr=[] # mean time to recovery
      for group in groups:
        gm=jks_stat.group_stat(group)
        print(gm)
        abd.append(gm.abd)
        tbn.append(gm.tbn)
        sbr.append(gm.sbr)
        mttr.append(gm.mttr)

      N = len(groups)
      ind = np.arange(N)  # the x locations for the groups
      width = 0.5       # the width of the bars
      
      fig, axes = plt.subplots(2, 2)
      rects1 = axes[0,0].bar(ind, abd, width, color='r')
      axes[0,0].set_ylabel('Time(s)')
      axes[0,0].set_title('Average Build Duration')
      axes[0,0].set_xticks(ind + width / 2)
      axes[0,0].set_xticklabels(groups)
      
      rects2 = axes[0,1].bar(ind, tbn, width, color='g')
      axes[0,1].set_ylabel('Number')
      axes[0,1].set_title('Total Build Number')
      axes[0,1].set_xticks(ind + width / 2)
      axes[0,1].set_xticklabels(groups)
      
      rects3 = axes[1,0].bar(ind, sbr, width, color='b')
      axes[1,0].set_ylabel('Percentage(%)')
      axes[1,0].set_title('Successful Build')
      axes[1,0].set_xticks(ind + width / 2)
      axes[1,0].set_xticklabels(groups)
      
      rects4 = axes[1,1].bar(ind, mttr, width, color='y')
      axes[1,1].set_ylabel('Time(m)')
      axes[1,1].set_title('Mean Time to Recovery')
      axes[1,1].set_xticks(ind + width / 2)
      axes[1,1].set_xticklabels(groups)
      
      autolabel(rects1, axes[0,0])
      autolabel(rects2, axes[0,1])
      autolabel(rects3, axes[1,0])
      autolabel(rects4, axes[1,1])
      
      fig = matplotlib.pyplot.gcf()
      fig.set_size_inches(16, 9)
      plt.savefig("jenkins_metrics.png")
      os.system("start jenkins_metrics.png")
