#!/usr/bin/python

import os
import csv
import sys, getopt
import pydevd
import string
import matplotlib.pyplot as plt
import pydevd
import cmath

def analyze_single_file_throughput(dirpath, filename):
    '''
    Analyze single file throughput.
    :param file_path:
    :return: {'testType':'mptcp', 'subflowNum': 1, 'averageBw':10000000, "stdevList": [{"time":1, "stdev":0.918}]}
    '''
    #file_path = ' ';
    # 1. get ips-->bw
    # 2. leverage bw
    file_path = os.path.join(dirpath, file_name)
    result = {"sumBwDict":{}}
    bw_map = {}
    stdevDict = {}
    bw_ration_map = None
    bw_average = 0.0
    bw_optimal = 10000000.0
    bw__average_ratio = 0.0
    num_sublflow = 2
    standard_deviation = 0.0
    csv_reader = csv.reader(open(file_path))
    count = 0;
    absolute_start_time = 0
    for row in csv_reader:
        time = int(row[0])
        src_ip = row[1]
        dst_ip = row[3]
        time_interval = row[6].split('-')
        start_time = float(time_interval[0])
        end_time = float(time_interval[1])
        count += 1
        # throughput
        bw = float(row[8])
        if absolute_start_time == 0:
            absolute_start_time = time
        relative_time = time - absolute_start_time
        if (end_time - start_time) == 1:
            if relative_time not in stdevDict:
                stdevDict[relative_time] = []
            stdevDict[relative_time].append({"ips": (src_ip, dst_ip), "bw": bw})
        if start_time == 0 and end_time <= 2:
            continue
        if start_time > 0:
            continue
        bw_map[(src_ip, dst_ip)] = bw

    print("Data lines:%d" % count)
    bw_sum = 0.0
    con_num = 0.0;
    for bw in bw_map.values():
        bw_sum += bw
        con_num += 1
    # bw_average = bw_sum / con_num
    bw_average = bw_sum / con_num
    bw__average_ratio = bw_average / bw_optimal
    print('Average bw:%d, Optimal bw:%d,  Average bw ratio: %f' % (bw_average, bw_optimal, bw__average_ratio))

    # handle stdev
    max_bw_sum = 0.0
    for time in stdevDict.keys():
        dataList = stdevDict[time]
        stdev = 1.0
        bw_sum = 0.0
        bw_ave = 0.0
        count = 0
        for data in dataList:
            bw_sum += data["bw"]
            count += 1
        # bw_ave = bw_sum/count
        # tmp = 0.0
        # for data in dataList:
        #     tmp +=(data["bw"] - bw_ave)**2
        # stdev = cmath.sqrt(tmp/count)
        if bw_sum > max_bw_sum:
            max_bw_sum = bw_sum
    stdev_sum = 0.0
    for bw in bw_map.values():
        stdev_sum = (bw / 1000 - bw_average / 1000) ** 2
    # stdev = float(cmath.sqrt(stdev_sum/con_num))
    stdev = (stdev_sum / con_num) ** 0.5
    result['maxThroughput']= max_bw_sum
    result['averageBw'] = bw_average
    result['averageBwRatio'] = bw__average_ratio
    result['stdev'] = stdev
    print result
    return result
    pass

if __name__ == '__main__':
    # debug:
    # pydevd.settrace('10.103.90.184', port=5151, stdoutToServer=True, stderrToServer=True)
    # 1. read data dir
    top_dir = raw_input("Enter data dir path:")
    bw_result_file_path = os.path.join(top_dir, 'average_ratio_result.csv')
    stdev_result_file_path = os.path.join(top_dir,'stdev_result.csv')
    if not os.path.exists(bw_result_file_path):
        os.mknod(bw_result_file_path)
    if not os.path.exists(stdev_result_file_path):
        os.mknod(stdev_result_file_path)
    # 2. ls files and seperate file by test type
    files = os.listdir(top_dir)
    mptcp_src_files = []
    ecmp_src_files = []
    for file in files:
        if string.find(file, 'mptcp') != -1:
            mptcp_src_files.append(file)
        elif string.find(file, 'ecmp') != -1:
            ecmp_src_files.append(file)
        else:
            continue
    # 3. call analyze_single_file_throughput() handle all files
    #   mptcp_list[{}], ecmp_list[{}], order thhese list
    mptcp_result_list = []
    mptcp_result_dict = {}
    ecmp_result_list = []
    ecmp_result_dict = {}
    for file_name in mptcp_src_files:
        args = string.split(file_name, '_')
        subflow_num = int(args[0])
        result_data = analyze_single_file_throughput(top_dir, file_name)
        test_index = string.split(file_name, "_")[4]
        result_data['testType'] = 'mptcp'
        result_data['subflowNum'] = subflow_num
        if not mptcp_result_dict.has_key(subflow_num):
            mptcp_result_dict[subflow_num] = {'maxAverageBwRatio':0.0,'maxAverageBw':0.0, 'averageBwRatio':0.0, 'testType':'mptcp', 'subflowNum':subflow_num, 'maxThroughput':0,
                                              'averageBwSum':0.0,'averageBwRatioSum':0.0, 'maxThroughputSum':0, 'count':0, 'stdevSum':0.0}
        if mptcp_result_dict[subflow_num]['maxAverageBwRatio'] > result_data['averageBwRatio']:
            mptcp_result_dict[subflow_num]['maxAverageBwRatio'] = result_data['averageBwRatio']
            mptcp_result_dict[subflow_num]['maxAverageBw'] = result_data['averageBw']

        if mptcp_result_dict[subflow_num]['maxThroughput'] > result_data['maxThroughput']:
            mptcp_result_dict[subflow_num]['maxThroughput'] = result_data['maxThroughput']

        mptcp_result_dict[subflow_num]['averageBwSum'] = mptcp_result_dict[subflow_num]['averageBwSum'] + result_data[
            'averageBw']
        if result_data['averageBwRatio'] < 0.5:
            exit(1)
        mptcp_result_dict[subflow_num]['averageBwRatioSum'] = mptcp_result_dict[subflow_num]['averageBwRatioSum'] + result_data[
            'averageBwRatio']
        mptcp_result_dict[subflow_num]['count'] = mptcp_result_dict[subflow_num]['count'] + 1
        mptcp_result_dict[subflow_num]['maxThroughputSum'] = mptcp_result_dict[subflow_num]['maxThroughputSum'] + result_data[
            'maxThroughput']
        mptcp_result_dict[subflow_num]['stdevSum'] = mptcp_result_dict[subflow_num]['stdevSum'] +  result_data['stdev']

    for result_data in mptcp_result_dict.values():
        result_data['finalAverageBw'] = result_data['averageBwSum'] / result_data['count']
        result_data['finalAverageBwRatio'] = result_data['averageBwRatioSum'] / result_data['count']
        result_data['finalAverageMaxThroughput'] = result_data['maxThroughputSum'] / result_data['count']
        result_data['finalMaxThroughput'] = result_data['maxThroughput']
        result_data['finalAverageStdev'] = result_data['stdevSum'] / result_data['count']
        mptcp_result_list.append(result_data)

    for file_name in ecmp_src_files:
        args = string.split(file_name, '_')
        subflow_num = int(args[0])
        result_data = analyze_single_file_throughput(top_dir, file_name)
        result_data['testType'] = 'ecmp'
        result_data['subflowNum'] = subflow_num
        if not ecmp_result_dict.has_key(subflow_num):
            ecmp_result_dict[subflow_num] = {'maxAverageBwRatio':0.0,'maxAverageBw':0.0, 'averageBwRatio':0.0, 'testType':'mptcp', 'subflowNum':subflow_num, 'maxThroughput':0,
                                              'averageBwSum':0.0,'averageBwRatioSum':0.0, 'maxThroughputSum':0, 'count':0, 'stdevSum':0.0}
        if ecmp_result_dict[subflow_num]['maxAverageBwRatio'] > result_data['averageBwRatio']:
            ecmp_result_dict[subflow_num]['maxAverageBwRatio'] = result_data['averageBwRatio']
            ecmp_result_dict[subflow_num]['maxAverageBw'] = result_data['averageBw']

        if ecmp_result_dict[subflow_num]['maxThroughput'] > result_data['maxThroughput']:
            ecmp_result_dict[subflow_num]['maxThroughput'] = result_data['maxThroughput']

        ecmp_result_dict[subflow_num]['averageBwSum'] = ecmp_result_dict[subflow_num]['averageBwSum'] + result_data[
            'averageBw']
        if result_data['averageBwRatio'] < 0.5:
            exit(1)
        ecmp_result_dict[subflow_num]['averageBwRatioSum'] = ecmp_result_dict[subflow_num]['averageBwRatioSum'] + result_data[
            'averageBwRatio']
        ecmp_result_dict[subflow_num]['count'] = ecmp_result_dict[subflow_num]['count'] + 1
        ecmp_result_dict[subflow_num]['maxThroughputSum'] = ecmp_result_dict[subflow_num]['maxThroughputSum'] + result_data[
            'maxThroughput']
        ecmp_result_dict[subflow_num]['stdevSum'] = ecmp_result_dict[subflow_num]['stdevSum'] +  result_data['stdev']


    for result_data in ecmp_result_dict.values():
        result_data['finalAverageBw'] = result_data['averageBwSum'] / result_data['count']
        result_data['finalAverageBwRatio'] = result_data['averageBwRatioSum'] / result_data['count']
        result_data['finalAverageMaxThroughput'] = result_data['maxThroughputSum'] / result_data['count']
        result_data['finalMaxThroughput'] = result_data['maxThroughput']
        result_data['finalAverageStdev'] = result_data['stdevSum'] / result_data['count']
        ecmp_result_list.append(result_data)


    mptcp_result_list.sort(key = lambda k : (k.get('subflowNum')))
    ecmp_result_list.sort(key = lambda k : (k.get('subflowNum')))
    # 4. Output analyzed Data and plot
    mptcp_show_subflownum = []
    mptcp_show_ave_bwratio = []
    mptcp_show_ave_maxthroughput = []
    mptcp_show_maxthroughput = []
    mptcp_show_ave_stdev = []

    ecmp_show_subflownum = []
    ecmp_show_ave_bwratio = []
    ecmp_show_ave_maxthroughput = []
    ecmp_show_maxthroughput = []
    ecmp_show_ave_stdev = []
    for data in mptcp_result_list:
        mptcp_show_subflownum.append(data['subflowNum'])
        mptcp_show_ave_bwratio.append(data['finalAverageBwRatio'])
        mptcp_show_ave_maxthroughput.append(data['finalAverageMaxThroughput'])
        mptcp_show_maxthroughput.append(data['finalMaxThroughput'])
        mptcp_show_ave_stdev.append(data['finalAverageStdev'])
    for data in ecmp_result_list:
        ecmp_show_subflownum.append(data['subflowNum'])
        ecmp_show_ave_bwratio.append(data['finalAverageBwRatio'])
        ecmp_show_ave_maxthroughput.append(data['finalAverageMaxThroughput'])
        ecmp_show_maxthroughput.append(data['finalMaxThroughput'])
        ecmp_show_ave_stdev.append(data['finalAverageStdev'])

    bw_writer = csv.writer(open(bw_result_file_path,'w'))
    bw_writer.writerow(mptcp_show_subflownum)
    bw_writer.writerow(mptcp_show_ave_bwratio)
    bw_writer.writerow(ecmp_show_ave_bwratio)

    stdev_writer = csv.writer(open(stdev_result_file_path, 'w'))
    stdev_writer.writerow(mptcp_show_subflownum)
    stdev_writer.writerow(mptcp_show_ave_stdev)
    stdev_writer.writerow(ecmp_show_ave_stdev)


    plt.subplot(221)
    plt.plot(mptcp_show_subflownum,mptcp_show_ave_bwratio, 'r-', ecmp_show_subflownum, ecmp_show_ave_bwratio, 'b-')
    plt.subplot(222)
    plt.plot(mptcp_show_subflownum, mptcp_show_ave_maxthroughput, 'r-', ecmp_show_subflownum, ecmp_show_ave_maxthroughput, 'b-')
    plt.subplot(223)
    plt.plot(mptcp_show_subflownum, mptcp_show_maxthroughput, 'r-', ecmp_show_subflownum, ecmp_show_maxthroughput, 'b-')
    plt.subplot(224)
    plt.plot(mptcp_show_subflownum, mptcp_show_ave_stdev, 'r-', ecmp_show_subflownum, ecmp_show_ave_stdev, 'b-')

    plt.show()
    plt
    pass